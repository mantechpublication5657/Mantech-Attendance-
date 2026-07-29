from django.core.management.base import BaseCommand
from django.utils.timezone import localdate
from django.contrib.auth import get_user_model
from payroll.models import Payroll
from employees.models import EmployeeProfile

User = get_user_model()

class Command(BaseCommand):
    help = "Auto create payroll for all employees using previous month basic salary"

    def handle(self, *args, **kwargs):

        today = localdate()
        current_month = today.month
        current_year = today.year

        # PREVIOUS MONTH
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year

        employees = EmployeeProfile.objects.select_related("user").all()

        created_count = 0
        skipped_count = 0

        for profile in employees:

            user = profile.user

            # SKIP IF PAYROLL ALREADY EXISTS
            already_exists = Payroll.objects.filter(
                employee=user,
                month=current_month,
                year=current_year
            ).exists()

            if already_exists:
                skipped_count += 1
                continue

            # GET PREVIOUS MONTH BASIC SALARY
            previous_payroll = Payroll.objects.filter(
                employee=user,
                month=prev_month,
                year=prev_year
            ).first()

            if not previous_payroll:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipped {user.username} — no previous payroll found"
                    )
                )
                skipped_count += 1
                continue

            # CREATE NEW PAYROLL WITH PREVIOUS BASIC SALARY
            payroll = Payroll.objects.create(
                employee=user,
                month=current_month,
                year=current_year,
                basic_salary=previous_payroll.basic_salary,
                hra=0,
                da=0,
                bonus=0,
                deductions=0,
            )

            payroll.calculate_salary()

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created payroll for {user.username} — basic salary: {payroll.basic_salary}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — Created: {created_count} | Skipped: {skipped_count}"
            )
        )