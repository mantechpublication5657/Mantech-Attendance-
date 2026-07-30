from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

from employees.models import EmployeeProfile
from attendance.models import Attendance
from datetime import datetime, timedelta, time as dt_time
import calendar
from noticeboard.models import NoticeBoard
from grievances.models import AdminNotification
from accounts.models import User
from accounts.permissions import is_admin

@login_required
def home_dashboard(request):
    today = timezone.localdate()
    current_year = today.year
    current_month = today.month

    # =========================================
    # CURRENT USER PROFILE
    # =========================================

    user = request.user
    profile, created = EmployeeProfile.objects.get_or_create(user=user)

    try:
        employee_profile = EmployeeProfile.objects.select_related("admin_data").get(user=user)
    except EmployeeProfile.DoesNotExist:
        employee_profile = None

    # =========================================
    # USER ATTENDANCE ONLY
    # =========================================

    attendance_queryset = Attendance.objects.filter(
        employee=user,
        date__year=current_year,
        date__month=current_month
    )

    # =========================================
    # USER MONTHLY COUNTS
    # =========================================

    present_count = attendance_queryset.filter(status="Present").count()
    absent_count = attendance_queryset.filter(status="Absent").count()
    late_count = attendance_queryset.filter(status="Late").count()
    leave_count = attendance_queryset.filter(status="Leave").count()
    half_day_count = attendance_queryset.filter(status="Half Day").count()

    # =========================================
    # CALENDAR
    # =========================================

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(current_year, current_month)

    present_days = []
    absent_days = []
    late_days = []
    leave_days = []
    half_day_days = []
    sunday_days = []

    for a in attendance_queryset:
        if a.status == "Present":
            present_days.append(a.date.day)
        elif a.status == "Absent":
            absent_days.append(a.date.day)
        elif a.status == "Late":
            late_days.append(a.date.day)
        elif a.status == "Leave":
            leave_days.append(a.date.day)
        elif a.status == "Half Day":
            half_day_days.append(a.date.day)
        elif a.status == "Sunday":
            sunday_days.append(a.date.day)
            
    # =========================================
    # WEEKLY DATA (USER ONLY)
    # =========================================

    weekly_data = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        attendance = Attendance.objects.filter(
            employee=user,
            date=day
        )

        total_present = attendance.filter(status="Present").count()
        total_late = attendance.filter(status="Late").count()
        total_leave = attendance.filter(status="Leave").count()
        total_half_day = attendance.filter(status="Half Day").count()

        if total_present > 0:
            status = "Present"
        elif total_late > 0:
            status = "Late"
        elif total_leave > 0:
            status = "Leave"
        elif total_half_day > 0:
            status = "Half Day"
        else:
            status = "Absent"

        weekly_data.append({
            "day": day.strftime("%a"),
            "present": total_present,
            "late": total_late,
            "leave": total_leave,
            "half_day": total_half_day,
            "status": status,
        })

    # =========================================
    # HISTORY (USER ONLY)
    # =========================================

    attendance_history = Attendance.objects.filter(
        employee=user
    ).order_by("-date")[:10]

    # =========================================
    # RECENT EMPLOYEES (ONLY FOR ADMIN VIEW)
    # =========================================

    recent_employees = (
        EmployeeProfile.objects
        .select_related("admin_data")
        .order_by("-admin_data__joining_date")[:5]
    )

    total_employees = EmployeeProfile.objects.count()

    today_attendance_count = Attendance.objects.filter(
        date=today,
        check_in__isnull=False
    ).count()

    present_percentage = round(
        (today_attendance_count / total_employees) * 100, 2
    ) if total_employees else 0

    remaining_percentage = 100 - present_percentage
    
    
    # =========================================
    # NOTICEBOARD (USER ONLY)
    # =========================================
    
    # Notice Board Data
    notices = NoticeBoard.objects.filter(
        is_active=True
    ).order_by('-created_at')
    
    unseen_count = AdminNotification.objects.filter(
        is_seen=False
    ).count()

    # Add this alongside your existing present_days, absent_days etc.
    leave_remarks = {}
    for a in attendance_queryset:
        if a.status == 'Leave' and a.remarks:
            leave_remarks[a.date.day] = a.remarks
            
    # =========================================
    # For present and absent toggle in attendance history
    # =========================================
    
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Present = has an Attendance record today WITH status 'Present' or 'Late'
    # (check_in may or may not exist — status is the source of truth)
    present_records = Attendance.objects.filter(
        date=today,
        status__in=['Present', 'Late', 'Half Day']
    ).select_related(
        'employee',
        'employee__employee_profile',
        'employee__employee_profile__admin_data'
    ).order_by('check_in')

    present_employee_ids = present_records.values_list('employee_id', flat=True)

    # =========================================
    # ATTENDANCE LEADERBOARD (TOP 3 EARLIEST CHECK-INS)
    # =========================================
    # Only employees who checked in at/before the 9:30 cutoff qualify.
    # Ranking is purely by check-in time, so a late arrival among the
    # current top 3 naturally falls out as soon as someone earlier is
    # queried in — no separate "late" bookkeeping needed.
    LEADERBOARD_CUTOFF = dt_time(9, 30)

    leaderboard = Attendance.objects.filter(
        date=today,
        check_in__isnull=False,
        check_in__lte=LEADERBOARD_CUTOFF
    ).select_related(
        'employee',
        'employee__employee_profile',
        'employee__employee_profile__admin_data'
    ).order_by('check_in')[:3]

    # Absent = either has a record with Absent/Leave status today,
    # OR has no record at all today
    # We handle both cases by querying all employees then excluding present ones
    absent_employees = User.objects.filter(
        employee_profile__isnull=False
    ).exclude(
        id__in=present_employee_ids
    ).select_related(
        'employee_profile',
        'employee_profile__admin_data'
    ).order_by('first_name')

    # Optionally: get their attendance record if it exists (for status label)
    absent_with_status = []
    for emp in absent_employees:
        try:
            record = Attendance.objects.get(employee=emp, date=today)
            att_status = record.status   # 'Absent', 'Leave', 'Sunday' etc.
        except Attendance.DoesNotExist:
            att_status = 'Absent'        # no record = treat as absent
        absent_with_status.append({
            'employee': emp,
            'status': att_status,
        })

    new_context = {
        'today': today,
        'selected_date': today,
        'present_records': present_records,
        'absent_employees': absent_with_status,   # now a list of dicts
        'present_count': present_records.count(),
        'absent_count': len(absent_with_status),
        'total_employees': User.objects.filter(employee_profile__isnull=False).count(),
    }
    # add attendance_rate
    total = new_context['total_employees']
    new_context['attendance_rate'] = round(
        new_context['present_count'] / total * 100, 1
    ) if total else 0

        
    # =========================================
    # CONTEXT
    # =========================================

    context = {

    # USER DATA
    "profile": profile,
    "employee_profile": employee_profile,
    "attendance_queryset": attendance_queryset,

    # USER STATS
    "present_count": present_count,
    "absent_count": absent_count,
    "late_count": late_count,
    "leave_count": leave_count,
    "half_day_count": half_day_count,
    
    # CALENDAR
    "month_days": month_days,
    "present_days": present_days,
    "absent_days": absent_days,
    "late_days": late_days,
    "leave_days": leave_days,
    "half_day_days": half_day_days,
    'sunday_days':    sunday_days,
    
    # WEEKLY
    "weekly_data": weekly_data,

    # HISTORY
    "attendance_history": attendance_history,

    # ADMIN OVERVIEW
    "recent_employees": recent_employees,
    "total_employees": total_employees,
    "today_attendance_count": today_attendance_count,
    "present_percentage": present_percentage,
    "remaining_percentage": remaining_percentage,

    # DATE
    "today": today,
    "current_time": timezone.localtime(),
    "current_month_name": today.strftime("%B"),
    "current_year": current_year,
    
    # NOTICEBOARD
    "notices": notices,
    "notices_count": notices.count(),

    # LEADERBOARD
    "leaderboard": leaderboard,
    
    # UNSEEN COUNT FOR GRAVIENCE
    'unseen_count': unseen_count,
    
    # ADD HOLIDAY
    'leave_remarks': leave_remarks,
    
    # FOR PRESENT AND ABSENT TOGGLE
    'present_today': present_records,
    'absent_today': absent_employees,
    'present_today_count': present_records.count(),
    'absent_today_count': absent_employees.count(),
    
    **new_context,
    
    }
    return render(request, "pages/home.html", context)



