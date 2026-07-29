from .models import AdminNotification
from accounts.permissions import is_admin


def admin_notifications(request):
    """
    Injects unseen notification count into every template context.
    Add 'grievances.context_processors.admin_notifications'
    to TEMPLATES[0]['OPTIONS']['context_processors'] in settings.py
    """
    unseen_count = 0
    if is_admin(request.user):
        unseen_count = AdminNotification.objects.filter(is_seen=False).count()
    return {'admin_unseen_notifications': unseen_count}
