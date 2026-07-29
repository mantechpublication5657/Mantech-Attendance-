# employees/admin.py
from django.contrib import admin
from .models import EmployeeProfile, AdminControlledData


# -----------------------------
# ADMIN CONTROLLED DATA INLINE
# -----------------------------
class AdminControlledDataInline(admin.StackedInline):
    model = AdminControlledData
    extra = 0


# -----------------------------
# EMPLOYEE PROFILE ADMIN
# -----------------------------
@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):

    list_display = (
        'emp_id',
        'username',
        'email',
        'department',
        'designation',
        'role',
        'joining_date',
    )

    search_fields = (
        'emp_id',
        'user__username',
        'user__email',
    )

    list_filter = (
        'department',
        'admin_data__designation',
        'admin_data__role',
    )

    inlines = [AdminControlledDataInline]

    list_select_related = ('user', 'admin_data')

    # ------------------------
    # DISPLAY METHODS
    # ------------------------

    def emp_id(self, obj):
        return obj.emp_id or "-"
    emp_id.admin_order_field = 'emp_id'
    emp_id.short_description = 'Employee ID'

    def username(self, obj):
        return obj.user.username if obj.user else "-"
    username.admin_order_field = 'user__username'
    username.short_description = 'Username'

    def email(self, obj):
        return obj.user.email if obj.user else "-"
    email.admin_order_field = 'user__email'
    email.short_description = 'Email'

    def department(self, obj):
        return obj.department or "-"
    department.short_description = 'Department'

    def designation(self, obj):
        return getattr(getattr(obj, 'admin_data', None), 'designation', "-")
    designation.short_description = 'Designation'

    def role(self, obj):
        return getattr(getattr(obj, 'admin_data', None), 'role', "-")
    role.short_description = 'Role'

    def joining_date(self, obj):
        return getattr(getattr(obj, 'admin_data', None), 'joining_date', "-")
    joining_date.short_description = 'Joining Date'


# from django.contrib import admin
# from .models import LeaveRecord


# @admin.register(LeaveRecord)
# class LeaveRecordAdmin(admin.ModelAdmin):
#     list_display = (
#         'id',
#         'employee',
#         'leave_type',
#         'days_taken',
#     )

#     list_filter = (
#         'leave_type',
#         'employee',
#     )

#     search_fields = (
#         'employee__user__username',
#         'employee__user__email',
#         'leave_type',
#     )

#     ordering = ('-id',)

#     list_per_page = 25