# from yourapp.models import Attendance  ← your actual import
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
@user_passes_test(is_admin)
def attendance_today_list(request):

    # --- Date filter ---
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    # --- Department filter ---
    department = request.GET.get('department', '')

    # --- Present: status is Present, Late, or Half Day ---
    present_qs = Attendance.objects.filter(
        date=selected_date,
        status__in=['Present', 'Late', 'Half Day']
    ).select_related(
        'employee',
        'employee__employee_profile',
        'employee__employee_profile__admin_data',
    ).order_by('check_in')

    if department:
        present_qs = present_qs.filter(
            employee__employee_profile__department=department
        )

    present_employee_ids = present_qs.values_list('employee_id', flat=True)

    # --- Absent: all employees excluding present ones ---
    absent_user_qs = User.objects.filter(
        employee_profile__isnull=False
    ).exclude(
        id__in=present_employee_ids
    ).select_related(
        'employee_profile',
        'employee_profile__admin_data',
    ).order_by('first_name')

    if department:
        absent_user_qs = absent_user_qs.filter(
            employee_profile__department=department
        )

    # Attach today's attendance status to each absent employee
    # (could be Absent/Leave/Sunday record, or no record at all)
    today_records = Attendance.objects.filter(
        date=selected_date
    ).values('employee_id', 'status')

    today_status_map = {r['employee_id']: r['status'] for r in today_records}

    absent_with_status = []
    for emp in absent_user_qs:
        absent_with_status.append({
            'employee': emp,
            'status': today_status_map.get(emp.id, 'Absent'),  # no record = Absent
        })

    # --- Counts ---
    total_employees = User.objects.filter(employee_profile__isnull=False).count()
    present_count   = present_qs.count()
    absent_count    = len(absent_with_status)
    attendance_rate = round((present_count / total_employees * 100), 1) if total_employees else 0

    context = {
        'selected_date'   : selected_date,
        'present_records' : present_qs,
        'absent_employees': absent_with_status,   # list of dicts: {employee, status}
        'present_count'   : present_count,
        'absent_count'    : absent_count,
        'total_employees' : total_employees,
        'attendance_rate' : attendance_rate,
    }
    return render(request, 'dashboard/attendance_today_list.html', context)



def custom_404(request, exception):
    return render(request, '404.html', status=404)