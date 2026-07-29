
from django.urls import path
from . import views

urlpatterns = [
    path('employees/', views.leave_employee_list, name='leave_employee_list'),
    path(
    'convert-absent-leave/<uuid:user_id>/',
    views.convert_absent_to_leave,
    name='convert_absent_to_leave'
),
    
     path(
        "missing-attendance/",
        views.missing_attendance_employees,
        name="missing_attendance_employees"
    ),

    path(
        "mark-missing-absent/<uuid:user_id>/",
        views.mark_missing_attendance_absent,
        name="mark_missing_attendance_absent"
    ),
    
path('live/holiday/add/', views.add_holiday, name='add_holiday'),
]

