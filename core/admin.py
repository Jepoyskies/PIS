# core/admin.py
from django.contrib import admin
from .models import SchoolYear, Student, Teacher, Section, Enrollment, DisciplinaryRecord, AttendanceRecord, ExcuseLetter, StaffProfile

admin.site.register(SchoolYear)
admin.site.register(Teacher)
admin.site.register(Section)
admin.site.register(Student)
admin.site.register(Enrollment)
admin.site.register(DisciplinaryRecord)
admin.site.register(AttendanceRecord)
admin.site.register(ExcuseLetter)

# NEW: Register StaffProfile so you can see it in the Django Admin page
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department')