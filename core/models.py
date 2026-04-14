from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class SchoolYear(TimeStampedModel):
    code = models.CharField(max_length=9, unique=True)
    is_active = models.BooleanField(default=False)
    def __str__(self): return self.code

class Teacher(TimeStampedModel):
    prefix = models.CharField(max_length=10)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.prefix} {self.last_name}"

class Section(TimeStampedModel):
    grade_level = models.IntegerField()
    name = models.CharField(max_length=100)
    moderator = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    # RBAC Fix: Link the Beadle directly to the Section
    beadle = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='beadle_of')
    def __str__(self): return f"Gr {self.grade_level} - {self.name}"

# NEW: Staff Profile for non-admin Staff
class StaffProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, default="Prefect Office")
    def __str__(self): return self.user.username

class Student(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='student_profile')
    student_number = models.CharField(max_length=20, unique=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=10, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    parent_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    is_beadle = models.BooleanField(default=False) # Fallback boolean
    is_deleted = models.BooleanField(default=False)
    def __str__(self): return f"{self.last_name}, {self.first_name}"

class Enrollment(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT)
    is_enrolled = models.BooleanField(default=True)
    class Meta: unique_together = ('student', 'school_year')

class DisciplinaryRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='disciplinary_records')
    category = models.CharField(max_length=20) 
    date_of_incident = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    demerits = models.IntegerField(default=0)
    action_taken = models.CharField(max_length=255, blank=True, null=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, null=True)

# ---> NEW FEATURE INJECTED: AttendanceBatch for Workflow 3 & 4
class AttendanceBatch(TimeStampedModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    date = models.DateField()
    submitted_by = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)
    def __str__(self): return f"{self.section.name} - {self.date}"

class AttendanceRecord(TimeStampedModel):
    STATUS_CHOICES = [('PRESENT', 'Present'), ('ABSENT', 'Absent'), ('LATE', 'Late')]
    # Linked to Batch
    batch = models.ForeignKey(AttendanceBatch, on_delete=models.CASCADE, related_name='records', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    
    # Updated to a single status for simplicity in the UI
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT')
    is_excused = models.BooleanField(default=False)

class ExcuseLetter(TimeStampedModel):
    attendance_record = models.OneToOneField(AttendanceRecord, on_delete=models.CASCADE, related_name='excuse_letter')
    letter_image = models.ImageField(upload_to='excuse_letters/')
    status = models.CharField(max_length=15, default='PENDING') # PENDING, APPROVED, REJECTED

# ==========================================
# THE AUTO-ACCOUNT ENGINE (SIGNAL)
# ==========================================
@receiver(post_save, sender=Student)
def create_student_login(sender, instance, created, **kwargs):
    """ Whenever a student is created, automatically create a Django User """
    if created and not instance.user:
        username = instance.student_number
        password = instance.student_number
        new_user = User.objects.create_user(username=username, password=password)
        # Students are NOT staff
        new_user.is_staff = False
        new_user.save()
        
        instance.user = new_user
        instance.save()