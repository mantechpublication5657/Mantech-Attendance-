from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from payroll.views import User, is_admin

from employees.views import is_admin
from attendance.models import Attendance
from employees.models import EmployeeProfile
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.core.paginator import Paginator

from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test

from employees.models import EmployeeProfile
from attendance.models import Attendance


@user_passes_test(is_admin)
def leave_employee_list(request):

    query = request.GET.get("q", "").strip()

    # MONTH & YEAR FILTER
    selected_month = request.GET.get("month")
    selected_year = request.GET.get("year")

    today = timezone.localdate()

    # DEFAULT CURRENT MONTH/YEAR
    current_month = today.month
    current_year = today.year

    # IF USER SELECTED FILTER
    if selected_month and selected_year:

        current_month = int(selected_month)
        current_year = int(selected_year)

    # GET EMPLOYEE IDS WHO ARE ABSENT
    absent_employee_ids = Attendance.objects.filter(
        status="Absent",
        date__month=current_month,
        date__year=current_year
    ).values_list(
        "employee_id",
        flat=True
    ).distinct()

    # ONLY ABSENT EMPLOYEES
    employees_qs = EmployeeProfile.objects.select_related(
        "user",
        "admin_data"
    ).filter(
        user__id__in=absent_employee_ids
    )

    # SEARCH FILTER
    if query:

        employees_qs = employees_qs.filter(

            Q(user__username__icontains=query) |

            Q(user__first_name__icontains=query) |

            Q(user__last_name__icontains=query) |

            Q(emp_id__icontains=query)

        )

    # ORDERING
    employees_qs = employees_qs.order_by(
        "user__first_name"
    )

    # PAGINATION
    paginator = Paginator(employees_qs, 10)

    page_number = request.GET.get("page")

    employees = paginator.get_page(page_number)

    context = {
        "employees": employees,
        "query": query,
        "current_month": current_month,
        "current_year": current_year,
    }

    return render(
        request,
        "leaves/leave_dashboard.html",
        context
    )

@login_required
def convert_absent_to_leave(request, user_id):

    employee = get_object_or_404(
        User,
        id=user_id
    )

    absent_records = Attendance.objects.filter(
        employee=employee,
        status='Absent'
    ).order_by('-date')

    if request.method == "POST":

        attendance_id = request.POST.get("attendance_id")

        attendance = get_object_or_404(
            Attendance,
            id=attendance_id,
            employee=employee
        )

        attendance.status = "Leave"
        attendance.save()

        messages.success(
            request,
            "Attendance converted successfully."
        )

        return redirect(
            'convert_absent_to_leave',
            user_id=employee.id
        )

    context = {
        "absent_records": absent_records,
        "employee": employee,
    }

    return render(
        request,
        "leaves/convert_leave.html",
        context
    )
    
# views.py


from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from employees.models import EmployeeProfile
from attendance.models import Attendance
import calendar

def is_admin(user):
    return user.is_superuser or user.groups.filter(name="Admin").exists() or user.is_staff


@user_passes_test(is_admin)
def missing_attendance_employees(request):

    today = timezone.localdate()

    # -------------------------------
    # FILTERS
    # -------------------------------

    # Username filter
    username_query = request.GET.get("username", "").strip()

    # Month filter
    selected_month = request.GET.get("month")

    # Year filter
    selected_year = request.GET.get("year")

    # Default current month/year
    current_year = today.year
    current_month = today.month

    if selected_month and selected_year:
        current_month = int(selected_month)
        current_year = int(selected_year)

    # Start and end date of selected month
    start_date = date(current_year, current_month, 1)

    # If selected month is current month → till today
    if current_month == today.month and current_year == today.year:
        end_date = today
    else:
        # Last date of selected month
        if current_month == 12:
            end_date = date(current_year, 12, 31)
        else:
            end_date = date(current_year, current_month + 1, 1) - timedelta(days=1)

    employees_data = []

    employees = EmployeeProfile.objects.select_related(
        "user",
        "admin_data"
    ).all()

    # Username filter
    if username_query:
        employees = employees.filter(
            Q(user__username__icontains=username_query) |
            Q(emp_id__icontains=username_query)
        )

    for employee in employees:

        # Skip employees without admin data
        if not hasattr(employee, "admin_data"):
            continue

        # Skip employees without joining date
        if not employee.admin_data.joining_date:
            continue

        joining_date = employee.admin_data.joining_date

        # Skip future joining employees
        if joining_date > end_date:
            continue

        # Start checking from joining date or month start
        checking_start = max(joining_date, start_date)

        missing_dates = []

        current_date = checking_start

        while current_date <= end_date:

            # Skip Sundays (Optional)
            # if current_date.weekday() == 6:
            #     current_date += timedelta(days=1)
            #     continue

            attendance_exists = Attendance.objects.filter(
                employee=employee.user,
                date=current_date
            ).exists()

            if not attendance_exists:
                missing_dates.append(current_date)

            current_date += timedelta(days=1)

        if missing_dates:

            employees_data.append({
                "employee": employee,
                "missing_dates": missing_dates,
                "total_missing": len(missing_dates),
            })

    context = {
        "employees_data": employees_data,
        "current_month": current_month,
        "current_year": current_year,
        "selected_username": username_query,
    }

    return render(
        request,
        "leaves/missing_attendance_employees.html",
        context
    )

# @user_passes_test(is_admin)
# def mark_missing_attendance_absent(request, user_id):

#     today = timezone.localdate()

#     current_year = today.year
#     current_month = today.month

#     start_date = date(current_year, current_month, 1)

