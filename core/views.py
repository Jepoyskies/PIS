from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count

from .models import Student, DisciplinaryRecord, SchoolYear, Section, Enrollment, StaffProfile, DailyAttendance, PeriodAttendance, StudentPeriodRecord
from .forms import StudentForm, DisciplinaryRecordForm, StaffAccountForm, SectionForm, StudentMaintenanceForm
import json

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_maintenance_stats():
    """Returns the stats for the maintenance sidebar."""
    return {
        'staff_count': User.objects.filter(is_staff=True, is_superuser=False).count(),
        'student_count': Student.objects.filter(is_deleted=False).count(),
        'section_count': Section.objects.count(),
    }

def get_staff_context(request):
    """Returns the active school year context for the main system."""
    all_school_years = SchoolYear.objects.all().order_by('-code')
    active_sy_id = request.session.get('active_sy_id')
    active_sy = None
    if active_sy_id:
        active_sy = SchoolYear.objects.filter(id=active_sy_id).first()
    if not active_sy:
        active_sy = SchoolYear.objects.filter(is_active=True).first()
        
    pending_batches = PeriodAttendance.objects.filter(is_locked=True, is_approved=False).select_related('daily_attendance__section', 'submitted_by')
        
    context = {
        'all_school_years': all_school_years, 
        'active_sy': active_sy, 
        'pending_batches': pending_batches,
        'is_admin': request.user.is_superuser
    }
    context.update(get_maintenance_stats())
    return context

# ==========================================
# AUTH & ROUTING (RESTRICTED LOGIN)
# ==========================================

def login_view(request):
    if request.user.is_authenticated: 
        return redirect('home')
        
    selected_role = None 
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        selected_role = request.POST.get('selected_role') # Will be 'staff' or 'student'

        user = authenticate(request, username=u, password=p)
        
        if user:
            # --- RBAC CHECK ---
            
            # If they are at the Faculty portal but are NOT staff/admin
            if selected_role == 'staff' and not (user.is_staff or user.is_superuser):
                messages.error(request, "Access Denied: This portal is for Faculty & Staff only.")
                # We return render here and pass selected_role back to keep form open
                return render(request, 'core/login.html', {'selected_role': selected_role})

            # If they are at the Student portal but have no student profile
            if selected_role == 'student' and not hasattr(user, 'student_profile'):
                messages.error(request, "Access Denied: Staff must use the Faculty & Staff portal.")
                return render(request, 'core/login.html', {'selected_role': selected_role})

            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Username or Password')
            
    # Always pass selected_role back (it will be None on first load)
    return render(request, 'core/login.html', {'selected_role': selected_role})

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')

@login_required(login_url='login')
def traffic_cop(request):
    """ Routes users based on their role (RBAC) """
    user = request.user
    if user.is_superuser or user.is_staff: 
        return redirect('staff_home')
        
    if hasattr(user, 'student_profile'):
        return redirect('student_dashboard')
        
    logout(request)
    return redirect('login')

@login_required
def set_school_year(request):
    if request.method == 'POST':
        sy_id = request.POST.get('school_year_id')
        request.session['active_sy_id'] = sy_id
    return redirect(request.META.get('HTTP_REFERER', 'staff_home'))

# ==========================================
# MAINTENANCE MODULE
# ==========================================

@login_required
def maintenance_dashboard(request):
    if not request.user.is_staff: return redirect('home')
    context = get_maintenance_stats()
    context['is_admin'] = request.user.is_superuser
    return render(request, 'core/maintenance_dashboard.html', context)

@login_required
def manage_staff(request):
    if not request.user.is_superuser: return redirect('home')
    staff_list = User.objects.filter(is_staff=True, is_superuser=False)
    
    if request.method == 'POST':
        form = StaffAccountForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    StaffProfile.objects.create(
                        user=user, 
                        employee_id=form.cleaned_data.get('employee_id'),
                        department="Prefect Office"
                    )
                messages.success(request, f"Staff account {user.username} created.")
                return redirect('manage_staff')
            except Exception as e:
                messages.error(request, f"Error: {e}")
    else:
        form = StaffAccountForm()

    context = get_maintenance_stats()
    context.update({'form': form, 'staff_list': staff_list, 'is_admin': request.user.is_superuser})
    return render(request, 'core/manage_staff_ui.html', context)

@login_required
def manage_sections(request):
    if not request.user.is_staff: return redirect('home')
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Section created successfully!")
            return redirect('manage_sections')
    
    sections = Section.objects.all().order_by('grade_level')
    context = get_staff_context(request) 
    context.update({'sections': sections})
    return render(request, 'core/manage_sections.html', context)

