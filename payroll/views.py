# payroll/views.py
import profile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import Payroll
from .forms import PayrollForm   # you’ll need to create a ModelForm for Payroll
from employees.models import EmployeeProfile
from datetime import date
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date, timedelta
from django.utils.timezone import localdate

User = get_user_model()
def is_admin(user):
    return user.is_staff or user.is_superuser

from django.db.models import OuterRef, Subquery  # add this at the top of views.py

@user_passes_test(is_admin)
def payroll_dashboard(request, user_id):
    today = date.today()
    query = request.GET.get("q", "")
    current_month = int(request.GET.get("month", today.month))
    current_year = int(request.GET.get("year", today.year))

    if not request.user.is_authenticated:
        return redirect("login")

    # --- Employee list filtered by search (emp_id / username) ---
    employees_qs = EmployeeProfile.objects.select_related("user", "admin_data").all()

    if query:
        employees_qs = employees_qs.filter(
            Q(user__username__icontains=query) |
            Q(emp_id__icontains=query)
        )

    # --- Annotate each employee with whether they have a payroll for selected month/year ---
    payroll_subquery = Payroll.objects.filter(
        employee=OuterRef("user"),
        month=current_month,
        year=current_year
    ).values("id")[:1]

    employees_qs = employees_qs.annotate(
        has_payroll=Subquery(payroll_subquery)
    )

    # --- Paginate after annotation ---
    paginator = Paginator(employees_qs, 10)
    page_number = request.GET.get("page")
    employees = paginator.get_page(page_number)

    # --- Payroll filtered by month & year only ---
    if request.user.is_staff or request.user.is_superuser:
        payrolls = Payroll.objects.select_related("employee").filter(
            month=current_month,
            year=current_year
        )
    else:
        payrolls = Payroll.objects.filter(
            employee=request.user,
            month=current_month,
            year=current_year
        )

    context = {
        "user": request.user,
        "month": today.month,
        "year": today.year,
        "current_month": current_month,
        "current_year": current_year,
        "payrolls": payrolls,
        "employees": employees,
    }

    return render(request, "payroll/payroll_dashboard.html", context)


@user_passes_test(is_admin)
def add_payroll(request, user_id, month=None, year=None):

    today = localdate()
    current_month = month if month else today.month
    current_year = year if year else today.year

    selected_user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(EmployeeProfile, user=selected_user)

    # CHECK EXISTING PAYROLL
    payroll_exists = Payroll.objects.filter(
        employee=selected_user,
        month=current_month,
        year=current_year
    ).exists()

    if payroll_exists:
        messages.warning(request, "Payroll already exists for this month.")
        return redirect("payroll_detail", user_id=selected_user.id, month=current_month, year=current_year)

    # FETCH PREVIOUS MONTH'S PAYROLL
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    previous_payroll = Payroll.objects.filter(
        employee=selected_user,
        month=prev_month,
        year=prev_year
    ).first()

    # CARRY OVER GROSS SALARY
    carried_gross_salary = previous_payroll.gross_salary if previous_payroll else None
    carried_basic_salary = previous_payroll.basic_salary if previous_payroll else None
    carried_hra = previous_payroll.hra if previous_payroll else None
    carried_da = previous_payroll.da if previous_payroll else None

    if request.method == "POST":

        form = PayrollForm(request.POST)

        if form.is_valid():

            payroll = form.save(commit=False)

            payroll.employee = selected_user
            payroll.month = current_month
            payroll.year = current_year

            # IF ADMIN ENTERED A NEW GROSS SALARY USE IT
            # OTHERWISE CARRY OVER FROM PREVIOUS MONTH
            
            if not payroll.gross_salary:
                payroll.gross_salary = carried_gross_salary

            # AUTO CALCULATE HRA & DA
            if payroll.gross_salary:
                payroll.basic_salary = (payroll.gross_salary * 50) / 100
                payroll.hra = (payroll.gross_salary * 20) / 100
                payroll.da = (payroll.gross_salary * 30) / 100

            # SAVE TO DATABASE
            payroll.save()

            # CALCULATE SALARY
            payroll.calculate_salary()

            messages.success(request, "Payroll added successfully.")
            return redirect("payroll_detail", user_id=selected_user.id, month=current_month, year=current_year)

    else:

        # PRE-FILL GROSS SALARY FROM PREVIOUS MONTH
        form = PayrollForm(initial={"gross_salary": carried_gross_salary, "basic_salary": carried_basic_salary, "hra": carried_hra, "da": carried_da})

    context = {
        "employee": profile,
        "form": form,
        "month": current_month,
        "year": current_year,
        "carried_gross_salary": carried_gross_salary,   # for template 
        "carried_basic_salary": carried_basic_salary,   # for template
        "carried_hra": carried_hra,                     # for template  
        "carried_da": carried_da,                       # for template
    }

    return render(request, "payroll/payroll_add.html", context)    
    
