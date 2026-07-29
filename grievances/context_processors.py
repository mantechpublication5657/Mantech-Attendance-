from .models import AdminNotification


def admin_notifications(request):
    """
    Injects unseen notification count into every template context.
    Add 'grievances.context_processors.admin_notifications'
    to TEMPLATES[0]['OPTIONS']['context_processors'] in settings.py
    """
    unseen_count = 0
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        unseen_count = AdminNotification.objects.filter(is_seen=False).count()
    return {'admin_unseen_notifications': unseen_count}
