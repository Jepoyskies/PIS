from django.db import transaction
from .models import DisciplinaryRecord, Offense, SchoolYear

def sync_student_attendance_logs(student, daily_attendance, staff_user):
    """
    Business logic for attendance log synchronization.
    Refactored out of views.py to reduce technical debt.
    """
    with transaction.atomic():
        # Clear existing logs for this day
        DisciplinaryRecord.objects.filter(
            student=student, 
            date_of_incident=daily_attendance.date,
            category="ATTENDANCE"
        ).delete()

        # ... (logic remains same as before)
        from .models import StudentPeriodRecord
        absent_periods = list(StudentPeriodRecord.objects.filter(
            student=student,
            period__daily_attendance=daily_attendance,
            period__is_approved=True,
            code='A'
        ).values_list('period__period_number', flat=True))

        if not absent_periods:
            return

        all_day = {1, 2, 3, 4, 5, 6, 7}
        morning = {1, 2, 3, 4}
        afternoon = {5, 6, 7}
        absent_set = set(absent_periods)
        offenses_to_log = []

        if all_day.issubset(absent_set):
            offenses_to_log.append("WD")
        else:
            if morning.issubset(absent_set):
                offenses_to_log.append("AWM")
            else:
                for p in [1, 2, 3, 4]:
                    if p in absent_set: offenses_to_log.append(f"AM{p}")
            if afternoon.issubset(absent_set):
                offenses_to_log.append("AWA")
            else:
                for p in [5, 6, 7]:
                    if p in absent_set: offenses_to_log.append(f"PM{p}")

        active_sy = SchoolYear.objects.filter(is_active=True).first()
        for code in offenses_to_log:
            official_offense = Offense.objects.filter(code=code).first()
            if official_offense:
                DisciplinaryRecord.objects.create(
                    student=student,
                    category="ATTENDANCE",
                    offense_name=official_offense.name,
                    date_of_incident=daily_attendance.date,
                    demerits=official_offense.default_demerits,
                    sanction=official_offense.default_sanction,
                    recorded_by=staff_user,
                    school_year=active_sy,
                    remarks="Auto-generated from Beadle Attendance"
                )
