# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import User
# from .utils import generate_unique_employee_id

# @receiver(post_save, sender=User)
# def assign_employee_id(sender, instance, created, **kwargs):
#     if created and not instance.employee_id:
#         role_prefix = {
#             "admin": "ADM",
#             "hr": "HR",
#             "employee": "EMP"
#         }.get(instance.role, "EMP")

#         instance.employee_id = generate_unique_employee_id(role_prefix)
#         instance.save()
