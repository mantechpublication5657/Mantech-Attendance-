# payroll/models.py

from django.db import models
from django.conf import settings
from datetime import timedelta
from decimal import Decimal
from datetime import date, timedelta
from attendance.models import Attendance
import calendar

import calendar
from datetime import date, timedelta
from decimal import Decimal



class Payroll(models.Model):

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payrolls"
    )

    month = models.PositiveIntegerField()   # 1–12
    year  = models.PositiveIntegerField()

    # =========================================
    # SALARY COMPONENTS
    # =========================================

    gross_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # Store HRA & DA as percentage rates (e.g. 40 means 40%)
    hra_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        help_text="HRA percentage of basic salary (e.g. 40 for 40%)"
    )

    da_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60,
        help_text="DA percentage of basic salary (e.g. 60 for 60%)"
    )

    # Stored full-month component values (for reference)
    hra = models.DecimalField(
        verbose_name="HRA",
        max_digits=10,
        decimal_places=2,
        default=0
    )

    
    da = models.DecimalField(
        verbose_name="SA",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    bonus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    bonus_remark = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    deduction_remark = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    net_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False
    )

    # =========================================
    # EARNED SALARY COMPONENTS
    # =========================================

    earned_basic_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    earned_hra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    earned_da = models.DecimalField(
        verbose_name="Earned SA",
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================================
    # META
    # =========================================

    class Meta:
        unique_together = ("employee", "month", "year")

    # =========================================
    # STRING
    # =========================================

    def __str__(self):
        return (
            f"{self.employee.username} "
            f"- {self.month}/{self.year}"
        )

    # =========================================
    # HELPERS
    # =========================================

    def _get_second_saturday(self, year, month, total_month_days):
        """Return the date of the 2nd Saturday of the given month, or None."""
        saturday_count = 0
        for day in range(1, total_month_days + 1):
            current_date = date(year, month, day)
            if current_date.weekday() == 5:   # Saturday = 5
                saturday_count += 1
                if saturday_count == 2:
                    return current_date
        return None

    def _get_total_sundays(self, year, month, total_month_days):
        """Return count of Sundays in the given month."""
        return sum(
            1
            for day in range(1, total_month_days + 1)
            if date(year, month, day).weekday() == 6
        )

    # =========================================
    # MAIN CALCULATION  (does NOT call save)
    # =========================================

    def calculate_salary(self):
        """
        Calculate earned salary based on attendance.

        Returns net_salary (Decimal) WITHOUT saving.
        The caller is responsible for calling .save() afterward
        to avoid unintended side effects or signal loops.

        Salary structure assumption:
            gross_salary  = basic_salary + hra + da
            hra           = basic_salary * (hra_rate / 100)
            da            = basic_salary * (da_rate  / 100)

        Per-day rate is based on total calendar days of the month.
        """

        # ------------------------------------------
        # GUARD: basic_salary must be set
        # ------------------------------------------
        if not self.basic_salary or self.basic_salary <= 0:
            self.earned_basic_salary = Decimal("0.00")
            self.earned_hra          = Decimal("0.00")
            self.earned_da           = Decimal("0.00")
            self.net_salary          = Decimal("0.00")
            return self.net_salary

        # ------------------------------------------
        # STEP 0: Calendar setup
        # ------------------------------------------
        total_month_days = calendar.monthrange(self.year, self.month)[1]
        second_saturday  = self._get_second_saturday(
            self.year, self.month, total_month_days
        )

        # ------------------------------------------
        # STEP 1: Per-day & half-day rates
        #         Based on total calendar days (e.g. 31 for May)
        # ------------------------------------------
        per_day_salary  = self.gross_salary / Decimal(total_month_days)
        half_day_salary = per_day_salary / Decimal("2")

        # ------------------------------------------
        # STEP 2: Fetch attendance records for the month
        # ------------------------------------------
        attendances = Attendance.objects.filter(
            employee=self.employee,
            date__year=self.year,
            date__month=self.month,
        )

        # ------------------------------------------
        # STEP 3: Payable full days
        #   Present, Late, Leave → full pay
        #   Exclude Sundays (week_day=1 in Django ORM → Sunday)
        # ------------------------------------------
        payable_days = attendances.filter(
            status__in=["Present", "Late", "Leave"]
        ).exclude(date__week_day=1).count()

        # ------------------------------------------
        # STEP 4: Half-day earnings
        #   2nd Saturday Half Day → full day pay (company policy)
        #   Any other Half Day    → half day pay
        #   Exclude Sundays
        # ------------------------------------------
        half_day_records = attendances.filter(
            status="Half Day"
        ).exclude(date__week_day=1)

        half_day_earned = Decimal("0.00")
        for record in half_day_records:
            if second_saturday and record.date == second_saturday:
                half_day_earned += per_day_salary   # 2nd Sat Half Day → full pay
            else:
                half_day_earned += half_day_salary  # Normal Half Day  → half pay

        # ------------------------------------------
        # STEP 5: Initial earned basic salary
        # ------------------------------------------
        earned_basic = (
            per_day_salary * Decimal(payable_days)
            + half_day_earned
        )

        # ------------------------------------------
        # STEP 6: 2nd Saturday rules
        #   Default: paid holiday (no record → no deduction)
        #   Absent  → deduct one full day
        #   Half Day, Leave, Present, Late → already handled above
        # ------------------------------------------
        second_sat_deduction = Decimal("0.00")
        if second_saturday:
            second_sat_record = attendances.filter(date=second_saturday).first()

            if second_sat_record is None:
                # Holiday — no record → full pay, nothing to deduct
                pass

            elif second_sat_record.status == "Absent":
                # Explicitly marked Absent → deduct one full day
                second_sat_deduction += per_day_salary

            # Half Day  → handled in Step 4 as full pay
            # Leave     → handled in Step 3 as payable day
            # Present / Late → handled in Step 3 as payable day

        # ------------------------------------------
        # STEP 7: Sunday rules
        #   Sunday is paid UNLESS both adjacent Saturday AND Monday are Absent.
        #   Paid Sunday  → add per_day_salary to earned_basic
        #   Unpaid Sunday → track in sunday_cut
        # ------------------------------------------
        sunday_cut = Decimal("0.00")

        sunday_records = attendances.filter(date__week_day=1)  # Django: 1 = Sunday
        for sunday_record in sunday_records:
            prev_saturday = sunday_record.date - timedelta(days=1)
            next_monday   = sunday_record.date + timedelta(days=1)

            sat_absent = attendances.filter(
                date=prev_saturday, status="Absent"
            ).exists()
            mon_absent = attendances.filter(
                date=next_monday, status="Absent"
            ).exists()

            if sat_absent and mon_absent:
                sunday_cut += per_day_salary           # Unpaid Sunday
            else:
                earned_basic += per_day_salary         # Paid Sunday → add to earned

        # ------------------------------------------
        # STEP 8: Earned HRA & DA
        #   BUG FIX 1: Use employee-specific rates from hra_rate / da_rate fields
        #   BUG FIX 2: HRA = 40%, DA = 60% (was swapped in original code)
        # ------------------------------------------
        hra_multiplier = self.hra_rate / Decimal("100")
        da_multiplier  = self.da_rate  / Decimal("100")

        earned_hra = earned_basic * hra_multiplier   # e.g. 40% of earned basic
        earned_da  = earned_basic * da_multiplier    # e.g. 60% of earned basic

        # ------------------------------------------
        # STEP 9: Final net salary
        #   earned_basic already reflects only days worked,
        #   so NO separate absence_deduction is needed.
        #   Deduct: second_sat_deduction, sunday_cut, other deductions.
        # ------------------------------------------
        final_salary = (
            earned_basic
            + earned_hra
            + earned_da
            + self.bonus
            - second_sat_deduction
            - sunday_cut
            - self.deductions
        )

        # Floor at zero — salary can never be negative
        if final_salary < Decimal("0.00"):
            final_salary = Decimal("0.00")

        # ------------------------------------------
        # STEP 10: Persist computed values to instance
        #   BUG FIX 3: Do NOT call self.save() here.
        #   Caller must call payroll.calculate_salary() then payroll.save().
        # ------------------------------------------
        self.earned_basic_salary = earned_basic.quantize(Decimal("0.01"))
        self.earned_hra          = earned_hra.quantize(Decimal("0.01"))
        self.earned_da           = earned_da.quantize(Decimal("0.01"))
        self.net_salary          = final_salary.quantize(Decimal("0.01"))

        # Also update full-month hra/da reference fields
        self.hra = (self.basic_salary * hra_multiplier).quantize(Decimal("0.01"))
        self.da  = (self.basic_salary * da_multiplier).quantize(Decimal("0.01"))

        return self.net_salary

# class Payroll(models.Model):

#     employee = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="payrolls"
#     )

#     month = models.PositiveIntegerField()   # 1–12
#     year = models.PositiveIntegerField()

#     # =========================================
#     # SALARY COMPONENTS
#     # =========================================

#     gross_salary = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0
#     )
    
#     basic_salary = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0
#     )

#     hra = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0
#     )

#     da = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0
#     )

#     bonus = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0
#     )

#     deductions = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0
#     )

#     net_salary = models.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         default=0,
#         editable=False
#     )
    
#     # =========================================
#     # EARNED SALARY COMPONENTS
#     # =========================================
    
#     earned_basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     earned_hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     earned_da = models.DecimalField(max_digits=10, decimal_places=2, default=0)

#     created_at = models.DateTimeField(
#         auto_now_add=True
#     )

#     updated_at = models.DateTimeField(
#         auto_now=True
#     )

#     # =========================================
#     # META
#     # =========================================

#     class Meta:
#         unique_together = ("employee", "month", "year")

#     # =========================================
#     # STRING
#     # =========================================

#     def __str__(self):

#         return (
#             f"{self.employee.username} "
#             f"- {self.month}/{self.year}"
#         )



#     def calculate_salary(self):
#         # -------------------------------------
#         # TOTAL DAYS IN MONTH
#         # -------------------------------------
#         total_month_days = calendar.monthrange(self.year, self.month)[1]

#         # -------------------------------------
#         # COUNT TOTAL SUNDAYS & 2ND SATURDAY
#         # -------------------------------------
#         total_sundays   = 0
#         second_saturday = None
#         saturday_count  = 0

#         for day in range(1, total_month_days + 1):
#             current_date = date(self.year, self.month, day)

#             if current_date.weekday() == 6:  # Sunday
#                 total_sundays += 1

#             if current_date.weekday() == 5:  # Saturday
#                 saturday_count += 1
#                 if saturday_count == 2:
#                     second_saturday = current_date

#         # -------------------------------------
#         # PER DAY & HALF DAY SALARY
#         # -------------------------------------
#         per_day_salary  = self.basic_salary / Decimal(total_month_days)
#         half_day_salary = per_day_salary / Decimal("2")

#         # -------------------------------------
#         # ATTENDANCE RECORDS
#         # -------------------------------------
#         attendances = Attendance.objects.filter(
#             employee=self.employee,
#             date__year=self.year,
#             date__month=self.month,
#         )

#         # -------------------------------------
#         # STEP 1: PAYABLE DAYS
#         # Present + Late + Leave (fully paid) — exclude Sundays
#         # -------------------------------------
#         payable_days = attendances.filter(
#             status__in=["Present", "Late", "Leave"]
#         ).exclude(date__week_day=1).count()

#         # -------------------------------------
#         # STEP 2: HALF DAYS
#         # Each half day = 0.5 pay — exclude Sundays
#         # 2nd Saturday half day → treated as full day (handled below)
#         # -------------------------------------
#         half_day_records = attendances.filter(
#             status="Half Day"
#         ).exclude(date__week_day=1)

#         half_day_earned = Decimal("0.00")
#         for record in half_day_records:
#             if second_saturday and record.date == second_saturday:
#                 half_day_earned += per_day_salary   # 2nd Saturday Half Day → full pay
#             else:
#                 half_day_earned += half_day_salary  # normal half day → half pay

#         # -------------------------------------
#         # STEP 3: EARNED BASIC SALARY
#         # -------------------------------------
#         earned_basic_salary = (
#             per_day_salary * Decimal(payable_days)
#             + half_day_earned
#         )

#         # -------------------------------------
#         # STEP 4: ABSENT DEDUCTION
#         # Exclude Sundays and 2nd Saturday (both handled separately)
#         # -------------------------------------
#         absent_records = attendances.filter(
#             status="Absent"
#         ).exclude(date__week_day=1)

#         absence_deduction = Decimal("0.00")
#         for record in absent_records:
#             if second_saturday and record.date == second_saturday:
#                 continue  # handled in Step 5
#             absence_deduction += per_day_salary

#         # -------------------------------------
#         # STEP 5: 2ND SATURDAY RULES
#         # 2nd Saturday is a paid holiday by default.
#         # Only deduct if explicitly marked Absent.
#         # No record = holiday = full pay (do NOT deduct).
#         # -------------------------------------
#         if second_saturday:
#             second_sat_record = attendances.filter(date=second_saturday).first()

#             if second_sat_record is None:
#                 # No record → it's a normal day holiday
#                 pass

#             elif second_sat_record.status == "Absent":
#                 # Explicitly marked Absent → deduct one full day
#                 absence_deduction += per_day_salary

#             elif second_sat_record.status == "Half Day":
#                 # Already handled as full pay in Step 2 — nothing more to do
#                 pass

#             elif second_sat_record.status == "Leave":
#                 # Leave → full pay, already in payable_days Step 1
#                 pass

#             # Present / Late → already in payable_days Step 1

#         # -------------------------------------
#         # STEP 6: SUNDAY RULE
#         # Deduct Sunday only if BOTH adjacent Sat AND Mon are absent
#         # Otherwise Sunday is paid → add to earned
#         # -------------------------------------
#         sunday_cut = Decimal("0.00")

#         for sunday_record in attendances.filter(date__week_day=1):
#             saturday = sunday_record.date - timedelta(days=1)
#             monday   = sunday_record.date + timedelta(days=1)

#             sat_absent = attendances.filter(date=saturday, status="Absent").exists()
#             mon_absent = attendances.filter(date=monday,   status="Absent").exists()

#             if sat_absent and mon_absent:
#                 sunday_cut += per_day_salary          # unpaid Sunday
#             else:
#                 earned_basic_salary += per_day_salary # paid Sunday

#         # -------------------------------------
#         # STEP 7: FINAL SALARY
#         # -------------------------------------
#         # final_salary = (
#         #     earned_basic_salary
#         #     + self.hra
#         #     + self.da
#         #     + self.bonus
#         #     # - absence_deduction
#         #     - self.deductions
#         #     - sunday_cut
#         # )
        
#         self.earned_basic_salary = earned_basic_salary
#         self.earned_hra = earned_basic_salary * Decimal("0.60")
#         self.earned_da = earned_basic_salary * Decimal("0.40")
        
#         final_salary = (
#             earned_basic_salary
#             + self.earned_hra
#             + self.earned_da
#             + self.bonus
#             - self.deductions
#             - sunday_cut
#         )

#         if final_salary < Decimal("0.00"):
#             final_salary = Decimal("0.00")

#         self.net_salary = final_salary.quantize(Decimal("0.01"))
#         self.save()
#         return self.net_salary