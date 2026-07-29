from django.contrib import admin
from .models import Holiday

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'holiday_type', 'custom_type', 'remarks', 'created_by', 'created_at')
    list_filter = ('holiday_type',)
    search_fields = ('remarks', 'custom_type')
    ordering = ('-date',)
    readonly_fields = ('created_by', 'created_at')