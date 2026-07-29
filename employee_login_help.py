import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from employees.models import EmployeeProfile

print("\n" + "=" * 70)
print("EMPLOYEE LOGIN CREDENTIALS - DIAGNOSTIC REPORT")
print("=" * 70)

employees = EmployeeProfile.objects.all().select_related('user')

if employees.exists():
    print(f"\n✓ Found {employees.count()} employees in the system:\n")
    
    for e in employees:
        print(f"  Employee ID: {e.emp_id}")
        print(f"  Name: {e.user.first_name} {e.user.last_name}")
        print(f"  ├─ Email: {e.user.email}")
        print(f"  ├─ Username: {e.user.username}")
        print(f"  ├─ Active: {'✓ Yes' if e.user.is_active else '✗ No'}")
        print(f"  └─ Email Verified: {'✓ Yes' if e.user.is_email_verified else '✗ No (ISSUE!)'}")
        print()
else:
    print("✗ No employees found in the system!")

print("=" * 70)
print("TROUBLESHOOTING GUIDE:")
print("=" * 70)
print("""
If you're getting "Invalid credentials":

1. CHECK THE USERNAME/EMAIL:
   - Use either the USERNAME or EMAIL field (both should work)
   - Usernames and emails are case-insensitive

2. CHECK THE PASSWORD:
   - Make sure you're entering the EXACT password set by admin
   - Passwords ARE case-sensitive
   - Spaces matter!

3. NOT IN EMPLOYEE LIST?
   - If the user isn't in the list above, they don't have an EmployeeProfile
   - Contact admin to add them as an employee
   
4. PASSWORD RESET OPTION:
   - Use the "Forgot Password" link on the login page
   - Or run: python reset_password.py <email>
""")
print("=" * 70)
