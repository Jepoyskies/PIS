from django.db import transaction
from .models import DisciplinaryRecord, Offense, SchoolYear, StudentPeriodRecord


def sync_student_attendance_logs(student, daily_attendance, staff_user):
    """
    Intelligently maps a student's period absences and violations to the best official Offense.
    """
    with transaction.atomic():
        # 1. Clear existing auto-generated logs for this student on this day to prevent duplicates
        DisciplinaryRecord.objects.filter(
            student=student,
            date_of_incident=daily_attendance.date,
            remarks__startswith="Auto-generated from Beadle Attendance"
        ).delete()

        # 2. Get all approved period records for this student today where they were NOT present
        records = list(StudentPeriodRecord.objects.filter(
            student=student,
            period__daily_attendance=daily_attendance,
            period__is_approved=True
        ).exclude(code='P').select_related('period'))

        if not records:
            return

        offenses_to_log = []

        # --- PROCESS ABSENCES ---
        absent_periods = [r.period.period_number for r in records if r.code == 'A']
        if absent_periods:
            absent_set = set(absent_periods)
            all_day = {1, 2, 3, 4, 5, 6, 7}
            morning = {1, 2, 3, 4}
            afternoon = {5, 6, 7}

            if all_day.issubset(absent_set):
                offenses_to_log.append("WD")
            elif morning.issubset(absent_set):
                offenses_to_log.append("AWM")
            elif afternoon.issubset(absent_set):
                offenses_to_log.append("AWA")
            else:
                for p in [1, 2, 3, 4]:
                    if p in absent_set:
                        offenses_to_log.append(f"AM{p}")
                for p in [5, 6, 7]:
                    if p in absent_set:
                        offenses_to_log.append(f"PM{p}")

        # --- PROCESS OTHER VIOLATIONS (L, UU, UH, ID, CL) ---
        other_records = [r for r in records if r.code != 'A']

        # Use a dictionary to prevent duplicates (e.g. only one 'UU' or 'ID' penalty per day)
        unique_other_codes = {}
        for r in other_records:
            code = r.code
            if code == 'L':
                final_code = 'L' if r.period.period_number == 1 else 'LC'
                unique_other_codes[final_code] = True
            else:
                unique_other_codes[code] = True

        for code in unique_other_codes.keys():
            offenses_to_log.append(code)

        # 3. Save to Database with FALLBACKS (Guarantees data is saved!)
        active_sy = SchoolYear.objects.filter(is_active=True).first()

        fallbacks = {
            'WD': ('Absent - Whole Day', 15, '1 Hr CS', 'Absences'),
            'AWM': ('Absent - Whole Morning', 8, 'Warning', 'Absences'),
            'AWA': ('Absent - Whole Afternoon', 8, 'Warning', 'Absences'),
            'AM1': ('Absent - 1st Period', 3, 'Warning', 'Absences'),
            'PM5': ('Absent - 5th Period', 3, 'Warning', 'Absences'),
            'L': ('Late for Flag Ceremony / Homeroom', 3, 'Warning', 'Tardiness'),
            'LC': ('Late for Class', 2, 'Warning', 'Tardiness'),
            'UU': ('Unprescribed Uniform', 5, 'Warning', 'Conduct'),
            'UH': ('Unprescribed Haircut', 5, 'Warning', 'Conduct'),
            'ID': ('No ID Card', 3, 'Warning', 'Conduct'),
            'CL': ('Campus Leave without Permit', 15, '1 Hr CS', 'Conduct'),
        }

        for o_code in offenses_to_log:
            official_offense = Offense.objects.filter(code=o_code).first()

            # Use official offense if found, else use our fallback, else use a generic name
            if official_offense:
                category = official_offense.offense_type or "ATTENDANCE"
                name = official_offense.name
                demerits = official_offense.default_demerits
                sanction = official_offense.default_sanction
            else:
                fallback = fallbacks.get(o_code, (f'Violation ({o_code})', 1, 'Warning', 'Conduct'))
                name, demerits, sanction, category = fallback

            DisciplinaryRecord.objects.create(
                student=student,
                category=category,
                offense_name=name,
                date_of_incident=daily_attendance.date,
                demerits=demerits,
                sanction=sanction,
                recorded_by=staff_user,
                school_year=active_sy,
                remarks="Auto-generated from Beadle Attendance",
                record_count=1
            )
