# employees/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, AdminControlledData

User = get_user_model()


# --------------------------------------------------
# EMPLOYEE BASIC INFO FORM (Employee-editable)
# --------------------------------------------------
class EmployeeBasicInfoForm(forms.ModelForm):
    """Fields the employee themselves can fill / edit."""

    class Meta:
        model = EmployeeProfile
        fields = [
            'phone',
            'address',
            'profile_picture',
            'gender',
            'date_of_birth',
            'emergency_contact_phone',
            'department',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


# --------------------------------------------------
# ADMIN CONTROLLED FORM (Admin-only fields)
# --------------------------------------------------
class EmployeeAdminForm(forms.ModelForm):
    """Fields only admin / HR can set."""

    class Meta:
        model = AdminControlledData
        fields = [
            'joining_date',
            'designation',
            'role',
        ]
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }


# --------------------------------------------------
# COMBINED ADD EMPLOYEE FORM (used by admin)
# --------------------------------------------------
class AddEmployeeForm(forms.Form):
    """
    A flat form combining user creation + profile + admin data,
    used on the single-page 'Add Employee' view.
    """

    # --- User account ---
    username = forms.CharField(max_length=150,required=True)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150,required=False)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput(), label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput(), label='Confirm Password')

    # --- Basic info ---
    phone = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    gender = forms.ChoiceField(
        choices=[('', '— Select —')] + list(EmployeeProfile.GENDER_CHOICES),
        required=False
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    emergency_contact_phone = forms.CharField(max_length=15, required=False)
    profile_picture = forms.ImageField(required=False)

    # --- Admin-controlled ---
    department = forms.ChoiceField(
        choices=[('', '— Select Department —')] + list(EmployeeProfile._meta.get_field("department").choices),
        required=False
    )
    designation = forms.CharField(max_length=100, required=False)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    role = forms.ChoiceField(
        choices=[('', '— Select Role —')] + list(AdminControlledData._meta.get_field("role").choices),
        required=True
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
