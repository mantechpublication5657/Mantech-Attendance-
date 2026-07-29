
# Create your views here.
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.mail import send_mail

from django.contrib.auth import get_user_model
from .models import User

User = get_user_model()


def verify_user_otp(request, user_id):

    user = User.objects.get(id=user_id)

    # Remaining resend timer
    remaining_seconds = 0

    if user.otp_last_sent:

        resend_available_time = user.otp_last_sent + timedelta(minutes=5)

        if timezone.now() < resend_available_time:

            remaining_seconds = int(
                (resend_available_time - timezone.now()).total_seconds()
            )

    # Verify OTP
    if request.method == 'POST':

        entered_otp = request.POST.get('otp')

        if entered_otp == str(user.email_otp):

            user.is_email_verified = True
            user.email_otp = None
            user.save()

            messages.success(
                request,
                f"Email verified Successfully {user.username.capitalize()}!"
            )

            return redirect('verified')

        else:

            messages.error(
                request,
                f"Invalid OTP {user.username.capitalize()}!"
            )

    context = {
        'user_id': user.id,
        'remaining_seconds': remaining_seconds
    }

    return render(
        request,
        'accounts/verify_otp.html',
        context
    )

def resend_otp(request, user_id):

    user = User.objects.get(id=user_id)

    otp = get_random_string(length=6, allowed_chars='0123456789')

    user.email_otp = otp
    user.otp_last_sent = timezone.now()
    user.save()

    subject = "MP HRMS-New OTP Code"

    message = (
        f"Hello {user.username.capitalize()},\n\n"
        f"You requested a new One-Time Password (OTP) for your Mantech Publication HRMS account.\n\n"
        f"🔑 Your New OTP Code: {otp}\n\n"
        f"This code will expire in 5 minutes. Please do not share it with anyone.\n\n"
        f"If you did not request this OTP, please ignore this email or contact our support team immediately.\n\n"
        f"Best regards,\n"
        f"Mantech Publication HRMS Team"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

    messages.success(request, f"New OTP sent to your email {user.username.capitalize()}.")
    return redirect('verify_otp', user_id=user.id)

def verified_view(request):
    return render(request, 'accounts/verified.html')

@ensure_csrf_cookie
def login_view(request):

    # If already logged in
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method == 'POST':

        email_or_username = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email_or_username or not password:
            messages.error(request, "Please enter both email/username and password.")
            return redirect('login')

        user_obj = User.objects.filter(email__iexact=email_or_username).first()
        if not user_obj:
            user_obj = User.objects.filter(username__iexact=email_or_username).first()

        if not user_obj:
            messages.error(request, "User does not exist.")
            return redirect('login')

        # Try authenticating with the custom USERNAME_FIELD first, then fall back
        # to the username field if needed. This handles custom email-based users
        # and users who enter either email or username.
        user = authenticate(request, username=user_obj.email, password=password)
        if user is None and user_obj.username and user_obj.username != user_obj.email:
            user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

        if not user.is_email_verified:
            messages.error(request, f"Please verify your email {user.username.capitalize()} !")
            return redirect('verify_otp', user_id=user_obj.id)

        login(request, user)
        messages.success(request, f"Logged in successfully as {user.username.capitalize()} !")
        return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')

@login_required
def change_password_view(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        # Check old password
        if not user.check_password(old_password):
            messages.error(request, "Your old password is incorrect.")
            return redirect("change_password")

        # Check new password match
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
            return redirect("change_password")

        # Update password
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)

        messages.success(request, "Your password has been changed successfully.")
        return redirect("home")

    return render(request, "accounts/change_password.html")
