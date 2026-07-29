# payroll/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("<uuid:user_id>/", views.payroll_dashboard, name="payroll_dashboard"),

 # ADD PAYROLL
    path(
        "<uuid:user_id>/<int:month>/<int:year>/add/",
        views.add_payroll,
        name="add_payroll"
    ),

    # EDIT PAYROLL
    path(
        "<uuid:user_id>/<int:month>/<int:year>/edit/",
        views.edit_payroll,
        name="edit_payroll"
    ),

    # PAYROLL DETAIL
    path(
        "<uuid:user_id>/<int:month>/<int:year>/details/",
        views.payroll_detail,
        name="payroll_detail"
    ),
    
    path(
        "salary-slip/download/<uuid:user_id>/<int:month>/<int:year>/",
        views.download_salary_slip,
        name="download_salary_slip"
    ),

]
