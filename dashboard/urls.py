from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_dashboard, name='home'),
    path('attendance-today/', views.attendance_today_list, name='attendance_today_list'),
]