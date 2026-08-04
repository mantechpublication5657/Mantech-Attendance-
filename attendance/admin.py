from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Attendance
from .models import AttendanceLog


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'employee_name',
        'date',
        'check_in',
        'check_out',
        'status',
        'is_late'
    )

    list_filter = (
        'status',
        'is_late',
        'date'
    )

    search_fields = (
        'employee__username',
        'employee__first_name',
        'employee__last_name',
        'employee__email',
    )

    @admin.display(description='Employee', ordering='employee__first_name')
    def employee_name(self, obj):
        full_name = f"{obj.employee.first_name} {obj.employee.last_name}".strip()
        return full_name or obj.employee.username


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("employee_name", "date", "action", "timestamp")
    list_filter = ("date", "action")
    search_fields = ("employee__username", "employee__first_name", "employee__last_name", "notes")

    @admin.display(description='Employee', ordering='employee__first_name')
    def employee_name(self, obj):
        full_name = f"{obj.employee.first_name} {obj.employee.last_name}".strip()
        return full_name or obj.employee.username
