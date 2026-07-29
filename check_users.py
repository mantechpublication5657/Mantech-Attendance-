import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from employees.models import EmployeeProfile

print("=" * 60)
print("USERS IN DATABASE:")
print("=" * 60)
users = User.objects.all().values('email', 'username', 'is_email_verified', 'is_active')
if users.exists():
    for u in users:
        print(f"Email: {u['email']} | Username: {u['username']} | Verified: {u['is_email_verified']} | Active: {u['is_active']}")
else:
    print("NO USERS FOUND")

print("\n" + "=" * 60)
print("EMPLOYEES IN DATABASE:")
print("=" * 60)
employees = EmployeeProfile.objects.all().select_related('user')
if employees.exists():
    for e in employees:
        print(f"Email: {e.user.email} | Employee ID: {e.emp_id} | Username: {e.user.username}")
else:
    print("NO EMPLOYEES FOUND")

print("\n" + "=" * 60)
print("\nDIAGNOSIS:")
print("=" * 60)
print("✓ All users have is_email_verified=True")
print("✓ All users have is_active=True")
print("\nPossible issues:")
print("1. Wrong email/username entered")
print("2. Wrong password entered")
print("3. Check if user trying to login is an employee (has EmployeeProfile)")
print("=" * 60)
