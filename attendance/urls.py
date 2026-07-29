from django.urls import path
from . import views
from .pdf_report import download_attendance_pdf

urlpatterns = [
    path('<uuid:user_id>/', views.attendance_home, name='attendance_dashboard'),

    path('check-in/', views.check_in, name='check_in'),

    path('check-out/', views.check_out, name='check_out'),
    
    # urls.py

    path(
        'update-check-out/<uuid:user_id>/',
        views.update_check_out,
        name='update_check_out'
    ),

    path('monthly/', views.monthly_attendance, name='monthly_attendance'),
        

]