@login_required
def manage_students(request):
    if not request.user.is_staff: return redirect('home')
    
    if request.method == 'POST':
        if 'toggle_beadle' in request.POST:
            student = get_object_or_404(Student, student_number=request.POST.get('student_number'))
            student.is_beadle = not student.is_beadle
            student.save()
            if student.is_beadle and student.section:
                Section.objects.filter(id=student.section.id).update(beadle=student)
            elif not student.is_beadle:
                Section.objects.filter(beadle=student).update(beadle=None)
            messages.success(request, "Beadle Role Updated!")
            return redirect('manage_students')
            
        elif 'edit_student' in request.POST:
            student = get_object_or_404(Student, student_number=request.POST.get('student_number'))
            student.last_name = request.POST.get('last_name').upper()
            student.first_name = request.POST.get('first_name').upper()
            student.middle_initial = request.POST.get('middle_initial', '').upper()
            student.sex = request.POST.get('sex')
            student.date_of_birth = request.POST.get('date_of_birth') or None
            student.address = request.POST.get('address')
            student.section_id = request.POST.get('section_id') or None
            student.save()
            messages.success(request, "Student details updated!")
            return redirect('manage_students')
        else:
            form = StudentMaintenanceForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    new_student = form.save()
                    active_sy_id = request.session.get('active_sy_id')
                    active_sy = SchoolYear.objects.filter(id=active_sy_id).first() or SchoolYear.objects.filter(is_active=True).first()
                    if active_sy:
                        Enrollment.objects.create(student=new_student, school_year=active_sy)
                messages.success(request, "Student created successfully!")
                return redirect('manage_students')
    
    students = Student.objects.filter(is_deleted=False).order_by('-created_at')
    sections = Section.objects.all() 
    context = get_maintenance_stats()
    context.update({'students': students, 'sections': sections, 'is_admin': request.user.is_superuser})
    return render(request, 'core/manage_students.html', context)

# ==========================================
# STAFF MODULES
# ==========================================

@login_required
def staff_home(request):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    return render(request, 'core/pis_home.html', context)

@login_required
def staff_dashboard(request):
    if not request.user.is_staff: return redirect('home')
    if request.method == 'POST':
        # logic for add/edit/beadle... (already in your original code)
        pass

    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    search_name = request.GET.get('searchName', '')
    search_id = request.GET.get('searchId', '')
    students = Student.objects.filter(enrollments__school_year=active_sy, is_deleted=False)
    
    if search_name:
        students = students.filter(last_name__icontains=search_name) | students.filter(first_name__icontains=search_name)
    if search_id:
        students = students.filter(student_number__icontains=search_id)
        
    context.update({
        'students': students.distinct(), 
        'search_name': search_name, 
        'search_id': search_id,
        'sections': Section.objects.all().order_by('grade_level')
    })
    return render(request, 'core/dashboard.html', context)

@login_required
def disciplinary_module(request, category):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    student = Student.objects.filter(student_number=search_id).first() if search_id else None
    
    if student:
        records = DisciplinaryRecord.objects.filter(student=student, category=category, school_year=active_sy).order_by('-date_of_incident')
    else:
        records = DisciplinaryRecord.objects.filter(category=category, school_year=active_sy).order_by('-date_of_incident')[:50] 
    
    context.update({'module_name': category, 'student': student, 'records': records, 'search_id': search_id})
    return render(request, 'core/conduct.html', context)

@login_required
def staff_attendance_list(request):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    batches = PeriodAttendance.objects.filter(is_locked=True).select_related('daily_attendance__section', 'submitted_by')
    context['attendance_batches'] = batches.order_by('-daily_attendance__date')
    return render(request, 'core/staff_attendance_list.html', context)

@login_required
def staff_attendance_review(request, batch_id):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    batch = get_object_or_404(PeriodAttendance.objects.prefetch_related('records__student'), id=batch_id)
    context['batch'] = batch
    return render(request, 'core/staff_attendance_review.html', context)

@login_required
def approve_attendance_batch(request, batch_id):
    if not request.user.is_staff: return redirect('home')
    batch = get_object_or_404(PeriodAttendance, id=batch_id)
    if request.method == 'POST':
        with transaction.atomic():
            for rec in batch.records.all():
                # Logic to log offenses...
                pass
            batch.is_approved = True
            batch.save()
            messages.success(request, "Attendance approved!")
    return redirect('staff_attendance_review', batch_id=batch.id)

@login_required
def api_student_offenses(request, student_id):
    student = get_object_or_404(Student, student_number=student_id)
    # Json logic...
    return JsonResponse({'status': 'success'})

@login_required
def reports_dashboard(request):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    return render(request, 'core/reports_dashboard.html', context)

# ==========================================
# PORTALS
# ==========================================

@login_required
def student_dashboard(request): 
    if not hasattr(request.user, 'student_profile'): return redirect('login')
    student = request.user.student_profile
    disc = DisciplinaryRecord.objects.filter(student=student).order_by('-date_of_incident')
    att_history = StudentPeriodRecord.objects.filter(student=student).order_by('-period__daily_attendance__date')[:20]
    return render(request, 'core/student_dashboard.html', {
        'student': student, 'discipline_history': disc, 'attendance_history': att_history
    })

@login_required
def beadle_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    if not student.is_beadle or not student.section: return redirect('student_dashboard')
    # Beadle Logic...
    return render(request, 'core/beadle_dashboard.html', {'student': student})