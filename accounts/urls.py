from django.urls import path
from . import views

urlpatterns = [
    
   path('signup/', views.signup_view, name='signup'),
   path('verify_otp/<str:user_id>/', views.verify_user_otp, name='verify_otp'),
   path('resend_otp/<str:user_id>/', views.resend_otp, name='resend_otp'),
   path('verified/', views.verified_view, name='verified'),
   path('login/', views.login_view, name='login'),
   path('logout/', views.user_logout, name='logout'),
   path("reset_password/",views.reset_password_view,name="reset_password"),
   path("change_password/",views.change_password_view,name="change_password"),
   
]