#     end_date = today

#     employee = get_object_or_404(
#         EmployeeProfile.objects.select_related(
#             "user",
#             "admin_data"
#         ),
#         user_id=user_id
#     )

#     # Check joining date
#     if not hasattr(employee, "admin_data") or not employee.admin_data.joining_date:

#         messages.error(request, "Joining date not found.")

#         return redirect("missing_attendance_employees")

#     joining_date = employee.admin_data.joining_date

#     checking_start = max(joining_date, start_date)

#     current_date = checking_start

#     created_count = 0

#     while current_date <= end_date:
#         attendance_exists = Attendance.objects.filter(
#             employee=employee.user,
#             date=current_date
#         ).exists()

#         if not attendance_exists:

#             # Sunday
#             if current_date.weekday() == 6:

#                 Attendance.objects.create(
#                     employee=employee.user,
#                     date=current_date,
#                     status="Off",
#                     check_in=None,
#                     check_out=None,
#                     remarks="Sunday Off"
#                 )

#             # Other Days
#             else:

#                 Attendance.objects.create(
#                     employee=employee.user,
#                     date=current_date,
#                     status="Absent",
#                     check_in=None,
#                     check_out=None,
#                     remarks="Marked absent manually by admin"
#                 )

#             created_count += 1

#         current_date += timedelta(days=1)
    
#     messages.success(
#         request,
#         f"{created_count} absent records created for {employee.user.username}."
#     )

#     return redirect("missing_attendance_employees")

@user_passes_test(is_admin)
def mark_missing_attendance_absent(request, user_id):
    today = timezone.localdate()

    # Get month and year from filter form
    try:
        month = int(request.GET.get("month", today.month))
        year = int(request.GET.get("year", today.year))
    except (TypeError, ValueError):
        messages.error(request, "Invalid month or year.")
        return redirect("missing_attendance_employees")

    # First and last day of selected month
    start_date = date(year, month, 1)

    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    # Prevent future dates
    if end_date > today:
        end_date = today

    employee = get_object_or_404(
        EmployeeProfile.objects.select_related(
            "user",
            "admin_data"
        ),
        user_id=user_id
    )

    # Check joining date
    if (
        not hasattr(employee, "admin_data")
        or not employee.admin_data.joining_date
    ):
        messages.error(request, "Joining date not found.")
        return redirect(
            "missing_attendance_employees"
        )

    joining_date = employee.admin_data.joining_date

    # Don't create attendance before joining date
    checking_start = max(joining_date, start_date)

    current_date = checking_start
    created_count = 0

    while current_date <= end_date:

        attendance_exists = Attendance.objects.filter(
            employee=employee.user,
            date=current_date
        ).exists()

        if not attendance_exists:

            # Sunday
            if current_date.weekday() == 6:
                Attendance.objects.create(
                    employee=employee.user,
                    date=current_date,
                    status="Sunday",
                    check_in=None,
                    check_out=None,
                    remarks="Sunday Off"
                )

            # Other days
            else:
                Attendance.objects.create(
                    employee=employee.user,
                    date=current_date,
                    status="Absent",
                    check_in=None,
                    check_out=None,
                    remarks="Marked absent manually by admin"
                )

            created_count += 1

        current_date += timedelta(days=1)

    messages.success(
        request,
        f"{created_count} attendance records created for "
        f"{employee.user.username} ({month}/{year})."
    )

    # Return to same filtered page
    return redirect(
        "missing_attendance_employees"
    )


# attendance/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from attendance.models import  Attendance
from leaves.models import Holiday

User = get_user_model()


def is_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def add_holiday(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        holiday_type = request.POST.get('holiday_type')
        custom_type = request.POST.get('custom_type', '').strip()
        remarks = request.POST.get('remarks', '').strip()

        # Validation
        if not date or not holiday_type:
            messages.error(request, 'Date and holiday type are required.')
            return render(request, 'attendance/add_holiday.html', {
                'form_data': request.POST
            })

        if holiday_type == 'Other' and not custom_type:
            messages.error(request, 'Please specify the holiday type.')
            return render(request, 'attendance/add_holiday.html', {
                'form_data': request.POST
            })

        # Build the remark string for attendance
        display_type = custom_type if holiday_type == 'Other' else holiday_type
        attendance_remark = f"{display_type}"
        if remarks:
            attendance_remark += f" — {remarks}"

        # Save holiday record
        holiday, created = Holiday.objects.get_or_create(
            date=date,
            defaults={
                'holiday_type': holiday_type,
                'custom_type': custom_type or None,
                'remarks': remarks or None,
                'created_by': request.user,
            }
        )

        if not created:
            messages.warning(request, f'A holiday on {date} already exists.')
            return render(request, 'attendance/add_holiday.html', {
                'form_data': request.POST
            })

        # Apply Leave to all active employees
        employees = User.objects.filter(is_active=True)
        created_count = 0
        skipped_count = 0

        for employee in employees:
            obj, was_created = Attendance.objects.get_or_create(
                employee=employee,
                date=date,
                defaults={
                    'status': 'Leave',
                    'remarks': attendance_remark,
                }
            )
            if was_created:
                created_count += 1
            else:
                skipped_count += 1

        messages.success(
            request,
            f'Holiday applied! {created_count} employee(s) marked as Leave. '
            f'{skipped_count} already had an attendance record on {date}.'
        )
        return redirect('add_holiday')

    return render(request, 'leaves/add_holiday.html', {
        'holiday_type_choices': Holiday.HOLIDAY_TYPE_CHOICES,
    })