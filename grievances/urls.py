from django.urls import path
from . import views


urlpatterns = [

    # ── Dashboard (employee + admin, single entry point) ──────────────
    path('grievance/dashboard/', views.grievance_dashboard, name='grievance_dashboard'),

    # ── Employee URLs ──────────────────────────────────────────────────
    path('my-applications/', views.employee_grievance_list, name='grievance_list'),
    path('my-applications/new/', views.grievance_create, name='grievance_create'),
    path('my-applications/<int:pk>/', views.grievance_detail_employee, name='grievance_detail'),
    path('my-applications/<int:pk>/edit/', views.grievance_edit, name='grievance_edit'),
    path('my-applications/<int:pk>/delete/', views.grievance_delete, name='grievance_delete'),

    # ── Admin URLs ─────────────────────────────────────────────────────
    path('grievances/', views.admin_notification_list, name='admin_notifications'),
    path('grievances/<int:pk>/', views.admin_grievance_detail, name='admin_grievance_detail'),

    # ── Admin AJAX ─────────────────────────────────────────────────────
    path('grievances/mark-all-seen/', views.admin_mark_all_seen, name='admin_mark_all_seen'),
    path('grievances/unseen-count/', views.admin_unseen_count, name='admin_unseen_count'),
    
]