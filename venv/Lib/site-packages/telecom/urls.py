from django.urls import path
from telecom import views

urlpatterns = [
    path('send-otp/', views.SendOTPView.as_view()),
    path('verify-otp/', views.VerifyOTPView.as_view()),
    path('send-sms/', views.SendSMSView.as_view()),
]
