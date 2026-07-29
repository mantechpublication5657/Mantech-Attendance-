from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Attendance
from .models import AttendanceLog


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        'employee',
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
    )
    

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "action", "timestamp")
    list_filter = ("date", "action")
    search_fields = ("employee__username", "notes")
