from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction

from .models import Student, DisciplinaryRecord, SchoolYear, Section, Enrollment, StaffProfile
from .forms import StudentForm, DisciplinaryRecordForm, StaffAccountForm, SectionForm, StudentMaintenanceForm
from .decorators import admin_required, staff_required, beadle_required

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
    return {'all_school_years': all_school_years, 'active_sy': active_sy}

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
@staff_required
def maintenance_dashboard(request):
    context = get_maintenance_stats()
    context['is_admin'] = request.user.is_superuser
    return render(request, 'core/maintenance_dashboard.html', context)

@login_required
@admin_required
def manage_staff(request):
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
    context.update({
        'form': form,
        'staff_list': staff_list,
        'is_admin': request.user.is_superuser
    })
    return render(request, 'core/manage_staff_ui.html', context)

@login_required
@staff_required
def manage_sections(request):
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
@staff_required
def manage_students(request):
    if request.method == 'POST':
        form = StudentMaintenanceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save() # This also triggers the auto-User account creation
            messages.success(request, "Student created successfully!")
            return redirect('manage_students')
    
    students = Student.objects.filter(is_deleted=False).order_by('-created_at')
    sections = Section.objects.all() # Needed for the dropdown
    context = get_maintenance_stats()
    context.update({'students': students, 'sections': sections, 'is_admin': request.user.is_superuser})
    return render(request, 'core/manage_students.html', context)

# ==========================================
# STAFF DASHBOARD (XP UI)
# ==========================================

@login_required
@staff_required
def staff_home(request):
    context = get_staff_context(request)
    return render(request, 'core/pis_home.html', context)

@login_required
@staff_required
def staff_dashboard(request):
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    students = Student.objects.filter(enrollments__school_year=active_sy, is_deleted=False)
    context['students'] = students
    return render(request, 'core/dashboard.html', context)

@login_required
@staff_required
def disciplinary_module(request, category):
    context = get_staff_context(request)
    active_sy = context.get('active_sy')
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    student = Student.objects.filter(student_number=search_id).first() if search_id else None
    
    # Ternary operator to get records for the specific student and category
    records = DisciplinaryRecord.objects.filter(student=student, category=category, school_year=active_sy) if student else []
    
    context.update({
        'module_name': category, 'student': student, 'records': records, 'search_id': search_id
    })
    return render(request, 'core/conduct.html', context)

# ==========================================
# PORTALS
# ==========================================

@login_required
def beadle_dashboard(request): 
    return render(request, 'core/beadle_dashboard.html')

@login_required
def student_dashboard(request): 
    return render(request, 'core/student_dashboard.html')

def staff_attendance_review(request): 
    return render(request, 'core/maintenance.html', {'msg': 'Attendance Review'})