from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import Attendance
import calendar
from datetime import datetime
from datetime import time


from django.utils.timezone import localdate
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

from .models import Attendance
from employees.models import EmployeeProfile
from accounts.permissions import owner_or_admin_required

@login_required
@owner_or_admin_required
def attendance_home(request, user_id):

    today = localdate()
    current_year = today.year
    current_month = today.month

    current_day = timezone.localdate()
    now_time = timezone.localtime().time()
    
    employee_profile = EmployeeProfile.objects.filter(user_id=user_id).first()
    
    attendance = Attendance.objects.filter(
        employee=user_id,
        date=current_day
    ).first()

    checkin_done = False
    checkout_done = False
    can_checkout = False
    attendance_message = "No record for today"

    # ==========================================
    # ATTENDANCE STATUS LOGIC
    # ==========================================
    if attendance:
        current_time = timezone.localtime().time()
        office_end_time = time(18, 5)
        late_time = time(9, 40)

        if attendance.check_in:
            checkin_done = True
            attendance_message = "Attendance Marked"

        if attendance.check_out:
            checkout_done = True
            attendance_message = "Checked Out"

        if attendance.check_in and not attendance.check_out:
            if current_time >= office_end_time:
                attendance.check_out = office_end_time
                attendance.status = "Present"
                attendance.save()

        if attendance.check_in and attendance.check_out:
            checkin_datetime = datetime.combine(today, attendance.check_in)
            checkout_datetime = datetime.combine(today, attendance.check_out)
            total_hours = (checkout_datetime - checkin_datetime).total_seconds() / 3600

            if total_hours <= 1:
                attendance.status = "Absent"
            elif attendance.check_out < office_end_time:
                attendance.status = "Half Day"
            elif attendance.check_in > late_time:
                attendance.status = "Late"
            else:
                attendance.status = "Present"
            attendance.save()

    # ==========================================
    # FILTERS
    # ==========================================
    selected_month = request.GET.get('month')
    selected_status = request.GET.get('status')

    # Resolve active month/year for calendar & labels
    if selected_month:
        current_month = int(selected_month)

    # ==========================================
    # CALENDAR — always full month, no status filter
    # so all days are colored correctly
    # ==========================================
    full_month_qs = Attendance.objects.filter(
        employee=employee_profile.user.id,
        date__year=current_year,
        date__month=current_month,
    )

    present_days = []
    absent_days = []
    late_days = []
    leave_days = []
    half_day_days = []
    sunday_days = []

    for item in full_month_qs:
        if item.status == 'Present':
            present_days.append(item.date.day)
        elif item.status == 'Absent':
            absent_days.append(item.date.day)
        elif item.status == 'Late':
            late_days.append(item.date.day)
        elif item.status == 'Leave':
            leave_days.append(item.date.day)
        elif item.status == 'Half Day':
            half_day_days.append(item.date.day)
        elif item.status == 'Sunday':
            sunday_days.append(item.date.day)

    # ==========================================
    # FILTERED QUERYSET — for table, counts, chart
    # ==========================================
    attendance_queryset = Attendance.objects.filter(
        employee=employee_profile.user.id,
        date__year=current_year,
        date__month=current_month,
    )

    if selected_status:
        attendance_queryset = attendance_queryset.filter(status=selected_status)

    present_count = attendance_queryset.filter(status='Present').count()
    absent_count  = attendance_queryset.filter(status='Absent').count()
    late_count    = attendance_queryset.filter(status='Late').count()
    leave_count   = attendance_queryset.filter(status='Leave').count()
    half_day_count = attendance_queryset.filter(status='Half Day').count()
    sunday_count = attendance_queryset.filter(status='Sunday').count()

    # ==========================================
    # CALENDAR GRID
    # ==========================================
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(current_year, current_month)

    # Month name for the filtered month
    import datetime as dt
    filtered_month_name = dt.date(current_year, current_month, 1).strftime('%B')
    
    from datetime import date, timedelta
    # ==========================================
    # MONTH ENDED + 7-DAY WINDOW CHECK
    # ==========================================
    
    if current_month == 12:
        first_of_next_month = date(current_year + 1, 1, 1)
    else:
        first_of_next_month = date(current_year, current_month + 1, 1)

    download_deadline = first_of_next_month + timedelta(days=7)

    month_ended = (today >= first_of_next_month) and (today <= download_deadline)
    
    # After the month_ended check, add:
    from payroll.models import Payroll  # adjust import path as needed

    payroll = Payroll.objects.filter(
        employee=request.user,
        month=current_month,
        year=current_year
    ).first()

    # for add attendance 
    # Add this alongside your existing present_days, absent_days etc.
    leave_remarks = {}
    for a in attendance_queryset:
        if a.status == 'Leave' and a.remarks:
            leave_remarks[a.date.day] = a.remarks
            
            
    # ==========================================
    # CONTEXT
    # ==========================================
    context = {
        'month_days': month_days,
        'attendance_history': attendance_queryset.order_by('-date'),

        # Calendar coloring — always full month
        'present_days':   present_days,
        'absent_days':    absent_days,
        'late_days':      late_days,
        'leave_days':     leave_days,
        'half_day_days':  half_day_days,
        'sunday_days':    sunday_days,

        # Counts — respect status filter
        'present_count':  present_count,
        'absent_count':   absent_count,
        'late_count':     late_count,
        'leave_count':    leave_count,
        'half_day_count': half_day_count,
        'sunday_count':   sunday_count,
        'total_count':    present_count + late_count + half_day_count + leave_count,

        'current_date':       today.strftime('%d %B, %Y'),
        'current_month_name': filtered_month_name,   # reflects filter
        'current_month':      current_month,          # for PDF link
        'current_year':       current_year,
        'current_time':       now_time,
        'today':              today,

        'selected_month':  selected_month or '',
        'selected_status': selected_status or '',

        'attendance':        attendance,
        'checkin_done':      checkin_done,
        'checkout_done':     checkout_done,
        'can_checkout':      can_checkout,
        'attendance_message': attendance_message,
        
        'payroll':     payroll,
        'month_ended': month_ended,
        
        # for add attendance
        'leave_remarks': leave_remarks,
        
        #Employee
        'employee_profile': employee_profile,
    }

    return render(request, 'attendance/attendance_page.html', context)
