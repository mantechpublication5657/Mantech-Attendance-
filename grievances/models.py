from django.db import models
from django.conf import settings
from django.utils import timezone


class GrievanceCategory(models.TextChoices):
    HOLIDAY = 'holiday', 'Holiday Leave'
    CASUAL = 'casual', 'Casual Leave'
    SICK = 'sick', 'Sick Leave'
    SALARY = 'salary', 'Salary Issue'
    ATTENDANCE = 'attendance', 'Attendance'
    POLICY = 'policy', 'Policy Concern'
    OTHER = 'other', 'Other'


class GrievanceStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    REVIEWED = 'reviewed', 'Reviewed'
    RESOLVED = 'resolved', 'Resolved'
    REJECTED = 'rejected', 'Rejected'


class Grievance(models.Model):
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grievances'
    )
    category = models.CharField(
        max_length=20,
        choices=GrievanceCategory.choices,
        default=GrievanceCategory.OTHER
    )
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=GrievanceStatus.choices,
        default=GrievanceStatus.PENDING
    )
    is_read_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Grievance'
        verbose_name_plural = 'Grievances'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.subject} — {self.employee.get_full_name() or self.employee.username}"

    @property
    def has_admin_reply(self):
        return self.replies.filter(replied_by_admin=True).exists()


class GrievanceReply(models.Model):
    grievance = models.ForeignKey(
        Grievance,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grievance_replies'
    )
    replied_by_admin = models.BooleanField(default=False)
    message = models.TextField()
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        role = "Admin" if self.replied_by_admin else "Employee"
        return f"{role} reply on Grievance #{self.grievance.id}"


class AdminNotification(models.Model):
    grievance = models.OneToOneField(
        Grievance,
        on_delete=models.CASCADE,
        related_name='notification'
    )
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for Grievance #{self.grievance.id}"