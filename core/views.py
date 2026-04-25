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
        
    # INJECTED: Temporarily empty while we rebuild the Staff Review Module
    pending_batches =[]
        
    context = {
        'all_school_years': all_school_years, 
        'active_sy': active_sy, 
        'pending_batches': pending_batches,
        'is_admin': request.user.is_superuser # Unify Sidebar Logic
    }
    
    # Task 1: Unify Sidebar Logic - Merge Maintenance Stats
    context.update(get_maintenance_stats())
    
    return context

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
    
    # CHANGED: Use get_staff_context so the School Year dropdown works
    context = get_staff_context(request) 
    context.update({'sections': sections})
    
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
    
    # ==========================================
    # 1. HANDLE POST REQUESTS (Add, Edit, Beadle)
    # ==========================================
    if request.method == 'POST':
        # TOGGLE BEADLE
        if 'toggle_beadle' in request.POST:
            student = get_object_or_404(Student, student_number=request.POST.get('student_number'))
            student.is_beadle = not student.is_beadle
            student.save()
            
            # If made a beadle, assign them to their section
            if student.is_beadle and student.section:
                Section.objects.filter(id=student.section.id).update(beadle=student)
                
            status = "assigned as Beadle" if student.is_beadle else "revoked from Beadle"
            messages.success(request, f"{student.first_name} {student.last_name} was {status}!")
            return redirect('staff_dashboard')
            
        # EDIT STUDENT
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
            messages.success(request, "Student details updated successfully!")
            return redirect('staff_dashboard')
            
        # ADD STUDENT
        elif 'add_student' in request.POST:
            student_number = request.POST.get('student_number')
            if not Student.objects.filter(student_number=student_number).exists():
                Student.objects.create(
                    student_number=student_number,
                    first_name=request.POST.get('first_name').upper(),
                    last_name=request.POST.get('last_name').upper(),
                    sex=request.POST.get('sex'),
                    section_id=request.POST.get('section') or None
                )
                messages.success(request, "New student registered successfully!")
            else:
                messages.error(request, "A student with that ID Number already exists!")
            return redirect('staff_dashboard')

    # ==========================================
    # 2. HANDLE GET REQUESTS & RENDER PAGE
    # ==========================================
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    
    # Grab search parameters if they exist
    search_name = request.GET.get('searchName', '')
    search_id = request.GET.get('searchId', '')
    
    # Base Queryset
    students = Student.objects.filter(enrollments__school_year=active_sy, is_deleted=False)
    
    # Apply Search Filters
    if search_name:
        students = students.filter(last_name__icontains=search_name) | students.filter(first_name__icontains=search_name)
    if search_id:
        students = students.filter(student_number__icontains=search_id)
        
    context['students'] = students.distinct()
    context['search_name'] = search_name
    context['search_id'] = search_id
    
    # Pass sections so the Add/Edit dropdowns work
    context['sections'] = Section.objects.all().order_by('grade_level')
    
    return render(request, 'core/dashboard.html', context)

@login_required
def disciplinary_module(request, category):
    if not request.user.is_staff: return redirect('home')
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    
    # 1. Try to find a specific student if an ID was entered
    student = Student.objects.filter(student_number=search_id).first() if search_id else None
    
    # 2. UPDATED LOGIC:
    if student:
        # If a student is searched, show only their records
        records = DisciplinaryRecord.objects.filter(
            student=student, 
            category=category, 
            school_year=active_sy
        ).order_by('-date_of_incident')
    else:
        # If NO search, show the 50 most recent records for this category school-wide
        records = DisciplinaryRecord.objects.filter(
            category=category, 
            school_year=active_sy
        ).order_by('-date_of_incident')[:50] 
    
    context.update({
        'module_name': category, 
        'student': student, 
        'records': records, 
        'search_id': search_id
    })
    return render(request, 'core/conduct.html', context)

# INJECTED: Review & Confirm Attendance Logic
@login_required
def staff_attendance_review(request, batch_id):
    pass

