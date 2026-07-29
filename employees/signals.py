from django.db.models.signals import pre_save
from django.dispatch import receiver
from datetime import datetime
from .models import EmployeeProfile


@receiver(pre_save, sender=EmployeeProfile)
def generate_emp_id(sender, instance, **kwargs):
    if instance.emp_id:
        return

    year = datetime.now().year
    prefix = "EMP"

    last_emp = EmployeeProfile.objects.filter(
        emp_id__startswith=f"{prefix}-{year}"
    ).order_by("emp_id").last()

    if last_emp and last_emp.emp_id:
        last_number = int(last_emp.emp_id.split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    instance.emp_id = f"{prefix}-{year}-{str(next_number).zfill(4)}"