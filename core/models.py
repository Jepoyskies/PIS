from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum

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

class AttendanceBatch(TimeStampedModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    date = models.DateField()
    submitted_by = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)

class AttendanceRecord(TimeStampedModel):
    batch = models.ForeignKey(AttendanceBatch, on_delete=models.CASCADE, related_name='records', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, default='PRESENT')
    is_excused = models.BooleanField(default=False)

class ExcuseLetter(TimeStampedModel):
    attendance_record = models.OneToOneField(AttendanceRecord, on_delete=models.CASCADE, related_name='excuse_letter')
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