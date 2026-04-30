from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone

class TimeStampedModel(models.Model):
    """Abstract base class ensuring every table has audit timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SchoolYear(TimeStampedModel):
    code = models.CharField(max_length=9, unique=True, help_text="e.g., 2025-2026")
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.code

class Teacher(TimeStampedModel):
    prefix = models.CharField(max_length=10, help_text="e.g., Mr., Ms., Bro., Fr.")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.prefix} {self.last_name}, {self.first_name}"

class Section(TimeStampedModel):
    grade_level = models.IntegerField()
    name = models.CharField(max_length=100)
    moderator = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    beadle = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='beadle_of')

    def __str__(self):
        return f"Gr {self.grade_level} - {self.name}"

class StaffProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, default="Prefect Office")

    def __str__(self):
        return self.user.username

class Student(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
    student_number = models.CharField(max_length=20, unique=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=10, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    # NEW: EXTENDED PERSONAL & FAMILY INFORMATION
    home_phone = models.CharField(max_length=50, blank=True, null=True)
    birthplace = models.CharField(max_length=255, blank=True, null=True)
    citizenship = models.CharField(max_length=50, blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    religion = models.CharField(max_length=100, blank=True, null=True)
    brothers = models.IntegerField(default=0)
    sisters = models.IntegerField(default=0)
    
    guardian_name = models.CharField(max_length=255, blank=True, null=True)
    guardian_address = models.CharField(max_length=255, blank=True, null=True)
    guardian_contact = models.CharField(max_length=50, blank=True, null=True)

    father_name = models.CharField(max_length=255, blank=True, null=True)
    father_attainment = models.CharField(max_length=255, blank=True, null=True)
    father_occupation = models.CharField(max_length=255, blank=True, null=True)
    father_office_name = models.CharField(max_length=255, blank=True, null=True)
    father_office_number = models.CharField(max_length=50, blank=True, null=True)
    father_office_address = models.CharField(max_length=255, blank=True, null=True)
    father_contact = models.CharField(max_length=50, blank=True, null=True)

    mother_name = models.CharField(max_length=255, blank=True, null=True)
    mother_attainment = models.CharField(max_length=255, blank=True, null=True)
    mother_occupation = models.CharField(max_length=255, blank=True, null=True)
    mother_office_name = models.CharField(max_length=255, blank=True, null=True)
    mother_office_number = models.CharField(max_length=50, blank=True, null=True)
    mother_office_address = models.CharField(max_length=255, blank=True, null=True)
    mother_contact = models.CharField(max_length=50, blank=True, null=True)
    
    # UPDATED FIELDS
    status = models.CharField(max_length=20, choices=[('OLD', 'Old'), ('NEW', 'New'), ('TRANSFEREE', 'Transferee')], default='NEW')
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)
    parent_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    is_beadle = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    @property
    def unserved_cs_hours(self):
        demerits = self.disciplinary_records.aggregate(total=models.Sum('demerits'))['total'] or 0
        served = self.community_service_records.aggregate(total=models.Sum('hours_served'))['total'] or 0
        return demerits - served

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.student_number})"

class Enrollment(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT)
    is_enrolled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'school_year')

class DisciplinaryRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='disciplinary_records')
    category = models.CharField(max_length=20) 
    date_of_incident = models.DateField()
    
    # POPUP FIELDS
    time_of_incident = models.TimeField(null=True, blank=True)
    offense_name = models.CharField(max_length=255, null=True, blank=True)
    demerits = models.IntegerField(default=0)
    is_excused = models.BooleanField(default=False)
    sanction = models.CharField(max_length=255, blank=True, null=True)
    is_served = models.BooleanField(default=False)
    record_count = models.IntegerField(default=1)
    
    remarks = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, null=True)

class CommunityServiceRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='community_service_records')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT)
    date_served = models.DateField()
    hours_served = models.IntegerField()
    remarks = models.TextField(blank=True)


class DailyAttendance(TimeStampedModel):
    date = models.DateField(default=timezone.now)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('date', 'section')
        
    def __str__(self):
        return f"{self.section.name} - {self.date}"

class PeriodAttendance(TimeStampedModel):
    PERIOD_CHOICES =[(1, "1st Period"), (2, "2nd Period"), (3, "3rd Period"), 
                      (4, "4th Period"), (5, "5th Period"), (6, "6th Period"), (7, "7th Period")]
    
    daily_attendance = models.ForeignKey(DailyAttendance, related_name='periods', on_delete=models.CASCADE)
    period_number = models.IntegerField(choices=PERIOD_CHOICES)
    is_locked = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, help_text="Beadle who submitted")
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('daily_attendance', 'period_number')

class StudentPeriodRecord(TimeStampedModel):
    CODE_CHOICES =[
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('UU', 'Unprescribed Uniform'),
        ('UH', 'Unprescribed Haircut'),
        ('ID', 'No ID'),
        ('CL', 'Campus Leave')
    ]
    
    period = models.ForeignKey(PeriodAttendance, related_name='records', on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    code = models.CharField(max_length=2, choices=CODE_CHOICES, default='P')
    
    # --- ADD THESE TWO LINES ---
    original_code = models.CharField(max_length=50, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

class AttendanceAuditLog(TimeStampedModel):
    """ The 'Digital Correction Tape' to prevent cheating """
    record = models.ForeignKey(StudentPeriodRecord, related_name='audit_logs', on_delete=models.CASCADE)
    old_code = models.CharField(max_length=2)
    new_code = models.CharField(max_length=2)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
class ExcuseLetter(TimeStampedModel):
    # Changed from AttendanceRecord to DailyAttendance (excuses the whole day)
    daily_attendance = models.ForeignKey(DailyAttendance, on_delete=models.CASCADE, related_name='excuse_letters', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True)
    letter_image = models.ImageField(upload_to='excuse_letters/')
    status = models.CharField(max_length=15, default='PENDING')

@receiver(post_save, sender=Student)
def create_student_login(sender, instance, created, **kwargs):
    if created and not instance.user:
        u = User.objects.create_user(username=instance.student_number, password=instance.student_number)
        u.is_staff = False
        u.save()
        instance.user = u
        instance.save()