# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .models import Student, DisciplinaryRecord, SchoolYear, Enrollment
from .forms import StudentForm, DisciplinaryRecordForm

# @login_required(login_url='/admin/login/') # Uncomment when auth is ready
def home(request):
    return render(request, 'core/home.html')

def dashboard(request):
    # Retrieve the Active School Year (Global Session prep)
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if request.method == 'POST':
        # 1. Soft Delete Student
        if 'delete_student' in request.POST:
            student_num = request.POST.get('student_number_to_delete')
            Student.objects.filter(student_number=student_num).update(is_deleted=True)
            return redirect('dashboard')
        
        # 2. Add New Student via Django Form Validation
        elif 'add_student' in request.POST:
            form = StudentForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    # Save Registrar Data
                    student = form.save()
                    
                    # Save Prefect/Enrollment Data
                    if active_sy:
                        Enrollment.objects.create(
                            student=student,
                            school_year=active_sy,
                            date_enrolled=request.POST.get('date_enrolled') or None,
                            is_enrolled=request.POST.get('is_enrolled') == 'on'
                        )
                return redirect('dashboard')
            else:
                # In a real app, send form.errors to the front-end via messages framework
                print("Form Errors:", form.errors)

    # Search Bar Logic (Ignoring soft-deleted students)
    students = Student.objects.filter(is_deleted=False)
    
    search_name = request.GET.get('searchName', '')
    search_id = request.GET.get('searchId', '')

    if search_name:
        students = students.filter(
            Q(last_name__icontains=search_name) | 
            Q(first_name__icontains=search_name)
        )
    if search_id:
        students = students.filter(student_number__icontains=search_id)

    # Eager load enrollments to prevent N+1 DB queries in the template
    students = students.prefetch_related('enrollments')

    context = {
        'students': students,
        'search_name': search_name,
        'search_id': search_id,
        'active_sy': active_sy
    }
    
    return render(request, 'core/dashboard.html', context)


def disciplinary_module(request, category):
    """
    A single DRY view that powers Conduct, Absences, Tardiness, and Suspension.
    category parameter expects: 'conduct', 'absences', 'tardiness', or 'suspension'
    """
    category = category.upper() # Standardize for DB matching
    search_id = request.GET.get('search_id', '')
    student = None
    records = []
    
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    # Fetch History
    if search_id:
        student = Student.objects.filter(student_number=search_id, is_deleted=False).first()
        if student:
            records = DisciplinaryRecord.objects.filter(
                student=student, 
                category=category
            ).select_related('recorded_by').order_by('-date_of_incident')

    # Save Form
    if request.method == 'POST' and 'save_record' in request.POST:
        student_num = request.POST.get('student_number')
        student_obj = get_object_or_404(Student, student_number=student_num, is_deleted=False)
        
        form = DisciplinaryRecordForm(request.POST)
        if form.is_valid() and active_sy:
            record = form.save(commit=False)
            record.student = student_obj
            record.school_year = active_sy
            record.category = category
            # Fallback to a superuser if auth isn't fully set up yet
            record.recorded_by = request.user if request.user.is_authenticated else None
            record.remarks = form.cleaned_data['remarks']
            record.save()
            
            return redirect(f'/discipline/{category.lower()}/?search_id={student_num}')

    return render(request, 'core/conduct.html', {
        'module_name': category, # Send this to HTML so the header can change dynamically
        'student': student, 
        'records': records, 
        'search_id': search_id
    })