# EDIT PAYROLL (Admin only)
# -------------------------------
@user_passes_test(is_admin)
def edit_payroll(request, user_id, month, year):

    user = get_object_or_404(
        User,
        id=user_id
    )

    profile = get_object_or_404(
        EmployeeProfile,
        user=user
    )

    payroll = get_object_or_404(
        Payroll,
        employee=user,
        month=month,
        year=year
    )

    # =====================================
    # UPDATE PAYROLL
    # =====================================

    if request.method == "POST":

        form = PayrollForm(
            request.POST,
            instance=payroll
        )

        if form.is_valid():

            updated_payroll = form.save(commit=False)

            # Keep original values
            updated_payroll.employee = user
            updated_payroll.month = month
            updated_payroll.year = year

            # Edit Gross Salary → auto-update Basic, HRA, DA
            if updated_payroll.gross_salary:
                updated_payroll.basic_salary = (updated_payroll.gross_salary * 50) / 100
                updated_payroll.hra = (updated_payroll.gross_salary * 20) / 100
                updated_payroll.da = (updated_payroll.gross_salary * 30) / 100


            # Save first
            updated_payroll.save()

            # Recalculate salary
            updated_payroll.calculate_salary()

            messages.success(
                request,
                "Payroll updated successfully."
            )

            return redirect(
                "payroll_detail",
                user_id=user.id,
                month=month,
                year=year
            )

    else:

        form = PayrollForm(
            instance=payroll
        )

    context = {
        "employee": profile,
        "form": form,
        "payroll": payroll,
    }

    return render(
        request,
        "payroll/payroll_edit.html",
        context
    )

# -------------------------------
# PAYROLL DETAIL (Admin only)
# -------------------------------


