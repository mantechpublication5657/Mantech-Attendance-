"""Single source of truth for admin/ownership permission checks used across
the whole project (dashboard, employees, attendance, payroll, leaves,
noticeboard, grievances). Replaces the multiple divergent `is_admin`
helpers that used to be defined independently in each app.
"""
from functools import wraps

from django.core.exceptions import PermissionDenied


def is_admin(user):
    """True for any authenticated staff or superuser account."""
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def is_owner_or_admin(user, target_user_id):
    """True if `user` is an admin, or is the user identified by `target_user_id`."""
    return is_admin(user) or str(user.id) == str(target_user_id)


def owner_or_admin_required(view_func):
    """Decorator for views whose URL takes a `user_id` kwarg identifying the
    resource owner (e.g. attendance/payroll/employee detail pages). Allows
    the owner themselves or any admin; raises PermissionDenied otherwise.
    Must be combined with @login_required (or applied to an already
    login-required view) since it assumes `request.user` is meaningful.
    """
    @wraps(view_func)
    def wrapper(request, user_id, *args, **kwargs):
        if not is_owner_or_admin(request.user, user_id):
            raise PermissionDenied("You do not have access to this resource.")
        return view_func(request, user_id, *args, **kwargs)
    return wrapper
