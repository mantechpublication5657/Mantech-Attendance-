import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from django.contrib.auth import authenticate

def reset_employee_password(email_or_username, new_password):
    """Reset password for an employee"""
    
    # Find user
    user = User.objects.filter(email__iexact=email_or_username).first()
    if not user:
        user = User.objects.filter(username__iexact=email_or_username).first()
    
    if not user:
        print(f"✗ Error: User '{email_or_username}' not found!")
        return False
    
    # Check if user is an employee
    if not hasattr(user, 'employee_profile') or user.employee_profile is None:
        print(f"✗ Error: User '{user.username}' is not an employee!")
        return False
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    # Verify password works
    test_user = authenticate(username=user.email, password=new_password)
    if test_user:
        print(f"✓ Password reset successfully!")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Employee ID: {user.employee_profile.emp_id}")
        print(f"  New Password: {new_password}")
        return True
    else:
        print(f"✗ Error: Password reset failed (authentication test failed)!")
        return False

def list_all_employees():
    """List all employees"""
    from employees.models import EmployeeProfile
    
    employees = EmployeeProfile.objects.all().select_related('user')
    if not employees.exists():
        print("No employees found!")
        return
    
    print("\nAvailable Employees:")
    print("-" * 60)
    for e in employees:
        print(f"  • {e.user.username:20} ({e.user.email:30}) - {e.emp_id}")
    print("-" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\n" + "=" * 60)
        print("EMPLOYEE PASSWORD RESET TOOL")
        print("=" * 60)
        print("\nUsage:")
        print("  python reset_password.py <email_or_username> <new_password>")
        print("\nExample:")
        print("  python reset_password.py admin admin123")
        print("  python reset_password.py admin@gmail.com MyNewPassword123")
        print("\n" + "=" * 60)
        
        list_all_employees()
    else:
        email_or_username = sys.argv[1]
        new_password = sys.argv[2]
        reset_employee_password(email_or_username, new_password)
