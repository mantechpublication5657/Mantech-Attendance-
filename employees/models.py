# employees/models.py
from django.db import models
from django.conf import settings

# -----------------------------
# Department Choices
# -----------------------------
DEPARTMENT_CHOICES = (
    ('hr', 'Human Resources'),
    ('finance', 'Finance'),
    ('it', 'Information Technology'),
    ('sales', 'Sales'),
    ('marketing', 'Marketing'),
    ('operations', 'Operations'),
    ('admin', 'Administration'),
    ('accountant', 'Accountant'),
    ('positive_vibes', 'Positive Vibes Department'),
    ('computer_operator', 'Computer Operator'),
)

# -----------------------------
# Employee Profile Model
# -----------------------------
class EmployeeProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )

    emp_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False
    )

    department = models.CharField(
        max_length=50,
        choices=DEPARTMENT_CHOICES,
        null=True,
        blank=True
    )

    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='employee_photos/', null=True, blank=True)
    avatar_name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        if self.avatar_name:
            from django.templatetags.static import static
            return static(f'icons/{self.avatar_name}')
        return None

    def __str__(self):
        return f"{self.emp_id or 'NoID'} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'



# -----------------------------
# Admin Controlled Data Model
# -----------------------------
ROLE_CHOICES = (
    ('employee', 'Employee'),
    ('manager', 'Manager'),
    ('admin', 'Admin'),
    ('hr', 'HR'),
)

class AdminControlledData(models.Model):
    profile = models.OneToOneField(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name="admin_data"
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='employee')
    joining_date = models.DateField(null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep Django's is_staff flag (the flag every permission check in the
        # app actually relies on) in sync with the HR-facing role field.
        # 'manager' intentionally does NOT grant is_staff, since is_staff also
        # gates the Django admin site (/administration/) and manager is a
        # reporting-line concept, not an admin-access one.
        user = self.profile.user
        should_be_staff = self.role in ('admin', 'hr')
        if user.is_staff != should_be_staff:
            user.is_staff = should_be_staff
            user.save(update_fields=['is_staff'])


# -----------------------------
# Media Blob (DB-backed file storage)
# -----------------------------
class MediaBlob(models.Model):
    """
    Backs DatabaseStorage (employees/storage.py). Uploaded files are
    stored as rows here instead of on disk, so they survive redeploys
    on hosts (like Render's free tier) whose filesystem is wiped on
    every deploy — the database itself is the persistent part.
    """
    name = models.CharField(max_length=255, unique=True, db_index=True)
    content = models.BinaryField()
    content_type = models.CharField(max_length=100, default='application/octet-stream')
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def __str__(self):
        return f"{self.profile.emp_id} - {self.role} - {self.designation or 'No Designation'}"
