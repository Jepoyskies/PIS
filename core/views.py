from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from datetime import date

from .models import Student, DisciplinaryRecord, SchoolYear, Section, Enrollment, StaffProfile, AttendanceBatch, AttendanceRecord
from .forms import StudentForm, DisciplinaryRecordForm, StaffAccountForm, SectionForm, StudentMaintenanceForm

# ==========================================
# HELPER FUNCTIONS (Must be at the top)
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
        
    # INJECTED: Fetch Pending Attendances for the Notification Panel
    pending_batches = AttendanceBatch.objects.filter(is_confirmed=False).order_by('-date')
        
    return {'all_school_years': all_school_years, 'active_sy': active_sy, 'pending_batches': pending_batches}

# ==========================================
# AUTH & ROUTING
# ==========================================

def login_view(request):
    if request.user.is_authenticated: return redirect('home')
    if request.method == 'POST':
        u, p = request.POST.get('username'), request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid Username or Password')
    return render(request, 'core/login.html')

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
        student = user.student_profile
        if student.is_beadle or student.beadle_of.exists():
            return redirect('beadle_dashboard')
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
    context = get_maintenance_stats()
    context.update({'sections': sections, 'is_admin': request.user.is_superuser})
    return render(request, 'core/manage_sections.html', context)

@login_required
def manage_students(request):
    if not request.user.is_staff: return redirect('home')
    
    if request.method == 'POST':
        # INJECTED: Promote to Beadle Logic
        if 'toggle_beadle' in request.POST:
            student = get_object_or_404(Student, student_number=request.POST.get('student_number'))
            student.is_beadle = not student.is_beadle
            student.save()
            if student.is_beadle and student.section:
                Section.objects.filter(id=student.section.id).update(beadle=student)
            messages.success(request, "Beadle Role Updated!")
            return redirect('manage_students')
            
        # INJECTED: Edit Student Logic
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
            
        # Original: Add Student Logic
        else:
            form = StudentMaintenanceForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    form.save()
                messages.success(request, "Student created successfully!")
                return redirect('manage_students')
    
    students = Student.objects.filter(is_deleted=False).order_by('-created_at')
    sections = Section.objects.all() 
    context = get_maintenance_stats()
    context.update({'students': students, 'sections': sections, 'is_admin': request.user.is_superuser})
    return render(request, 'core/manage_students.html', context)

# ==========================================
# STAFF DASHBOARD (XP UI)
# ==========================================

@login_required
def staff_home(request):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    return render(request, 'core/pis_home.html', context)

@login_required
def staff_dashboard(request):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    students = Student.objects.filter(enrollments__school_year=active_sy, is_deleted=False)
    context['students'] = students
    return render(request, 'core/dashboard.html', context)

@login_required
def disciplinary_module(request, category):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    student = Student.objects.filter(student_number=search_id).first() if search_id else None
    
    records = DisciplinaryRecord.objects.filter(student=student, category=category, school_year=active_sy) if student else []
    
    context.update({
        'module_name': category, 'student': student, 'records': records, 'search_id': search_id
    })
    return render(request, 'core/conduct.html', context)

# INJECTED: Review & Confirm Attendance Logic
@login_required
def staff_attendance_review(request, batch_id):
    if not request.user.is_staff: return redirect('home')
    batch = get_object_or_404(AttendanceBatch, id=batch_id)
    records = batch.records.all().select_related('student')
    context = get_staff_context(request)
    context.update({'batch': batch, 'records': records})
    return render(request, 'core/staff_review.html', context)

@login_required
def staff_attendance_confirm(request, batch_id):
    if not request.user.is_staff: return redirect('home')
    batch = get_object_or_404(AttendanceBatch, id=batch_id)
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    
    with transaction.atomic():
        for record in batch.records.all():
            if record.status in ['ABSENT', 'LATE']:
                DisciplinaryRecord.objects.create(
                    student=record.student,
                    category=record.status,
                    date_of_incident=batch.date,
                    remarks=f"Auto-logged from Beadle report ({batch.section.name})",
                    demerits=1 if record.status == 'LATE' else 5,
                    recorded_by=request.user,
                    school_year=active_sy
                )
        batch.is_confirmed = True
        batch.save()
    messages.success(request, f"Attendance Confirmed and Violations Logged!")
    return redirect('staff_home')

# ==========================================
# PORTALS
# ==========================================

@login_required
def student_dashboard(request): 
    if not hasattr(request.user, 'student_profile'): return redirect('login')
    student = request.user.student_profile
    disc = DisciplinaryRecord.objects.filter(student=student).order_by('-date_of_incident')
    att = AttendanceRecord.objects.filter(student=student).order_by('-date')
    return render(request, 'core/student_dashboard.html', {'student': student, 'discipline_history': disc, 'attendance_history': att})

# INJECTED: Beadle Logic
@login_required
def beadle_dashboard(request): 
    student = getattr(request.user, 'student_profile', None)
    if not student or not student.is_beadle or not student.section: 
        return redirect('student_dashboard')
        
    classmates = student.section.students.filter(is_deleted=False).order_by('last_name')
    
    if request.method == 'POST':
        input_date = request.POST.get('attendance_date')
        with transaction.atomic():
            batch = AttendanceBatch.objects.create(section=student.section, date=input_date, submitted_by=student)
            for s in classmates:
                status = request.POST.get(f'status_{s.student_number}', 'PRESENT')
                AttendanceRecord.objects.create(batch=batch, student=s, date=input_date, status=status)
        return redirect('student_dashboard')
        
    return render(request, 'core/beadle_dashboard.html', {'student': student, 'section_students': classmates, 'today': date.today()})