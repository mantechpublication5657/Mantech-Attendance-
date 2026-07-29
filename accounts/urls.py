from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

   path('verify_otp/<str:user_id>/', views.verify_user_otp, name='verify_otp'),
   path('resend_otp/<str:user_id>/', views.resend_otp, name='resend_otp'),
   path('verified/', views.verified_view, name='verified'),
   path('login/', views.login_view, name='login'),
   path('logout/', views.user_logout, name='logout'),
   path("change_password/", views.change_password_view, name="change_password"),

   # Password reset (Django's built-in token-based flow)
   path("reset_password/", auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/reset_password/done/',
   ), name="reset_password"),
   path("reset_password/done/", auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html',
   ), name="password_reset_done"),
   path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/',
   ), name="password_reset_confirm"),
   path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html',
   ), name="password_reset_complete"),

]
