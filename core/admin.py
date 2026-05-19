# core/admin.py
from django.contrib import admin
from .models import (
    SchoolYear, Student, Teacher, Section, Enrollment, 
    DisciplinaryRecord, ExcuseLetter, StaffProfile,
    DailyAttendance, PeriodAttendance, StudentPeriodRecord, AttendanceAuditLog, Offense
)

admin.site.register(SchoolYear)
admin.site.register(Teacher)
admin.site.register(Section)
admin.site.register(Student)
admin.site.register(Enrollment)
admin.site.register(DisciplinaryRecord)
admin.site.register(ExcuseLetter)
admin.site.register(Offense)

# NEW: Register the new Attendance models
admin.site.register(DailyAttendance)
admin.site.register(PeriodAttendance)
admin.site.register(StudentPeriodRecord)
admin.site.register(AttendanceAuditLog)

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department')