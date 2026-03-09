from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import pandas as pd

# Import ALL your models
from .models import Student, DisciplinaryRecord, SchoolYear, Enrollment, CommunityServiceRecord, Section, Subject, Teacher, TeacherLoad
from .forms import StudentForm, DisciplinaryRecordForm

# ==========================================
# AUTHENTICATION
# ==========================================
def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Name or Password')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ==========================================
# MAIN GATEKEEPER
# ==========================================
@login_required(login_url='login')
def home(request):
    return render(request, 'core/home.html')

# ==========================================
# RIS (REGISTRAR) VIEWS
# ==========================================
@login_required(login_url='login')
def ris_dashboard(request):
    return redirect('ris_sections') 

@login_required(login_url='login')
def ris_sections(request):
    selected_grade = int(request.GET.get('grade', 7))
    if request.method == 'POST':
        if 'add_section' in request.POST:
            name = request.POST.get('section_name')
            campus = request.POST.get('campus', 'PUEBLO')
            moderator_id = request.POST.get('moderator_id')
            if name:
                Section.objects.create(
                    grade_level=selected_grade, name=name.upper(), campus=campus.upper(),
                    moderator_id=moderator_id if moderator_id else None
                )
            return redirect(f'/ris/sections/?grade={selected_grade}')
            
        elif 'add_subject' in request.POST:
            name = request.POST.get('subject_name')
            if name:
                Subject.objects.create(grade_level=selected_grade, name=name.upper())
            return redirect(f'/ris/sections/?grade={selected_grade}')

    sections = Section.objects.filter(grade_level=selected_grade).order_by('name')
    subjects = Subject.objects.filter(grade_level=selected_grade).order_by('name')
    teachers = Teacher.objects.filter(is_active=True).order_by('last_name')

    return render(request, 'core/ris_sections.html', {
        'selected_grade': selected_grade, 'sections': sections, 'subjects': subjects,
        'teachers': teachers, 'grade_levels': [7, 8, 9, 10]
    })

@login_required(login_url='login')
def ris_teacher_load(request):
    selected_teacher_id = request.GET.get('teacher_id')
    filter_status = request.GET.get('filter', 'active')
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if request.method == 'POST':
        if 'add_teacher' in request.POST:
            Teacher.objects.create(
                prefix=request.POST.get('prefix', '').upper(),
                last_name=request.POST.get('last_name', '').upper(),
                first_name=request.POST.get('first_name', '').upper()
            )
            return redirect(f'/ris/teacher-load/?filter={filter_status}')
            
        elif 'add_load' in request.POST and selected_teacher_id and active_sy:
            section_id = request.POST.get('section_id')
            subject_id = request.POST.get('subject_id')
            if section_id and subject_id:
                TeacherLoad.objects.create(
                    teacher_id=selected_teacher_id, section_id=section_id,
                    subject_id=subject_id, school_year=active_sy
                )
            return redirect(f'/ris/teacher-load/?teacher_id={selected_teacher_id}&filter={filter_status}')
            
        elif 'toggle_status' in request.POST and selected_teacher_id:
            t = get_object_or_404(Teacher, id=selected_teacher_id)
            t.is_active = not t.is_active
            t.save()
            return redirect(f'/ris/teacher-load/?teacher_id={selected_teacher_id}&filter={filter_status}')

    # Fetch Data
    if filter_status == 'active': teachers = Teacher.objects.filter(is_active=True).order_by('last_name')
    elif filter_status == 'inactive': teachers = Teacher.objects.filter(is_active=False).order_by('last_name')
    else: teachers = Teacher.objects.all().order_by('last_name')

    selected_teacher = None
    teacher_loads = []
    if selected_teacher_id:
        selected_teacher = Teacher.objects.filter(id=selected_teacher_id).first()
        if selected_teacher:
            teacher_loads = TeacherLoad.objects.filter(teacher=selected_teacher, school_year=active_sy)

    sections = Section.objects.all().order_by('grade_level', 'name')
    subjects = Subject.objects.all().order_by('grade_level', 'name')

    return render(request, 'core/ris_teacher_load.html', {
        'teachers': teachers, 'selected_teacher': selected_teacher, 'teacher_loads': teacher_loads,
        'filter_status': filter_status, 'sections': sections, 'subjects': subjects,
    })

