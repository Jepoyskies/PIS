import random
from datetime import date, timedelta
from django.utils import timezone  # Added for timezone.now()
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import (
    SchoolYear, Teacher, Section, Student, Enrollment, 
    DailyAttendance, PeriodAttendance, StudentPeriodRecord,
    StaffProfile, DisciplinaryRecord  # Added these missing models
)

class Command(BaseCommand):
    help = 'Seeds the database with realistic sample data for the PIS system.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Clear existing data
        # Order matters because of Foreign Key constraints
        StudentPeriodRecord.objects.all().delete()
        PeriodAttendance.objects.all().delete()
        DailyAttendance.objects.all().delete()
        DisciplinaryRecord.objects.all().delete()
        Enrollment.objects.all().delete()
        Student.objects.all().delete()
        Section.objects.all().delete()
        Teacher.objects.all().delete()
        SchoolYear.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        # 2. Create Superuser (if not exists)
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin / admin123'))

        # 3. Create School Years
        sy1 = SchoolYear.objects.create(code='2024-2025', is_active=False)
        sy2 = SchoolYear.objects.create(code='2025-2026', is_active=True)
        self.stdout.write('School Years created.')

        # 4. Create Teachers
        prefixes = ['Mr.', 'Ms.', 'Mrs.']
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'Robert', 'Emily', 'William', 'Jessica']
        last_names = ['Doe', 'Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Moore', 'Taylor']
        
        teachers = []
        for i in range(10):
            t = Teacher.objects.create(
                prefix=random.choice(prefixes),
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                is_active=True
            )
            teachers.append(t)
        self.stdout.write(f'{len(teachers)} Teachers created.')

        # 5. Create Sections
        sections = []
        section_names = ['ST. IGNATIUS', 'ST. FRANCIS', 'ST. BENEDICT', 'ST. SCHOLASTICA', 'ST. AUGUSTINE', 'ST. MONICA']
        for i, name in enumerate(section_names):
            grade = (i // 2) + 7  # Gr 7, 8, 9
            s = Section.objects.create(
                grade_level=grade,
                name=name,
                moderator=random.choice(teachers)
            )
            sections.append(s)
        self.stdout.write(f'{len(sections)} Sections created.')

        # 6. Create Staff Profiles
        staff_users = [
            ('prefect_staff', 'P001', 'Prefect Office'),
            ('registrar_staff', 'R001', 'Registrar Office'),
        ]
        for username, emp_id, dept in staff_users:
            u = User.objects.create_user(username=username, password=username)
            u.is_staff = True
            u.save()
            StaffProfile.objects.create(user=u, employee_id=emp_id, department=dept)
        self.stdout.write('Staff accounts created.')

        # 7. Create Students
        student_data = [
            ('2024-0001', 'DELA CRUZ', 'JUAN', 'M'),
            ('2024-0002', 'SANTOS', 'MARIA', 'F'),
            ('2024-0003', 'REYES', 'PEDRO', 'M'),
            ('2024-0004', 'BAUTISTA', 'ANA', 'F'),
            ('2024-0005', 'GARCIA', 'JOSE', 'M'),
            ('2024-0006', 'LOPEZ', 'ELENA', 'F'),
            ('2024-0007', 'CASTRO', 'RICARDO', 'M'),
            ('2024-0008', 'MENDOZA', 'SOFIA', 'F'),
            ('2024-0009', 'TORRES', 'MANUEL', 'M'),
            ('2024-0010', 'VILLANUEVA', 'ISABELLA', 'F'),
            ('2024-0011', 'CRUZ', 'ANTONIO', 'M'),
            ('2024-0012', 'RAMOS', 'CARMEN', 'F'),
            ('2024-0013', 'DIMAGIBA', 'ESTEBAN', 'M'),
            ('2024-0014', 'AGUINALDO', 'EMILIO', 'M'),
            ('2024-0015', 'BONIFACIO', 'ANDRES', 'M'),
            ('2024-0016', 'SILANG', 'GABRIELA', 'F'),
            ('2024-0017', 'RIZAL', 'JOSE', 'M'),
            ('2024-0018', 'JAENA', 'GRACIANO', 'M'),
            ('2024-0019', 'MABINI', 'APOLINARIO', 'M'),
            ('2024-0020', 'LUNA', 'ANTONIO', 'M'),
        ]

        all_students = []
        for sn, ln, fn, sex in student_data:
            section = random.choice(sections)
            student = Student.objects.create(
                student_number=sn,
                last_name=ln,
                first_name=fn,
                sex=sex,
                date_of_birth=date(2010, random.randint(1, 12), random.randint(1, 28)),
                address="Cagayan de Oro City",
                section=section
            )
            all_students.append(student)
            Enrollment.objects.create(student=student, school_year=sy2, is_enrolled=True)
        
        self.stdout.write(f'{len(all_students)} Students created.')

        # 8. Assign Beadles
        for sec in sections:
            sec_students = Student.objects.filter(section=sec)
            if sec_students.exists():
                beadle = random.choice(sec_students)
                beadle.is_beadle = True
                beadle.save()
                sec.beadle = beadle
                sec.save()
        self.stdout.write('Beadles assigned.')

        # 9. Create Disciplinary Records
        categories = ['Absences', 'Tardiness', 'Conduct', 'Suspension']
        remarks_list = ['Unruly behavior during assembly.', 'Frequent tardiness in the morning.', 'Cutting classes.', 'Disrespectful towards teacher.']
        prefect_user = User.objects.get(username='prefect_staff')
        
        for i in range(15):
            student = random.choice(all_students)
            DisciplinaryRecord.objects.create(
                student=student,
                category=random.choice(categories),
                date_of_incident=date.today() - timedelta(days=random.randint(1, 30)),
                remarks=random.choice(remarks_list),
                demerits=random.randint(5, 20),
                recorded_by=prefect_user,
                school_year=sy2
            )
        self.stdout.write('Disciplinary Records created.')

        # 10. Create Attendance Batches & Records
        self.stdout.write("Seeding sample attendance...")
        today = timezone.now().date()
        
        for sec in sections:
            if not sec.beadle:
                continue
            
            # 1. Create Daily record for this section
            daily, _ = DailyAttendance.objects.get_or_create(
                date=today, 
                section=sec
            )
            
            # 2. Create Period 1 record
            period, _ = PeriodAttendance.objects.get_or_create(
                daily_attendance=daily,
                period_number=1,
                defaults={
                    'submitted_by': sec.beadle,
                    'submitted_at': timezone.now(),
                    'is_locked': True
                }
            )
            
            # 3. Create records for every student in this section
            sec_students = Student.objects.filter(section=sec)
            for student in sec_students:
                # Randomize status code
                status_code = random.choices(['P', 'A', 'L'], weights=[85, 5, 10])[0]
                StudentPeriodRecord.objects.create(
                    period=period,
                    student=student,
                    code=status_code
                )
                
        self.stdout.write('Attendance data created.')
        self.stdout.write(self.style.SUCCESS('Successfully seeded database.'))