# -----------------------------
# CHECK IN
# -----------------------------
from django.utils import timezone
from django.utils.timezone import localtime


@login_required
def check_in(request):
    today = localtime().date()
    
    attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()

    if attendance and attendance.check_in:
        messages.warning(request, "You have already checked in today.")
        return redirect('attendance_dashboard', user_id=request.user.id)

    # Current India Time
    current_time = localtime().time()

    # 9:00-9:30 -> Present, 9:31-9:40 -> Late, 9:41 onward -> Half Day.
    late_start = timezone.datetime.strptime("09:31", "%H:%M").time()
    half_day_start = timezone.datetime.strptime("09:41", "%H:%M").time()

    if current_time < late_start:
        status = 'Present'
    elif current_time < half_day_start:
        status = 'Late'
    else:
        status = 'Half Day'

    is_late = status != 'Present'

    ip = request.META.get('REMOTE_ADDR')

    Attendance.objects.create(
        employee=request.user,
        date=today,
        check_in=current_time,
        status=status,
        is_late=is_late,
        ip_address=ip
    )

    messages.success(request, "Check-in successful.")

    return redirect('attendance_dashboard' , user_id=request.user.id)


@login_required
def check_out(request):

    today = localtime().date()
    current_time = localtime().time()

    late_time = timezone.datetime.strptime(
        "09:45",
        "%H:%M"
    ).time()

    # Half-day check-out opens at 2:00 PM, full-day check-out at 6:05 PM.
    half_day_time = time(14, 0)
    full_checkout_time = time(18, 5)

    attendance = Attendance.objects.filter(
        employee=request.user,
        date=today
    ).first()

    if not attendance:
        messages.error(request, "You must check in first.")
        return redirect('attendance_dashboard' , user_id=request.user.id)

    if attendance.check_out:
        messages.warning(request, "You have already checked out.")
        return redirect('attendance_dashboard', user_id=request.user.id)

    if current_time < half_day_time:
        messages.error(
            request,
            "Check-out is not allowed yet. Half-day check-out opens at 2:00 PM "
            "and full-day check-out at 6:05 PM."
        )
        return redirect('attendance_dashboard', user_id=request.user.id)

    attendance.check_out = current_time

    if current_time < full_checkout_time:
        attendance.status = "Half Day"
        attendance.save()
        messages.success(request, "Half-day check-out successful.")
    else:
        if attendance.check_in and attendance.check_in > late_time:
            attendance.status = "Late"
        else:
            attendance.status = "Present"
        attendance.save()
        messages.success(request, "Check-out successful.")

    return redirect('attendance_dashboard', user_id=request.user.id)



