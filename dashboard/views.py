from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

from employees.models import EmployeeProfile
from attendance.models import Attendance
from datetime import datetime, timedelta
import calendar
import json
from noticeboard.models import NoticeBoard
from noticeboard.views import visible_notices_for
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
    
    # Notice Board Data — only notices targeted at this employee's
    # department (or "All Employees"); staff/admins see every notice.
    notices = visible_notices_for(
        user,
        NoticeBoard.objects.filter(is_active=True)
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



@login_required
def leaderboard_page(request):
    from datetime import date, time as dt_time
    from collections import defaultdict

    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (TypeError, ValueError):
        year, month = today.year, today.month

    days_in_month = calendar.monthrange(year, month)[1]
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)
    effective_end = min(month_end, today)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    prev_days_in_month = calendar.monthrange(prev_year, prev_month)[1]
    prev_start = date(prev_year, prev_month, 1)
    prev_end = date(prev_year, prev_month, prev_days_in_month)

    def working_days_between(start, end):
        if end < start:
            return 0
        return sum(
            1 for n in range((end - start).days + 1)
            if (start + timedelta(days=n)).weekday() != 6  # Sunday off
        )

    working_days = working_days_between(month_start, effective_end)
    prev_working_days = working_days_between(prev_start, prev_end)

    employees = list(
        User.objects.filter(employee_profile__isnull=False)
        .select_related('employee_profile', 'employee_profile__admin_data')
    )

    all_records = Attendance.objects.filter(
        employee__in=employees,
        date__gte=prev_start,
        date__lte=effective_end,
    ).values('employee_id', 'date', 'status', 'check_in')

    records_by_emp = defaultdict(dict)
    for r in all_records:
        records_by_emp[r['employee_id']][r['date']] = r['status']

    STATUS_WEIGHT = {'Present': 1, 'Late': 1, 'Half Day': 0.5}

    # =========================================
    # LEADERBOARD SCORE (ranking metric)
    # =========================================
    # +10 for checking in at/before 9:30 AM, -10 for checking in after.
    # Days with no check-in at all (absent) neither earn nor lose points —
    # only actual check-in events are scored.
    # Cutoff is exclusive of 9:31:00 (not just 9:30:00) so a check-in
    # anywhere within the 9:30 minute (e.g. 9:30:45, which still shows
    # as "9:30 AM") counts as on-time instead of being penalized.
    LEADERBOARD_CUTOFF = dt_time(9, 31)

    points_by_emp = defaultdict(int)
    checkin_seconds_by_emp = defaultdict(list)
    for r in all_records:
        if month_start <= r['date'] <= effective_end and r['check_in']:
            points_by_emp[r['employee_id']] += 10 if r['check_in'] < LEADERBOARD_CUTOFF else -10
            t = r['check_in']
            checkin_seconds_by_emp[r['employee_id']].append(t.hour * 3600 + t.minute * 60 + t.second)

    # Today's exact check-in time, independent of which month is being
    # viewed (a past month's data wouldn't otherwise include today).
    today_checkin_by_emp = {
        r['employee_id']: r['check_in']
        for r in Attendance.objects.filter(
            employee__in=employees, date=today, check_in__isnull=False
        ).values('employee_id', 'check_in')
    }

    def status_for(pct):
        if pct >= 95:
            return 'Excellent', 'excellent'
        if pct >= 85:
            return 'Good', 'good'
        if pct >= 70:
            return 'Average', 'average'
        return 'Needs Improvement', 'poor'

    rows = []
    prev_percentages = []

    for emp in employees:
        emp_records = records_by_emp.get(emp.id, {})

        present_days = sum(
            STATUS_WEIGHT.get(status, 0)
            for d, status in emp_records.items()
            if month_start <= d <= effective_end
        )
        pct = round((present_days / working_days) * 100, 1) if working_days else 0

        prev_present = sum(
            STATUS_WEIGHT.get(status, 0)
            for d, status in emp_records.items()
            if prev_start <= d <= prev_end
        )
        prev_pct = round((prev_present / prev_working_days) * 100, 1) if prev_working_days else 0
        prev_percentages.append(prev_pct)
        emp_improvement = round(pct - prev_pct, 1)

        # Streak: consecutive working days present, walking back from effective_end.
        streak = 0
        d = effective_end
        while d >= month_start:
            if d.weekday() == 6:
                d -= timedelta(days=1)
                continue
            if emp_records.get(d) in ('Present', 'Late', 'Half Day'):
                streak += 1
                d -= timedelta(days=1)
            else:
                break

        status_label, status_class = status_for(pct)

        emp_checkin_seconds = checkin_seconds_by_emp.get(emp.id)
        if emp_checkin_seconds:
            avg_checkin_seconds = sum(emp_checkin_seconds) / len(emp_checkin_seconds)
            avg_h, rem = divmod(int(avg_checkin_seconds), 3600)
            avg_m = rem // 60
            avg_checkin_display = dt_time(avg_h, avg_m).strftime('%I:%M %p').lstrip('0')
        else:
            avg_checkin_seconds = None
            avg_checkin_display = '—'

        today_checkin = today_checkin_by_emp.get(emp.id)
        today_checkin_display = (
            today_checkin.strftime('%I:%M %p').lstrip('0') if today_checkin else '—'
        )

        rows.append({
            'employee': emp,
            'present_days': present_days,
            'total_days': working_days,
            'percentage': pct,
            'streak': streak,
            'status_label': status_label,
            'status_class': status_class,
            'improvement': emp_improvement,
            'points': points_by_emp.get(emp.id, 0),
            'avg_checkin_seconds': avg_checkin_seconds,
            'avg_checkin_display': avg_checkin_display,
            'today_checkin_display': today_checkin_display,
        })

    # Ranked by leaderboard score first (highest points wins). Equal
    # scores are broken by who actually checked in earlier on average —
    # not by attendance % — since two people can both be "on time" but
    # one consistently clocks in earlier (e.g. 9:28 vs 9:29).
    rows.sort(key=lambda r: (
        -r['points'],
        r['avg_checkin_seconds'] if r['avg_checkin_seconds'] is not None else float('inf'),
        -r['percentage'],
        -r['streak'],
    ))
    for i, r in enumerate(rows, start=1):
        r['rank'] = i

    total_employees = len(rows)
    avg_attendance = round(sum(r['percentage'] for r in rows) / total_employees, 1) if total_employees else 0
    prev_avg_attendance = round(sum(prev_percentages) / total_employees, 1) if total_employees else 0
    perfect_attendance = sum(1 for r in rows if r['percentage'] >= 100)
    best_streak = max((r['streak'] for r in rows), default=0)
    improvement = round(avg_attendance - prev_avg_attendance, 1)

    # =========================================
    # DAILY TREND (org-wide attendance % per working day this month)
    # =========================================
    daily_present = defaultdict(float)
    for r in all_records:
        if month_start <= r['date'] <= effective_end:
            daily_present[r['date']] += STATUS_WEIGHT.get(r['status'], 0)

    trend_labels = []
    trend_values = []
    d = month_start
    while d <= effective_end:
        if d.weekday() != 6:
            trend_labels.append(d.strftime('%d %b'))
            trend_values.append(
                round((daily_present.get(d, 0) / total_employees) * 100, 1) if total_employees else 0
            )
        d += timedelta(days=1)

    # =========================================
    # ACHIEVEMENTS + RULE-BASED INSIGHT
    # =========================================
    most_improved = max(rows, key=lambda r: r['improvement'], default=None)
    streak_leader = max(rows, key=lambda r: r['streak'], default=None)

    if avg_attendance >= 90:
        ai_insight = f"Team attendance is excellent this month at {avg_attendance}% — keep up the momentum!"
    elif improvement > 0:
        ai_insight = f"Attendance improved by {improvement}% compared to last month. Trending in the right direction."
    elif improvement < 0:
        ai_insight = f"Attendance dropped by {abs(improvement)}% compared to last month — worth checking in with the team."
    else:
        ai_insight = f"Attendance is steady at {avg_attendance}%, unchanged from last month."

    context = {
        'rows': rows,
        'top3': rows[:3],
        'rest': rows[3:],

        'avg_attendance': avg_attendance,
        'total_employees': total_employees,
        'perfect_attendance': perfect_attendance,
        'best_streak': best_streak,
        'improvement': improvement,

        'selected_month': month,
        'selected_year': year,
        'month_name': month_start.strftime('%B'),
        'months': [(i, date(2000, i, 1).strftime('%B')) for i in range(1, 13)],
        'years': range(today.year - 3, today.year + 1),

        'trend_labels': json.dumps(trend_labels),
        'trend_values': json.dumps(trend_values),
        'most_improved': most_improved,
        'streak_leader': streak_leader,
        'ai_insight': ai_insight,
    }
    return render(request, 'pages/leaderboard.html', context)


def custom_404(request, exception):
    return render(request, '404.html', status=404)