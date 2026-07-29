from django.db import models
from django.conf import settings

# Create your models here.
# attendance/models.py

class Holiday(models.Model):
    HOLIDAY_TYPE_CHOICES = (
        ('Festival', 'Festival'),
        ('Government Holiday', 'Government Holiday'),
        ('National Holiday', 'National Holiday'),
        ('Regional Holiday', 'Regional Holiday'),
        ('Optional Holiday', 'Optional Holiday'),
        ('Other', 'Other'),
    )

    date = models.DateField(unique=True)
    holiday_type = models.CharField(max_length=50, choices=HOLIDAY_TYPE_CHOICES)
    custom_type = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Used when holiday_type is 'Other'"
    )
    remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, related_name='holidays_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        label = self.custom_type if self.holiday_type == 'Other' else self.holiday_type
        return f"{self.date} — {label}"

    def get_display_type(self):
        return self.custom_type if self.holiday_type == 'Other' else self.holiday_type