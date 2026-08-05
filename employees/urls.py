from django.urls import path
from . import views
from attendance.pdf_report import download_attendance_pdf
from employees.views import download_id_card

urlpatterns = [
    path('', views.employee_dashboard, name='employee_dashboard'),
    path('dashboard/download/',      views.payroll_report_download, name='payroll_report_download'),
    path("list/", views.employee_list, name="employee_list"),
    path("add/", views.add_employee, name="add_employee"),

    # Use User UUID instead of employee_id
    path("<uuid:user_id>/", views.employee_detail, name="employee_detail"),
    path("profile/edit/", views.edit_employee_basic, name="edit_employee_basic"),
    path("profile/update-picture/", views.update_profile_picture, name="update_profile_picture"),

    # --- AdminControlledData ---
    path("<uuid:user_id>/admin-data/", views.admin_data_detail, name="admin_data_detail"),
    path("<uuid:user_id>/admin-data/edit/", views.admin_data_edit, name="admin_data_edit"),
    path('attendance/download-report/<uuid:user_id>/',download_attendance_pdf,name='download_attendance_pdf'),
    path("<uuid:user_id>/edit/", views.edit_add_employee, name="edit_add_employee"),
    
    # --- ID Card ---
    path('<uuid:user_id>/id-card/download/', download_id_card, name='download_id_card'),
    
    # ── experience letter download ─────────────────────────────────────────────
    path(
        'employee/<uuid:user_id>/download-experience-letter/',
        views.download_experience_letter,
        name='download_experience_letter',
    ),

    # ── appointment letter download ────────────────────────────────────────────
    path(
        'employee/<uuid:user_id>/download-appointment-letter/',
        views.download_appointment_letter,
        name='download_appointment_letter',
    ),

]
