# core/admin.py
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import (
    SchoolYear, Student, Teacher, Section, Enrollment, 
    DisciplinaryRecord, ExcuseLetter, StaffProfile,
    DailyAttendance, PeriodAttendance, StudentPeriodRecord, 
    AttendanceAuditLog, Offense, ExcuseLetterRequest
)

# ==========================================
# 1. DEFINE RESOURCES (How Excel columns map to your models)
# ==========================================

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        # The fields you want to import/export from the Excel file
        fields = ('id', 'student_number', 'last_name', 'first_name', 'middle_initial', 'sex', 'status', 'section')
        export_order = ('student_number', 'last_name', 'first_name', 'middle_initial', 'sex', 'section')
        import_id_fields = ['student_number'] # Prevents duplicates; updates existing students instead!

class TeacherResource(resources.ModelResource):
    class Meta:
        model = Teacher
        fields = ('id', 'prefix', 'first_name', 'last_name', 'is_active')

class SectionResource(resources.ModelResource):
    class Meta:
        model = Section
        fields = ('id', 'grade_level', 'name', 'moderator')

class OffenseResource(resources.ModelResource):
    class Meta:
        model = Offense
        fields = ('id', 'offense_type', 'code', 'name', 'default_demerits', 'default_sanction', 'classification')


# ==========================================
# 2. REGISTER MODELS WITH IMPORT/EXPORT BUTTONS
# ==========================================

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    list_display = ('student_number', 'last_name', 'first_name', 'section', 'is_beadle', 'is_deleted')
    search_fields = ('student_number', 'last_name', 'first_name')
    list_filter = ('status', 'sex', 'section')

@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    list_display = ('prefix', 'last_name', 'first_name', 'is_active')

@admin.register(Section)
class SectionAdmin(ImportExportModelAdmin):
    resource_class = SectionResource
    list_display = ('grade_level', 'name', 'moderator', 'beadle')
    list_filter = ('grade_level',)

@admin.register(Offense)
class OffenseAdmin(ImportExportModelAdmin):
    resource_class = OffenseResource
    list_display = ('code', 'name', 'offense_type', 'default_demerits', 'classification')
    search_fields = ('code', 'name')
    list_filter = ('offense_type', 'classification')


# ==========================================
# 3. REGISTER STANDARD ADMIN MODELS
# ==========================================

@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_active')

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department')

admin.site.register(Enrollment)
admin.site.register(DisciplinaryRecord)
admin.site.register(ExcuseLetter)
admin.site.register(DailyAttendance)
admin.site.register(PeriodAttendance)
admin.site.register(StudentPeriodRecord)
admin.site.register(AttendanceAuditLog)

# Register the new notification model so you can manage them in Admin!
@admin.register(ExcuseLetterRequest)
class ExcuseLetterRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'date_requested_for', 'is_resolved')
    list_filter = ('is_resolved', 'date_requested_for')
    search_fields = ('student__last_name', 'student__student_number')