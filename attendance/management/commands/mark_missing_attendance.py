from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from attendance.models import Attendance, AttendanceLog
from employees.models import EmployeeProfile


class Command(BaseCommand):
    help = "Mark all missing attendance records as Absent for all employees"

    def add_arguments(self, parser):
        # OPTIONAL: pass month and year as arguments
        # if not passed, defaults to previous month
        parser.add_argument(
            "--month",
            type=int,
            help="Month to process (1-12)"
        )
        parser.add_argument(
            "--year",
            type=int,
            help="Year to process (e.g. 2026)"
        )

    def handle(self, *args, **kwargs):

        today = timezone.localdate()

        month = kwargs.get("month")
        year = kwargs.get("year")

        # DEFAULT TO PREVIOUS MONTH IF NOT PROVIDED
        if not month or not year:
            if today.month == 1:
                month = 12
                year = today.year - 1
            else:
                month = today.month - 1
                year = today.year

        # START AND END DATE OF SELECTED MONTH
        start_date = date(year, month, 1)

        if month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # DO NOT PROCESS FUTURE DATES
        if start_date > today:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping - {month}/{year} is in the future."
                )
            )
            return

        # IF SELECTED MONTH IS CURRENT MONTH -> TILL YESTERDAY
        if month == today.month and year == today.year:
            end_date = today - timedelta(days=1)

        self.stdout.write(
            self.style.HTTP_INFO(
                f"\nProcessing attendance for {month}/{year} "
                f"({start_date} to {end_date})\n"
            )
        )

        employees = EmployeeProfile.objects.select_related(
            "user",
            "admin_data"
        ).all()

        total_marked = 0
        total_skipped = 0

        for profile in employees:

            # SKIP EMPLOYEES WITHOUT ADMIN DATA
            if not hasattr(profile, "admin_data"):
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped {profile.user.username} - no admin data"
                    )
                )
                total_skipped += 1
                continue

            # SKIP EMPLOYEES WITHOUT JOINING DATE
            if not profile.admin_data.joining_date:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped {profile.user.username} - no joining date"
                    )
                )
                total_skipped += 1
                continue

            joining_date = profile.admin_data.joining_date

            # SKIP FUTURE JOINING EMPLOYEES
            if joining_date > end_date:
                total_skipped += 1
                continue

            # START CHECKING FROM JOINING DATE OR MONTH START
            checking_start = max(joining_date, start_date)

            current_date = checking_start
            employee_marked = 0

            while current_date <= end_date:

                # SKIP SUNDAYS (UNCOMMENT IF NEEDED)
                if current_date.weekday() == 6:
                    current_date += timedelta(days=1)
                    continue

                # CHECK IF ATTENDANCE EXISTS
                attendance_exists = Attendance.objects.filter(
                    employee=profile.user,
                    date=current_date
                ).exists()

                if not attendance_exists:

                    # MARK AS ABSENT
                    Attendance.objects.create(
                        employee=profile.user,
                        date=current_date,
                        status="Absent",      # adjust to match your model's field value
                    )

                    AttendanceLog.objects.create(
                        employee=profile.user,
                        date=current_date,
                        action="Auto Absent",
                        notes="No check-in recorded - marked absent by mark_missing_attendance command.",
                    )

                    employee_marked += 1
                    total_marked += 1

                current_date += timedelta(days=1)

            if employee_marked > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[OK] {profile.user.username} - "
                        f"marked {employee_marked} days as Absent"
                    )
                )
            else:
                self.stdout.write(
                    f"  {profile.user.username} - no missing attendance"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone - Total Marked: {total_marked} | "
                f"Total Skipped: {total_skipped}\n"
            )
        )
        
        
# HOW TO RUN:
# Previous month (default)
# python manage.py mark_missing_attendance

# Specific month/year
# python manage.py mark_missing_attendance --month 5 --year 2026