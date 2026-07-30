from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

# Register your models here.
from .models import User


class CustomUserCreationForm(UserCreationForm):
    # Django's built-in UserCreationForm hardcodes Meta.model to the
    # default django.contrib.auth.models.User - must repoint it at ours.
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username')


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class UserAdmin(DjangoUserAdmin):
    """Custom User has USERNAME_FIELD='email' plus a few extra fields, so
    Django's default UserAdmin fieldsets (built around username-based login)
    don't apply directly. Without this, `admin.site.register(User)` fell
    back to a plain ModelAdmin, which renders the password field as a bare
    text input - typing a password there saves it as a literal, unhashed
    string, permanently breaking login for that account. Subclassing
    UserAdmin restores the proper add-user flow (password1/password2,
    hashed via set_password) and a read-only hash + "change password" link
    on the edit form, exactly like Django's own User model gets by default.
    """
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    ordering = ['email']
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_staff', 'is_email_verified']
    search_fields = ['email', 'username', 'first_name', 'last_name']

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Email verification', {'fields': ('is_email_verified', 'email_otp', 'otp_last_sent')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


admin.site.register(User, UserAdmin)

# admin.site.site_header = "⚡ Mantech HRMS Administration"
# admin.site.site_title = "Mantech HRMS"
# admin.site.index_title = "Manage Employees, Payroll, Attendance & Operations"

admin.site.site_header = "🚀 Mantech Administration"
admin.site.site_title = "Mantech Administration Control"
admin.site.index_title = "Manage Mantech Administration 🛡️"
