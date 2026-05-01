import json
from datetime import timedelta
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

import uuid
import base64
from django.core.files.base import ContentFile

from .models import Student, DisciplinaryRecord, SchoolYear, Section, Enrollment, StaffProfile, DailyAttendance, PeriodAttendance, StudentPeriodRecord
from .forms import StudentForm, DisciplinaryRecordForm, StaffAccountForm, SectionForm, StudentMaintenanceForm

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
# AUTH & ROUTING
# ==========================================

def login_view(request):
    if request.user.is_authenticated: 
        return redirect('home')
        
    selected_role = None 
        
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        selected_role = request.POST.get('selected_role') 

        user = authenticate(request, username=u, password=p)
        
        if user:
            # TEAMMATE FIX: ROLE RESTRICTION LOGIC 
            if selected_role == 'staff' and not (user.is_staff or user.is_superuser):
                messages.error(request, "Access Denied: This portal is for Faculty, Formators, & Staff. Please use the Students & Beadles portal.")
                return render(request, 'core/login.html', {'selected_role': selected_role})

            if selected_role == 'student' and not hasattr(user, 'student_profile'):
                messages.error(request, "Access Denied: This portal is for Students & Beadles. Faculty/Staff must use the Faculty, Formators, & Staff portal.")
                return render(request, 'core/login.html', {'selected_role': selected_role})

            if selected_role == 'external' and not user.is_superuser:
                messages.error(request, "Access Denied: External portal is currently restricted to system administrators.")
                return render(request, 'core/login.html', {'selected_role': selected_role})

            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid Username or Password')
            
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
                
            return redirect(request.META.get('HTTP_REFERER', 'manage_students'))
            
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
            return redirect(request.META.get('HTTP_REFERER', 'manage_students'))
            
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
                return redirect(request.META.get('HTTP_REFERER', 'manage_students'))
    
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
        if 'toggle_beadle' in request.POST:
            student = get_object_or_404(Student, student_number=request.POST.get('student_number'))
            student.is_beadle = not student.is_beadle
            student.save()
            
            if student.is_beadle and student.section:
                Section.objects.filter(id=student.section.id).update(beadle=student)
            elif not student.is_beadle:
                Section.objects.filter(beadle=student).update(beadle=None)
                
            return redirect(request.META.get('HTTP_REFERER', 'staff_dashboard'))
            
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
            return redirect(request.META.get('HTTP_REFERER', 'staff_dashboard'))
            
        elif 'add_student' in request.POST:
            student_number = request.POST.get('student_number')
            if not Student.objects.filter(student_number=student_number).exists():
                new_student = Student.objects.create(
                    student_number=student_number,
                    first_name=request.POST.get('first_name').upper(),
                    last_name=request.POST.get('last_name').upper(),
                    sex=request.POST.get('sex'),
                    section_id=request.POST.get('section') or None
                )
                
                active_sy_id = request.session.get('active_sy_id')
                active_sy = SchoolYear.objects.filter(id=active_sy_id).first() or SchoolYear.objects.filter(is_active=True).first()
                if active_sy:
                    Enrollment.objects.create(student=new_student, school_year=active_sy)
                    
                messages.success(request, "New student registered successfully!")
            else:
                messages.error(request, "A student with that ID Number already exists!")
            return redirect(request.META.get('HTTP_REFERER', 'staff_dashboard'))

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
    
    filter_range = request.GET.get('filter_range', 'default')
    status_filter = request.GET.get('status', 'all')
    selected_date_str = request.GET.get('filter_date')
    
    batches = PeriodAttendance.objects.filter(is_locked=True).select_related('daily_attendance__section', 'submitted_by')

    today = timezone.now().date()
    if selected_date_str:
        date_obj = timezone.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        batches = batches.filter(daily_attendance__date=date_obj)
    elif filter_range == 'today':
        batches = batches.filter(daily_attendance__date=today)
    elif filter_range == 'yesterday':
        batches = batches.filter(daily_attendance__date=today - timedelta(days=1))
    elif filter_range == 'this_week':
        start_of_week = today - timedelta(days=today.weekday())
        batches = batches.filter(daily_attendance__date__gte=start_of_week)
    elif filter_range == 'default':
        batches = batches.filter(Q(is_approved=False) | Q(daily_attendance__date=today))

    if status_filter == 'approved':
        batches = batches.filter(is_approved=True)
    elif status_filter == 'pending':
        batches = batches.filter(is_approved=False)

    context.update({
        'attendance_batches': batches.order_by('-daily_attendance__date', 'daily_attendance__section', 'period_number'),
        'filter_range': filter_range,
        'status_filter': status_filter,
        'selected_date': selected_date_str,
    })
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
        overrides_made =[] 
        
        with transaction.atomic():
            for rec in batch.records.all():
                override_code = request.POST.get(f'override_{rec.id}')
                
                if override_code and override_code != rec.code:
                    old_status = rec.get_code_display()
                    rec.code = override_code
                    rec.save()
                    new_status = rec.get_code_display()
                    overrides_made.append(f"{rec.student.last_name} ({old_status} ➔ {new_status})")

                if rec.code != 'P':
                    DisciplinaryRecord.objects.create(
                        student=rec.student,
                        category="ATTENDANCE", 
                        offense_name=rec.get_code_display(),
                        date_of_incident=batch.daily_attendance.date,
                        demerits=3 if rec.code == 'A' else 1,
                        remarks="Staff Override" if override_code else "", 
                        recorded_by=request.user,
                        school_year=SchoolYear.objects.filter(is_active=True).first()
                    )

            batch.is_approved = True
            batch.save()
            
            if overrides_made:
                summary = ", ".join(overrides_made)
                messages.success(request, f"✅ Attendance Approved! Overrides logged for: {summary}")
            else:
                messages.success(request, "✅ Attendance successfully approved and logged.")
            
    return redirect('staff_attendance_review', batch_id=batch.id)