# -----------------------------
# UPDATE ATTENDANCE LAST UPDATED
# -----------------------------

@login_required
def update_check_out(request, user_id):

    # allow only POST request
    if request.method != "POST":
        return redirect('attendance_dashboard', user_id=request.user.id)

    today = localtime().date()
    current_time = localtime().time()

    # security check
    if request.user.id != user_id:

        messages.error(
            request,
            "Unauthorized Access"
        )

        return redirect('attendance_dashboard', user_id=request.user.id)

    # get today attendance
    attendance = Attendance.objects.filter(
        employee_id=user_id,
        date=today
    ).first()

    if not attendance:

        messages.error(
            request,
            "Attendance not found."
        )

        return redirect('attendance_dashboard', user_id=request.user.id)

    half_day_time = time(14, 0)
    full_checkout_time = time(18, 5)

    if current_time < half_day_time:
        messages.error(
            request,
            "Check-out is not allowed yet. Half-day check-out opens at 2:00 PM "
            "and full-day check-out at 6:05 PM."
        )
        return redirect('attendance_dashboard', user_id=request.user.id)

    # update checkout time
    attendance.check_out = current_time

    late_time = time(9, 45)
    if current_time < full_checkout_time:
        attendance.status = "Half Day"
    elif attendance.check_in and attendance.check_in > late_time:
        attendance.status = "Late"
    else:
        attendance.status = "Present"

    attendance.save()

    messages.success(
        request,
        "Recent Check Out Added Successfully."
    )

    return redirect('attendance_dashboard', user_id=request.user.id)

# -----------------------------
# MONTHLY ATTENDANCE
# -----------------------------
import calendar

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import localdate

from .models import Attendance


@login_required
def monthly_attendance(request):

    today = localdate()

    current_year = today.year
    current_month = today.month
    current_date = today.strftime('%d %B, %Y')

    # IMPORTANT
    # Sunday = first day
    cal = calendar.Calendar(firstweekday=6)

    month_days = cal.monthdayscalendar(
        current_year,
        current_month
    )

    attendance_list = Attendance.objects.filter(
        employee=request.user,
        date__year=current_year,
        date__month=current_month
    )

    present_days = []
    absent_days = []
    late_days = []

    for attendance in attendance_list:

        if attendance.status == 'Present':
            present_days.append(attendance.date.day)

        elif attendance.status == 'Absent':
            absent_days.append(attendance.date.day)

        elif attendance.status == 'Late':
            late_days.append(attendance.date.day)

    
    
    context = {

        'month_days': month_days,

        'present_days': present_days,

        'absent_days': absent_days,

        'late_days': late_days,
        'current_date': current_date,

        'current_month_name': today.strftime('%B'),

        'current_year': current_year,
        'attendance_history': attendance_list.order_by('-date'),
    }

    return render(
        request,
        'attendance/monthly_attendance.html',
        context
    )