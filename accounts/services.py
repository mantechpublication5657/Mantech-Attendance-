from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(user, otp):

    subject = "Your HRMS OTP Code"

    message = f"""
Hello {user.username},

Your OTP is: {otp}

This OTP is valid for login/verification.

Do not share it with anyone.

HRMS System
"""

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False
    )