@login_required
def staff_attendance_confirm(request, batch_id):
    pass

@login_required
def api_student_offenses(request, student_id):
    active_sy_id = request.session.get('active_sy_id')
    sy_filter = {'school_year_id': active_sy_id} if active_sy_id else {'school_year__is_active': True}
    
    # Get all records for this student in the active school year
    records = DisciplinaryRecord.objects.filter(student__student_number=student_id, **sy_filter).order_by('-date_of_incident')
    
    # 1. Format data for the detailed modal
    detailed_records =[]
    for r in records:
        detailed_records.append({
            'date': r.date_of_incident.strftime('%m/%d/%Y'),
            'category': r.category,
            'offense': r.remarks, # You can change this later when you add specific dropdowns
            'demerits': r.demerits,
        })
        
    # 2. Format data for the "Offenses By Type" Modal (Groups them and counts them)
    summary = records.values('category').annotate(count=Count('id')).order_by('category')
    summary_list = [{'category': s['category'], 'count': s['count']} for s in summary]
    
    return JsonResponse({
        'records': detailed_records,
        'summary': summary_list
    })

@login_required
def reports_dashboard(request):
    if not request.user.is_staff: return redirect('home')
    
    # Leverages your existing helper to load school years, active_sy, etc.
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
    
    # Safely load the new attendance format for the student dashboard
    att_history = StudentPeriodRecord.objects.filter(student=student).order_by('-period__daily_attendance__date', '-period__period_number')[:20]
    
    return render(request, 'core/student_dashboard.html', {
        'student': student, 
        'discipline_history': disc, 
        'attendance_history': att_history
    })

# INJECTED: Beadle Logic
@login_required
def beadle_dashboard(request):
    student = get_object_or_404(Student, user=request.user)
    if not student.is_beadle or not student.section:
        return redirect('student_dashboard')

    section = student.section
    section_students = section.students.filter(is_deleted=False).order_by('last_name', 'first_name')
    today = timezone.now().date()

    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        period_number = int(request.POST.get('period_number'))
        
        daily_att, created = DailyAttendance.objects.get_or_create(date=attendance_date, section=section)
        
        period_att, p_created = PeriodAttendance.objects.get_or_create(
            daily_attendance=daily_att,
            period_number=period_number,
            defaults={'submitted_by': student, 'submitted_at': timezone.now()}
        )
        
        if not period_att.is_locked:
            period_att.records.all().delete() 
            for s in section_students:
                code = request.POST.get(f'code_{s.id}', 'P') 
                
                # --- PULL THE HIDDEN DATA FROM THE HTML ---
                original_code = request.POST.get(f'original_code_{s.id}')
                note = request.POST.get(f'note_{s.id}')
                
                # --- SAVE EVERYTHING TO THE DATABASE ---
                StudentPeriodRecord.objects.create(
                    period=period_att, 
                    student=s, 
                    code=code,
                    original_code=original_code,
                    note=note
                )
            
            period_att.is_locked = True
            period_att.save()
            messages.success(request, f"Period {period_number} attendance confirmed and locked!")
            return redirect('beadle_dashboard')
        else:
            messages.error(request, f"Period {period_number} is already locked. Go to the Prefect Office for changes.")

    # Fetch History for the History Tab
    daily_att = DailyAttendance.objects.filter(date=today, section=section).first()
    today_periods = daily_att.periods.all().prefetch_related('records__student').order_by('period_number') if daily_att else []
    
    # NEW: Create a quick list of numbers (e.g.,[1, 2]) that are already locked today
    submitted_period_numbers =[p.period_number for p in today_periods if p.is_locked]

    context = {
        'student': student,
        'section_students': section_students,
        'today': today,
        'today_periods': today_periods,
        'submitted_period_numbers': submitted_period_numbers, # NEW: Pass it to the template
    }
    return render(request, 'core/beadle_dashboard.html', context)