from django.contrib import admin
from .models import Payroll

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "month",
        "year",
        "basic_salary",
        "hra",
        "da",
        "bonus",
        "bonus_remark",
        "deductions",
        "deduction_remark",
        "net_salary",
        "created_at",
        "updated_at",
    )
    list_filter = ("year", "month", "employee")
    search_fields = ("employee__username", "employee__email")
    ordering = ("-year", "-month")

    # Make net_salary read-only (since it's auto-calculated)
    readonly_fields = ("net_salary", "created_at", "updated_at")

    # Automatically calculate salary when saving from admin
    def save_model(self, request, obj, form, change):
        obj.calculate_salary()
        super().save_model(request, obj, form, change)
