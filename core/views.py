from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from .models import (
    Student,
    DisciplinaryRecord,
    SchoolYear,
    Enrollment,
    CommunityServiceRecord,
    Section,
    Subject
)
from .forms import StudentForm, DisciplinaryRecordForm
import pandas as pd
from datetime import datetime


# =========================
# AUTH
# =========================

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


# =========================
# HOME
# =========================

@login_required(login_url='login')
def home(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    return render(request, 'core/home.html', {'active_sy': active_sy})


# =========================
# RIS DASHBOARD (NEW)
# =========================

@login_required(login_url='login')
def ris_dashboard(request):
    # Registrar side main screen
    # For now redirect to Sections module
    return redirect('ris_sections')


# =========================
# PIS DASHBOARD (OLD DASHBOARD RENAMED)
# =========================

@login_required(login_url='login')
def pis_dashboard(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if request.method == 'POST':

        # 1️⃣ EXCEL IMPORT
        if 'import_excel' in request.FILES:
            if not active_sy:
                messages.error(request, "Cannot import: No Active School Year set in Admin.")
                return redirect('pis_dashboard')

            excel_file = request.FILES['import_excel']

            try:
                df = pd.read_excel(excel_file)
                df = df.fillna('')

                with transaction.atomic():
                    for index, row in df.iterrows():
                        student_num = str(row.get('Student Number', '')).strip()
                        if not student_num:
                            continue

                        last_name = str(row.get('Last Name', '')).strip()
                        first_name = str(row.get('First Name', '')).strip()
                        sex = str(row.get('Sex', '')).strip().upper()[:1]

                        student, created = Student.objects.update_or_create(
                            student_number=student_num,
                            defaults={
                                'last_name': last_name,
                                'first_name': first_name,
                                'sex': sex if sex in ['M', 'F'] else 'M',
                            }
                        )

                        Enrollment.objects.update_or_create(
                            student=student,
                            school_year=active_sy,
                            defaults={'is_enrolled': True}
                        )

                messages.success(request, "Excel data imported successfully!")

            except Exception as e:
                messages.error(request, f"Error importing file: {e}")

            return redirect('pis_dashboard')

        # 2️⃣ DELETE STUDENT
        elif 'delete_student' in request.POST:
            student_num = request.POST.get('student_number_to_delete')
            Student.objects.filter(student_number=student_num).update(is_deleted=True)
            return redirect('pis_dashboard')

        # 3️⃣ ADD SINGLE STUDENT
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
                return redirect('pis_dashboard')

        # 4️⃣ TOGGLE ENROLMENT
        elif 'toggle_enrolment' in request.POST:
            student_num = request.POST.get('student_number_to_toggle')
            student = Student.objects.filter(
                student_number=student_num,
                is_deleted=False
            ).first()

            if student and active_sy:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    school_year=active_sy
                )
                enrollment.is_enrolled = not enrollment.is_enrolled
                enrollment.save()

            return redirect('pis_dashboard')

        # 5️⃣ LOG COMMUNITY SERVICE
        elif 'log_cs_hours' in request.POST:
            student_num = request.POST.get('student_number')
            student = Student.objects.filter(
                student_number=student_num,
                is_deleted=False
            ).first()

            if student and active_sy:
                CommunityServiceRecord.objects.create(
                    student=student,
                    school_year=active_sy,
                    date_served=request.POST.get('date_served'),
                    hours_served=request.POST.get('hours_served'),
                    remarks=request.POST.get('remarks')
                )

            return redirect('pis_dashboard')

    # GET REQUEST (Student Grid)
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

    students = students.prefetch_related('enrollments').order_by(
        'last_name', 'first_name'
    )

    return render(request, 'core/dashboard.html', {
        'students': students,
        'search_name': search_name,
        'search_id': search_id,
        'active_sy': active_sy
    })


# =========================
# DISCIPLINE MODULE
# =========================

@login_required(login_url='login')
def disciplinary_module(request, category):
    category = category.upper()
    search_id = request.GET.get('search_id', '')
    student = None
    records = []
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if search_id:
        student = Student.objects.filter(
            student_number=search_id,
            is_deleted=False
        ).first()

        if student:
            records = DisciplinaryRecord.objects.filter(
                student=student,
                category=category
            ).select_related('recorded_by').order_by('-date_of_incident')

    if request.method == 'POST' and 'save_record' in request.POST:
        student_num = request.POST.get('student_number')
        student_obj = get_object_or_404(
            Student,
            student_number=student_num,
            is_deleted=False
        )

        form = DisciplinaryRecordForm(request.POST)

        if form.is_valid() and active_sy:
            record = form.save(commit=False)
            record.student = student_obj
            record.school_year = active_sy
            record.category = category
            record.recorded_by = request.user
            record.save()

            return redirect(
                f'/discipline/{category.lower()}/?search_id={student_num}'
            )

    return render(request, 'core/conduct.html', {
        'module_name': category,
        'student': student,
        'records': records,
        'search_id': search_id,
        'active_sy': active_sy
    })


# =========================
# RIS SECTIONS
# =========================

@login_required(login_url='login')
def ris_sections(request):
    selected_grade = int(request.GET.get('grade', 7))

    sections = Section.objects.filter(
        grade_level=selected_grade
    ).order_by('name')

    subjects = Subject.objects.filter(
        grade_level=selected_grade
    ).order_by('name')

    return render(request, 'core/ris_sections.html', {
        'selected_grade': selected_grade,
        'sections': sections,
        'subjects': subjects,
        'grade_levels': [7, 8, 9, 10]
    })

@login_required(login_url='login')
def pis_home(request):
    return render(request, 'core/pis_home.html')