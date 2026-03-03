from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import transaction
from .models import Student, DisciplinaryRecord, SchoolYear, Enrollment
from .forms import StudentForm, DisciplinaryRecordForm

def home(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    return render(request, 'core/home.html', {'active_sy': active_sy})

def dashboard(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if request.method == 'POST':
        if 'delete_student' in request.POST:
            student_num = request.POST.get('student_number_to_delete')
            Student.objects.filter(student_number=student_num).update(is_deleted=True)
            return redirect('dashboard')
        
        elif 'add_student' in request.POST:
            form = StudentForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    student = form.save()
                    if active_sy:
                        Enrollment.objects.create(
                            student=student,
                            school_year=active_sy,
                            date_enrolled=request.POST.get('date_enrolled') or None,
                            is_enrolled=request.POST.get('is_enrolled') == 'on'
                        )
                return redirect('dashboard')

        # NEW: Toggle Enrolment Status
        elif 'toggle_enrolment' in request.POST:
            student_num = request.POST.get('student_number_to_toggle')
            student = Student.objects.filter(student_number=student_num, is_deleted=False).first()
            if student and active_sy:
                # Find their enrollment for this year, or create it if missing
                enrollment, created = Enrollment.objects.get_or_create(student=student, school_year=active_sy)
                enrollment.is_enrolled = not enrollment.is_enrolled # Flip the switch
                enrollment.save()
            return redirect('dashboard')

    students = Student.objects.filter(is_deleted=False)
    search_name = request.GET.get('searchName', '')
    search_id = request.GET.get('searchId', '')

    if search_name:
        students = students.filter(Q(last_name__icontains=search_name) | Q(first_name__icontains=search_name))
    if search_id:
        students = students.filter(student_number__icontains=search_id)

    students = students.prefetch_related('enrollments')

    return render(request, 'core/dashboard.html', {
        'students': students, 'search_name': search_name, 'search_id': search_id, 'active_sy': active_sy
    })

def disciplinary_module(request, category):
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    student = None
    records = []
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if search_id:
        student = Student.objects.filter(student_number=search_id, is_deleted=False).first()
        if student:
            records = DisciplinaryRecord.objects.filter(
                student=student, category=category
            ).select_related('recorded_by').order_by('-date_of_incident')

    if request.method == 'POST' and 'save_record' in request.POST:
        student_num = request.POST.get('student_number')
        student_obj = get_object_or_404(Student, student_number=student_num, is_deleted=False)
        form = DisciplinaryRecordForm(request.POST)
        
        if form.is_valid() and active_sy:
            record = form.save(commit=False)
            record.student = student_obj
            record.school_year = active_sy
            record.category = category
            record.recorded_by = request.user if request.user.is_authenticated else None
            record.remarks = form.cleaned_data['remarks']
            record.save()
            return redirect(f'/discipline/{category.lower()}/?search_id={student_num}')

    return render(request, 'core/conduct.html', {
        'module_name': category, 'student': student, 'records': records, 'search_id': search_id, 'active_sy': active_sy
    })