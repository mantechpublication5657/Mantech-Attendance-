from django.contrib import admin

# Register your models here.
from .models import User, OTP


admin.site.register(User)
# admin.site.register(OTP)

# admin.site.site_header = "⚡ Mantech HRMS Administration"
# admin.site.site_title = "Mantech HRMS"
# admin.site.index_title = "Manage Employees, Payroll, Attendance & Operations"

admin.site.site_header = "🚀 Mantech Administration"
admin.site.site_title = "Mantech Administration Control"
admin.site.index_title = "Manage Mantech Administration 🛡️"