def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def payroll_detail(request, user_id, month, year):

    # =========================================
    # USER / PROFILE / PAYROLL
    # =========================================
    user    = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(EmployeeProfile, user=user)
    payroll = get_object_or_404(Payroll, employee=user, month=month, year=year)

    # =========================================
    # MONTH CALENDAR — TOTAL DAYS, SUNDAYS, 2ND SATURDAY
    # =========================================
    total_month_days = calendar.monthrange(int(year), int(month))[1]

    total_sundays   = 0
    second_saturday = None
    saturday_count  = 0

    for day in range(1, total_month_days + 1):
        current_date = date(int(year), int(month), day)
        if current_date.weekday() == 6:   # Sunday
            total_sundays += 1
        if current_date.weekday() == 5:   # Saturday
            saturday_count += 1
            if saturday_count == 2:
                second_saturday = current_date

    # =========================================
    # PER DAY SALARY  (based on GROSS salary)
    # gross_salary = basic + hra + da
    # =========================================
    gross_month = (
        payroll.basic_salary + payroll.hra + payroll.da
    )
    per_day_salary  = (gross_month / Decimal(total_month_days)).quantize(Decimal("0.01"))
    half_day_salary = (per_day_salary / Decimal("2")).quantize(Decimal("0.01"))

    # =========================================
    # ATTENDANCE RECORDS FOR THIS MONTH
    # =========================================
    attendances = Attendance.objects.filter(
        employee=user,
        date__year=year,
        date__month=month,
    )

    # =========================================
    # ATTENDANCE SUMMARY COUNTS
    # =========================================
    present_days  = attendances.filter(status="Present").count()
    absent_days   = attendances.filter(status="Absent").count()
    late_days     = attendances.filter(status="Late").count()
    leave_days    = attendances.filter(status="Leave").count()
    half_day_days = attendances.filter(status="Half Day").count()

    # =========================================
    # PAYABLE DAYS & ATTENDANCE DEDUCTION
    # =========================================

    # --- Base payable days: Present + Late + Leave (full pay) ---
    payable_days = Decimal(present_days + late_days + leave_days)

    # --- Half Day processing ---
    # Normal half day  → 0.5 payable, deduct 0.5 day salary
    # 2nd Sat half day → 1.0 payable (full pay), no deduction
    half_day_earned     = Decimal("0.00")
    half_day_deduction  = Decimal("0.00")

    for record in attendances.filter(status="Half Day").exclude(date__week_day=1):
        if second_saturday and record.date == second_saturday:
            payable_days    += Decimal("1")          # full pay
            half_day_earned += per_day_salary
        else:
            payable_days    += Decimal("0.5")        # half pay
            half_day_earned += half_day_salary
            half_day_deduction += half_day_salary    # deduction for display

    # --- Sunday rule: paid unless both adjacent Sat & Mon are absent ---
    sunday_cut = Decimal("0.00")

    for sunday_record in attendances.filter(date__week_day=1):
        prev_saturday = sunday_record.date - timedelta(days=1)
        next_monday   = sunday_record.date + timedelta(days=1)

        sat_absent = attendances.filter(date=prev_saturday, status="Absent").exists()
        mon_absent = attendances.filter(date=next_monday,   status="Absent").exists()

        if sat_absent and mon_absent:
            sunday_cut += per_day_salary             # unpaid Sunday
        else:
            payable_days += Decimal("1")             # paid Sunday

    # --- 2nd Saturday rule ---
    # Default: paid holiday → no deduction
    # Only deduct if explicitly marked Absent
    second_sat_deduction = Decimal("0.00")
    if second_saturday:
        second_sat_record = attendances.filter(date=second_saturday).first()
        if second_sat_record and second_sat_record.status == "Absent":
            second_sat_deduction = per_day_salary    # explicitly absent

    # --- Absent day deductions (excluding 2nd Saturday — handled above) ---
    absent_deduction = Decimal("0.00")
    for record in attendances.filter(status="Absent").exclude(date__week_day=1):
        if second_saturday and record.date == second_saturday:
            continue   # already handled in second_sat_deduction
        absent_deduction += per_day_salary

    # --- Total attendance deduction ---
    attendance_deduction = (
        absent_deduction
        + half_day_deduction
        + sunday_cut
        + second_sat_deduction
    ).quantize(Decimal("0.01"))

    # --- Total deduction (attendance + admin) ---
    total_deduction = (
        attendance_deduction + payroll.deductions
    ).quantize(Decimal("0.01"))

    # =========================================
    # EARNED SALARY COMPONENTS
    # (recalculate here so view is self-contained)
    # =========================================
    hra_rate = payroll.hra_rate / Decimal("100")   # e.g. 0.40
    da_rate  = payroll.da_rate  / Decimal("100")   # e.g. 0.60

    # Earned gross = per_day_salary * payable_days (already includes paid Sundays)
    earned_gross = (per_day_salary * payable_days - sunday_cut - second_sat_deduction)

    # Split earned gross back to components using the ratio
    divisor              = Decimal("1") + hra_rate + da_rate
    earned_basic_salary  = (earned_gross / divisor).quantize(Decimal("0.01"))
    earned_hra           = (earned_basic_salary * hra_rate).quantize(Decimal("0.01"))
    earned_da            = (earned_basic_salary * da_rate).quantize(Decimal("0.01"))

    # =========================================
    # NET SALARY
    # =========================================
    net_salary = (
        earned_gross
        + payroll.bonus
        - payroll.deductions
    ).quantize(Decimal("0.01"))

    if net_salary < Decimal("0.00"):
        net_salary = Decimal("0.00")

    # =========================================
    # SAVE UPDATED VALUES TO PAYROLL
    # =========================================
    payroll.earned_basic_salary = earned_basic_salary
    payroll.earned_hra          = earned_hra
    payroll.earned_da           = earned_da
    payroll.net_salary          = net_salary
    payroll.save()

    # =========================================
    # CUT DAYS (for display)
    # =========================================
    cut_days = (
        Decimal(absent_days)
        + (half_day_deduction / per_day_salary if per_day_salary else Decimal("0"))
    ).quantize(Decimal("0.01"))

    # =========================================
    # CONTEXT
    # =========================================
    context = {
        # Employee
        "employee": profile,
        "payroll":  payroll,

        # Attendance Summary
        "present_days":  present_days,
        "absent_days":   absent_days,
        "late_days":     late_days,
        "leave_days":    leave_days,
        "half_day_days": half_day_days,

        # Calendar Info
        "total_month_days": total_month_days,
        "total_sundays":    total_sundays,
        "second_saturday":  second_saturday,

        # Salary Breakdown
        "per_day_salary":  per_day_salary,
        "half_day_salary": half_day_salary,
        "payable_days":    payable_days,
        "cut_days":        cut_days,

        # Earned Components
        "earned_basic_salary": earned_basic_salary,
        "earned_hra":          earned_hra,
        "earned_da":           earned_da,

        # Deductions
        "attendance_deduction": attendance_deduction,
        "absent_deduction":     absent_deduction.quantize(Decimal("0.01")),
        "half_day_deduction":   half_day_deduction.quantize(Decimal("0.01")),
        "sunday_cut":           sunday_cut.quantize(Decimal("0.01")),
        "admin_deduction":      payroll.deductions,
        "total_deduction":      total_deduction,

        # Totals
        "gross_salary": gross_month.quantize(Decimal("0.01")),
        "net_salary":   net_salary,
    }

    return render(request, "payroll/payroll_detail.html", context)

