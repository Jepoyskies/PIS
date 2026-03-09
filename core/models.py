# core/models.py
from django.db import models
from django.contrib.auth.models import User

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

# REGISTRAR DATA (Master Record)
class Student(TimeStampedModel):
    student_number = models.CharField(max_length=20, unique=True)
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=10, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')])
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    # We use a soft-delete boolean so we don't accidentally wipe historical records
    is_deleted = models.BooleanField(default=False)

    @property
    def unserved_cs_hours(self):
        demerits = self.disciplinary_records.aggregate(total=models.Sum('demerits'))['total'] or 0
        served = self.community_service_records.aggregate(total=models.Sum('hours_served'))['total'] or 0
        return demerits - served

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.student_number})"

# PREFECT/ENROLLMENT DATA (Relational)
class Enrollment(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    school_year = models.ForeignKey('SchoolYear', on_delete=models.RESTRICT)
    
    # NEW: Link the student to a specific section!
    section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True, related_name='enrolled_students')
    
    date_enrolled = models.DateField(null=True, blank=True)
    is_enrolled = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('student', 'school_year')

class DisciplinaryRecord(TimeStampedModel):
    CATEGORY_CHOICES = [
        ('ABSENCE', 'Absence'),
        ('TARDINESS', 'Tardiness'),
        ('CONDUCT', 'Conduct'),
        ('SUSPENSION', 'Suspension'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='disciplinary_records')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    date_of_incident = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    demerits = models.IntegerField(default=0)
    action_taken = models.CharField(max_length=255, blank=True, null=True)
    
    # Linked safely to Django's Auth system
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.student.last_name} ({self.date_of_incident})"

class CommunityServiceRecord(TimeStampedModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='community_service_records')
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT)
    date_served = models.DateField()
    hours_served = models.IntegerField()
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student.last_name} - {self.hours_served} hrs"

        # ==========================================
# REGISTRAR INFORMATION SYSTEM (RIS) MODELS
# ==========================================

class Teacher(TimeStampedModel):
    prefix = models.CharField(max_length=10, help_text="e.g., Mr., Ms., Bro., Fr.")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.prefix} {self.last_name}, {self.first_name}"

class Section(TimeStampedModel):
    GRADE_CHOICES = [(7, 'Grade 7'), (8, 'Grade 8'), (9, 'Grade 9'), (10, 'Grade 10')]
    
    grade_level = models.IntegerField(choices=GRADE_CHOICES)
    name = models.CharField(max_length=100, help_text="e.g., ST. ALOYSIUS GONZAGA")
    moderator = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_sections')
    campus = models.CharField(max_length=50, default="PUEBLO")

    def __str__(self):
        return f"Grade {self.grade_level} - {self.name}"

class Subject(TimeStampedModel):
    name = models.CharField(max_length=100)
    grade_level = models.IntegerField()

    def __str__(self):
        return f"{self.name} (Grade {self.grade_level})"

class TeacherLoad(TimeStampedModel):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teaching_loads')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_year = models.ForeignKey('SchoolYear', on_delete=models.RESTRICT)

    def __str__(self):
        return f"{self.teacher.last_name} - {self.subject.name} ({self.section.name})"