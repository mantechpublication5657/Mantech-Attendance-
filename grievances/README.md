# Mantech HRMS — Employee Grievance & Issue Management Feature

## What This Feature Does

- **Employees** can submit, edit, and delete HR applications/issues (holiday leave, salary, attendance, etc.)
- **Admin dashboard** gets a live notification bell showing unseen grievances
- **Admin** can open any grievance, reply, and the reply is automatically emailed to the employee
- **Employee portal** shows a "Check your email" notice after admin replies

---

## Files in This Package

```
models.py              — Grievance, GrievanceReply, AdminNotification models
forms.py               — GrievanceForm, AdminReplyForm
views.py               — All employee + admin views
urls.py                — URL routing
admin.py               — Django admin registration
context_processors.py  — Injects unseen count into all templates
templates/
  grievances/
    employee_list.html         — Employee: list of their applications
    grievance_form.html        — Employee: create / edit form
    grievance_confirm_delete.html
    employee_detail.html       — Employee: view detail + admin reply notice
    admin_notifications.html   — Admin: notification dashboard
    admin_detail.html          — Admin: detail view + reply form
    _navbar_bell.html          — Snippet: notification bell for navbar
```

---

## Setup Steps

### 1. Add the app to settings.py

```python
INSTALLED_APPS = [
    ...
    'grievances',  # or whatever you name the app folder
]
```

### 2. Add context processor to settings.py

```python
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'grievances.context_processors.admin_notifications',
            ],
        },
    },
]
```

### 3. Configure email in settings.py

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'          # or your SMTP host
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your@email.com'     # This is the "host_user_email" used for replies
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

### 4. Include URLs in your main urls.py

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('', include('grievances.urls')),
]
```

### 5. Run migrations

```bash
python manage.py makemigrations grievances
python manage.py migrate
```

### 6. Add notification bell to your navbar in base.html

Inside your `<ul class="navbar-nav">` for staff users:

```html
{% include "grievances/_navbar_bell.html" %}
```

---

## URL Reference

| URL | Name | Who |
|-----|------|-----|
| `/my-applications/` | `grievance_list` | Employee |
| `/my-applications/new/` | `grievance_create` | Employee |
| `/my-applications/<pk>/edit/` | `grievance_edit` | Employee |
| `/my-applications/<pk>/delete/` | `grievance_delete` | Employee |
| `/my-applications/<pk>/` | `grievance_detail` | Employee |
| `/admin/grievances/` | `admin_notifications` | Admin/Staff |
| `/admin/grievances/<pk>/` | `admin_grievance_detail` | Admin/Staff |
| `/admin/grievances/mark-all-seen/` | `admin_mark_all_seen` | Admin/Staff (AJAX) |
| `/admin/grievances/unseen-count/` | `admin_unseen_count` | Admin/Staff (AJAX) |

---

## How the Email Flow Works

1. Employee submits a grievance → `AdminNotification` is created
2. Admin sees notification bell update (polls every 30 seconds)
3. Admin opens the grievance, types a reply, clicks **Send Reply & Email**
4. Django sends email via `EMAIL_HOST_USER` to `employee.email`
5. `GrievanceReply.email_sent = True` is saved
6. Employee opens their grievance detail → sees green "Check your email" notice

---

## Issue Categories Available

- Holiday Leave
- Casual Leave
- Sick Leave
- Salary Issue
- Attendance
- Policy Concern
- Other