@login_required
def api_student_offenses(request, student_id):
    student = get_object_or_404(Student, student_number=student_id)
    
    # 1. HANDLE SAVING PERSONAL INFO
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fields =['address', 'home_phone', 'date_of_birth', 'birthplace', 'citizenship', 'nationality', 'religion', 
                      'brothers', 'sisters', 'guardian_name', 'guardian_address', 'guardian_contact',
                      'father_name', 'father_attainment', 'father_occupation', 'father_office_name', 'father_office_number', 
                      'father_office_address', 'father_contact', 'mother_name', 'mother_attainment', 'mother_occupation', 
                      'mother_office_name', 'mother_office_number', 'mother_office_address', 'mother_contact']
            
            for field in fields:
                if field in data:
                    if field in ['brothers', 'sisters']:
                        val = data[field]
                        setattr(student, field, int(val) if val else 0)
                    else:
                        setattr(student, field, data[field])
            
            # --- FIXED PHOTO SAVING LOGIC ---
            photo_b64 = data.get('photo_base64')
            if photo_b64:
                if photo_b64 == 'DELETE':
                    if student.photo:
                        student.photo.delete(save=False)
                elif photo_b64.startswith('data:image'):
                    format, imgstr = photo_b64.split(';base64,')
                    ext = format.split('/')[-1]
                    if ext == 'jpeg': ext = 'jpg'
                    filename = f"{student.student_number}_{uuid.uuid4().hex[:8]}.{ext}"
                    data_b64 = base64.b64decode(imgstr)
                    
                    if student.photo:
                        student.photo.delete(save=False) # Delete old file
                    student.photo.save(filename, ContentFile(data_b64), save=False)
            
            student.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # 2. HANDLE GETTING DATA
    active_sy_id = request.session.get('active_sy_id')
    sy_filter = {'school_year_id': active_sy_id} if active_sy_id else {'school_year__is_active': True}
    records = DisciplinaryRecord.objects.filter(student=student, **sy_filter).order_by('-date_of_incident')
    
    detailed_records =[]
    for r in records:
        detailed_records.append({
            'date_raw': r.date_of_incident.strftime('%Y-%m-%d'),
            'time': r.time_of_incident.strftime('%I:%M %p') if r.time_of_incident else '12:00 PM',
            'category': r.offense_name if r.offense_name else r.category,
            'demerits': r.demerits,
            'status': 'Excused' if r.is_excused else 'Unexcused',
            'sanction': r.sanction or '',
            'notes': r.remarks or '',
            'served': r.is_served
        })
        
    summary = records.values('category').annotate(count=Count('id')).order_by('category')
    summary_list = [{'category': s['category'], 'count': s['count']} for s in summary]
    
    # 3. BUILD PERSONAL INFO PAYLOAD
    student_info = {
        'photo_url': student.photo.url if student.photo else '', 
        'address': student.address, 'home_phone': student.home_phone, 
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
        'birthplace': student.birthplace, 'citizenship': student.citizenship, 'nationality': student.nationality,
        'religion': student.religion, 'brothers': student.brothers, 'sisters': student.sisters,
        'guardian_name': student.guardian_name, 'guardian_address': student.guardian_address, 'guardian_contact': student.guardian_contact,
        'father_name': student.father_name, 'father_attainment': student.father_attainment, 'father_occupation': student.father_occupation,
        'father_office_name': student.father_office_name, 'father_office_number': student.father_office_number, 'father_office_address': student.father_office_address,
        'father_contact': student.father_contact, 'mother_name': student.mother_name, 'mother_attainment': student.mother_attainment,
        'mother_occupation': student.mother_occupation, 'mother_office_name': student.mother_office_name, 'mother_office_number': student.mother_office_number,
        'mother_office_address': student.mother_office_address, 'mother_contact': student.mother_contact
    }
    
    return JsonResponse({
        'records': detailed_records,
        'summary': summary_list,
        'student_info': student_info 
    })

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
                original_code = request.POST.get(f'original_code_{s.id}')
                note = request.POST.get(f'note_{s.id}')
                
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

    daily_att = DailyAttendance.objects.filter(date=today, section=section).first()
    
    today_periods = daily_att.periods.filter(is_locked=True).prefetch_related('records__student').order_by('period_number') if daily_att else []
    submitted_period_numbers =[p.period_number for p in today_periods]

    context = {
        'student': student,
        'section_students': section_students,
        'today': today,
        'today_periods': today_periods,
        'submitted_period_numbers': submitted_period_numbers, 
    }
    return render(request, 'core/beadle_dashboard.html', context)

def api_get_offenses(request):
    """Returns the official list of offenses for the dropdowns"""
    from .models import Offense
    offenses = list(Offense.objects.values('id', 'name', 'default_demerits', 'default_sanction', 'default_count'))
    return JsonResponse({'offenses': offenses})