# =========================================================
# views.py
# =========================================================

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from payroll.models import Payroll

from .salary_slip_report import (
    generate_salary_slip,
    salary_slip_response,
)


def is_admin(user):
    return user.is_staff


# =========================================================
# DOWNLOAD SALARY SLIP VIEW
# =========================================================

import calendar

from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test

from accounts.models import User
from employees.models import EmployeeProfile
from attendance.models import Attendance
from payroll.models import Payroll

from .salary_slip_report import (
    generate_salary_slip,
    salary_slip_response
)


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user):
    return user.is_staff


# =========================================================
# DOWNLOAD SALARY SLIP
# =========================================================

from .salary_slip_report import (
    generate_salary_slip,
    salary_slip_response
)


@login_required
def download_salary_slip(request, user_id, month, year):

    # =====================================================
    # USER / PROFILE / PAYROLL
    # =====================================================
    user    = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(EmployeeProfile, user=user)
    payroll = get_object_or_404(Payroll, employee=user, month=month, year=year)

    # =====================================================
    # MONTH CALENDAR — TOTAL DAYS, SUNDAYS, 2ND SATURDAY
    # =====================================================
    total_month_days = calendar.monthrange(int(year), int(month))[1]

    second_saturday = None
    saturday_count  = 0

    for day in range(1, total_month_days + 1):
        current_date = date(int(year), int(month), day)
        if current_date.weekday() == 5:   # Saturday
            saturday_count += 1
            if saturday_count == 2:
                second_saturday = current_date
                break

    # =====================================================
    # PER DAY SALARY  (based on GROSS — basic + hra + da)
    # Matches payroll_detail exactly
    # =====================================================
    gross_month = (
        payroll.basic_salary + payroll.hra + payroll.da
    )
    per_day_salary  = (gross_month / Decimal(total_month_days)).quantize(Decimal("0.01"))
    half_day_salary = (per_day_salary / Decimal("2")).quantize(Decimal("0.01"))

    # =====================================================
    # ATTENDANCE RECORDS
    # =====================================================
    attendances = Attendance.objects.filter(
        employee=user,
        date__year=year,
        date__month=month,
    )

    # =====================================================
    # ATTENDANCE SUMMARY COUNTS
    # =====================================================
    present_days  = attendances.filter(status="Present").count()
    absent_days   = attendances.filter(status="Absent").count()
    late_days     = attendances.filter(status="Late").count()
    leave_days    = attendances.filter(status="Leave").count()
    half_day_days = attendances.filter(status="Half Day").count()

    # =====================================================
    # PAYABLE DAYS & DEDUCTION BREAKDOWN
    # Mirrors payroll_detail exactly
    # =====================================================

    # Base payable days: Present + Late + Leave
    payable_days = Decimal(present_days + late_days + leave_days)

    # --- Half Day processing ---
    half_day_earned    = Decimal("0.00")
    half_day_deduction = Decimal("0.00")

    for record in attendances.filter(status="Half Day").exclude(date__week_day=1):
        if second_saturday and record.date == second_saturday:
            payable_days    += Decimal("1")          # 2nd Sat Half Day → full pay
            half_day_earned += per_day_salary
        else:
            payable_days       += Decimal("0.5")     # Normal Half Day → half pay
            half_day_earned    += half_day_salary
            half_day_deduction += half_day_salary    # deduct half day salary

    # --- Sunday rule ---
    sunday_cut = Decimal("0.00")

    for sunday_record in attendances.filter(date__week_day=1):
        prev_saturday = sunday_record.date - timedelta(days=1)
        next_monday   = sunday_record.date + timedelta(days=1)

        sat_absent = attendances.filter(date=prev_saturday, status="Absent").exists()
        mon_absent = attendances.filter(date=next_monday,   status="Absent").exists()

        if sat_absent and mon_absent:
            sunday_cut   += per_day_salary           # unpaid Sunday
        else:
            payable_days += Decimal("1")             # paid Sunday

    # --- 2nd Saturday rule ---
    second_sat_deduction = Decimal("0.00")
    if second_saturday:
        second_sat_record = attendances.filter(date=second_saturday).first()
        if second_sat_record and second_sat_record.status == "Absent":
            second_sat_deduction = per_day_salary    # explicitly absent → deduct

    # --- Absent day deductions (skip 2nd Saturday — handled above) ---
    absent_deduction = Decimal("0.00")
    for record in attendances.filter(status="Absent").exclude(date__week_day=1):
        if second_saturday and record.date == second_saturday:
            continue
        absent_deduction += per_day_salary

    # --- Total attendance deduction ---
    attendance_deduction = (
        absent_deduction
        + half_day_deduction
        + sunday_cut
        + second_sat_deduction
    ).quantize(Decimal("0.01"))

    # --- Admin deduction ---
    admin_deduction = payroll.deductions

    # --- Total deduction ---
    total_deduction = (
        attendance_deduction + admin_deduction
    ).quantize(Decimal("0.01"))

    # =====================================================
    # EARNED SALARY COMPONENTS
    # Mirrors payroll_detail exactly
    # =====================================================
    hra_rate = payroll.hra_rate / Decimal("100")   # e.g. 0.40
    da_rate  = payroll.da_rate  / Decimal("100")   # e.g. 0.60

    earned_gross = (
        per_day_salary * payable_days
        - sunday_cut
        - second_sat_deduction
    )

    divisor             = Decimal("1") + hra_rate + da_rate
    earned_basic_salary = (earned_gross / divisor).quantize(Decimal("0.01"))
    earned_hra          = (earned_basic_salary * hra_rate).quantize(Decimal("0.01"))
    earned_da           = (earned_basic_salary * da_rate).quantize(Decimal("0.01"))

    # =====================================================
    # NET SALARY
    # =====================================================
    net_salary = (
        earned_gross
        + payroll.bonus
        - admin_deduction
    ).quantize(Decimal("0.01"))

    if net_salary < Decimal("0.00"):
        net_salary = Decimal("0.00")

    # =====================================================
    # GROSS SALARY (full month — basic + hra + da)
    # =====================================================
    gross_salary = gross_month.quantize(Decimal("0.01"))

    # =====================================================
    # CUT DAYS (for display)
    # =====================================================
    cut_days = (
        Decimal(absent_days)
        + (half_day_deduction / per_day_salary if per_day_salary else Decimal("0"))
    ).quantize(Decimal("0.01"))

    # =====================================================
    # SAVE UPDATED VALUES TO PAYROLL
    # =====================================================
    payroll.earned_basic_salary = earned_basic_salary
    payroll.earned_hra          = earned_hra
    payroll.earned_da           = earned_da
    payroll.net_salary          = net_salary
    payroll.save()

    # =====================================================
    # GENERATE PDF
    # =====================================================
    pdf_data = generate_salary_slip(

        employee=profile,
        payroll=payroll,

        # Attendance counts
        present_days=present_days,
        absent_days=absent_days,
        late_days=late_days,
        leave_days=leave_days,
        half_day_days=half_day_days,

        # Calendar
        total_month_days=total_month_days,
        payable_days=payable_days,
        cut_days=cut_days,

        # Per day rates
        per_day_salary=per_day_salary,
        half_day_salary=half_day_salary,

        # Earned components
        earned_basic_salary=earned_basic_salary,
        earned_hra=earned_hra,
        earned_da=earned_da,

        # Deduction breakdown
        attendance_deduction=attendance_deduction,
        absent_deduction=absent_deduction.quantize(Decimal("0.01")),
        half_day_deduction=half_day_deduction.quantize(Decimal("0.01")),
        sunday_cut=sunday_cut.quantize(Decimal("0.01")),
        admin_deduction=admin_deduction,
        total_deduction=total_deduction,

        # Totals
        gross_salary=gross_salary,
        net_salary=net_salary,
    )

    filename = f"SalarySlip_{profile.emp_id}_{month}_{year}.pdf"
    return salary_slip_response(filename, pdf_data)