from django.db import models

# Create your models here.
# models.py

from django.db import models
from django.utils import timezone


class NoticeBoard(models.Model):

    NOTICE_TYPE_CHOICES = [
        ('all', 'All Employees'),
        ('management', 'Management'),
        ('hr', 'HR Department'),
        ('accounts', 'Accounts Department'),
        ('sales', 'Sales Department'),
        ('editorial', 'Editorial Team'),
        ('intern', 'Interns'),
    ]

    MESSAGE_TYPE_CHOICES = [
        ('general', 'General Notice'),
        ('warning', 'Warning'),
        ('attendance', 'Attendance'),
        ('payroll', 'Payroll'),
        ('holiday', 'Holiday'),
        ('meeting', 'Meeting'),
        ('event', 'Event'),
        ('important', 'Important'),
    ]

    title = models.CharField(max_length=200)

    notice_type = models.CharField(
        max_length=30,
        choices=NOTICE_TYPE_CHOICES,
        default='all'
    )

    message_type = models.CharField(
        max_length=30,
        choices=MESSAGE_TYPE_CHOICES,
        default='general'
    )

    message = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notice Board"
        verbose_name_plural = "Notice Board"

    def __str__(self):
        return f"{self.title} - {self.notice_type}"