@login_required(login_url='login')
def ris_enrolment(request):
    selected_section_id = request.GET.get('section_id')
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if request.method == 'POST' and active_sy:
        # Assign a student to this section
        if 'assign_student' in request.POST and selected_section_id:
            student_num = request.POST.get('student_number')
            student = Student.objects.filter(student_number=student_num).first()
            if student:
                enrollment, created = Enrollment.objects.get_or_create(student=student, school_year=active_sy)
                enrollment.section_id = selected_section_id
                enrollment.is_enrolled = True
                enrollment.save()
            return redirect(f'/ris/enrolment/?section_id={selected_section_id}')
            
        # Remove a student from this section
        elif 'remove_student' in request.POST:
            enrollment_id = request.POST.get('enrollment_id')
            enrollment = Enrollment.objects.filter(id=enrollment_id).first()
            if enrollment:
                enrollment.section = None
                enrollment.save()
            return redirect(f'/ris/enrolment/?section_id={selected_section_id}')

    # Fetch data for the UI
    sections = Section.objects.all().order_by('grade_level', 'name')
    selected_section = None
    enrolled_students = []
    available_students = []

    if selected_section_id:
        selected_section = Section.objects.filter(id=selected_section_id).first()
        if selected_section:
            # Get students in this section
            enrolled_students = Enrollment.objects.filter(section=selected_section, school_year=active_sy).select_related('student').order_by('student__last_name')
            
            # Get students NOT in any section yet (for the dropdown)
            assigned_student_ids = Enrollment.objects.filter(school_year=active_sy, section__isnull=False).values_list('student_id', flat=True)
            available_students = Student.objects.filter(is_deleted=False).exclude(id__in=assigned_student_ids).order_by('last_name')

    return render(request, 'core/ris_enrolment.html', {
        'sections': sections,
        'selected_section': selected_section,
        'enrolled_students': enrolled_students,
        'available_students': available_students,
    })

# ==========================================
# PIS (PREFECT) VIEWS
# ==========================================
@login_required(login_url='login')
def pis_home(request):
    return render(request, 'core/pis_home.html')

@login_required(login_url='login')
def pis_dashboard(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if request.method == 'POST':
        if 'import_excel' in request.FILES:
            if not active_sy:
                messages.error(request, "Cannot import: No Active School Year.")
                return redirect('pis_dashboard')
            excel_file = request.FILES['import_excel']
            try:
                df = pd.read_excel(excel_file).fillna('')
                with transaction.atomic():
                    for index, row in df.iterrows():
                        student_num = str(row.get('Student Number', '')).strip()
                        if not student_num: continue
                        last_name = str(row.get('Last Name', '')).strip()
                        first_name = str(row.get('First Name', '')).strip()
                        sex = str(row.get('Sex', '')).strip().upper()[:1]
                        student, created = Student.objects.update_or_create(
                            student_number=student_num,
                            defaults={'last_name': last_name, 'first_name': first_name, 'sex': sex if sex in ['M', 'F'] else 'M'}
                        )
                        Enrollment.objects.update_or_create(student=student, school_year=active_sy, defaults={'is_enrolled': True})
                messages.success(request, "Imported successfully!")
            except Exception as e:
                messages.error(request, f"Error: {e}")
            return redirect('pis_dashboard')

        elif 'delete_student' in request.POST:
            student_num = request.POST.get('student_number_to_delete')
            Student.objects.filter(student_number=student_num).update(is_deleted=True)
            return redirect('pis_dashboard')
        
        elif 'add_student' in request.POST:
            form = StudentForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    student = form.save()
                    if active_sy:
                        Enrollment.objects.create(
                            student=student, school_year=active_sy,
                            date_enrolled=request.POST.get('date_enrolled') or None,
                            is_enrolled=request.POST.get('is_enrolled') == 'on'
                        )
                return redirect('pis_dashboard')

        elif 'toggle_enrolment' in request.POST:
            student_num = request.POST.get('student_number_to_toggle')
            student = Student.objects.filter(student_number=student_num, is_deleted=False).first()
            if student and active_sy:
                enrollment, created = Enrollment.objects.get_or_create(student=student, school_year=active_sy)
                enrollment.is_enrolled = not enrollment.is_enrolled
                enrollment.save()
            return redirect('pis_dashboard')
        
        elif 'log_cs_hours' in request.POST:
            student_num = request.POST.get('student_number')
            student = Student.objects.filter(student_number=student_num, is_deleted=False).first()
            if student and active_sy:
                CommunityServiceRecord.objects.create(
                    student=student, school_year=active_sy, date_served=request.POST.get('date_served'),
                    hours_served=request.POST.get('hours_served'), remarks=request.POST.get('remarks')
                )
            return redirect('pis_dashboard')

    students = Student.objects.filter(is_deleted=False)
    search_name = request.GET.get('searchName', '')
    search_id = request.GET.get('searchId', '')

    if search_name: students = students.filter(Q(last_name__icontains=search_name) | Q(first_name__icontains=search_name))
    if search_id: students = students.filter(student_number__icontains=search_id)
    students = students.prefetch_related('enrollments').order_by('last_name', 'first_name')

    return render(request, 'core/dashboard.html', {'students': students, 'search_name': search_name, 'search_id': search_id, 'active_sy': active_sy})

@login_required(login_url='login')
def disciplinary_module(request, category):
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    student = None
    records = []
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if search_id:
        student = Student.objects.filter(student_number=search_id, is_deleted=False).first()
        if student:
            records = DisciplinaryRecord.objects.filter(student=student, category=category).select_related('recorded_by').order_by('-date_of_incident')

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
            return redirect(f'/pis/discipline/{category.lower()}/?search_id={student_num}')

    return render(request, 'core/conduct.html', {'module_name': category, 'student': student, 'records': records, 'search_id': search_id, 'active_sy': active_sy})