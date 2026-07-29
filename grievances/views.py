from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone

from .models import Grievance, GrievanceReply, AdminNotification, GrievanceCategory
from .forms import GrievanceForm, AdminReplyForm


def is_admin(user):
    return user.is_staff or user.is_superuser


# ─────────────────────────────────────────────
#  GRIEVANCE DASHBOARD
# ─────────────────────────────────────────────

@login_required
def grievance_dashboard(request):
    """
    Unified dashboard:
    - Employees see their own stats + recent grievances.
    - Admins see system-wide stats + all pending notifications.
    """
    user = request.user

    if user.is_staff or user.is_superuser:
        # ── Admin stats ──────────────────────────
        all_grievances   = Grievance.objects.select_related('employee').order_by('-created_at')
        total            = all_grievances.count()
        pending_count    = all_grievances.filter(status='pending').count()
        reviewed_count   = all_grievances.filter(status='reviewed').count()
        resolved_count   = all_grievances.filter(status='resolved').count()
        rejected_count   = all_grievances.filter(status='rejected').count()
        unread_count     = all_grievances.filter(is_read_by_admin=False).count()
        unseen_notifs    = AdminNotification.objects.filter(is_seen=False).count()

        # Category breakdown
        category_stats = (
            all_grievances.values('category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        # Attach display label
        cat_map = {k: v for k, v in GrievanceCategory.choices}
        for c in category_stats:
            c['label'] = cat_map.get(c['category'], c['category'])

        recent_grievances = all_grievances[:8]
        notifications     = AdminNotification.objects.select_related(
            'grievance', 'grievance__employee'
        ).filter(is_seen=False).order_by('-created_at')[:5]

        return render(request, 'grievances/grievance_dashboard.html', {
            'is_admin'          : True,
            'total'             : total,
            'pending_count'     : pending_count,
            'reviewed_count'    : reviewed_count,
            'resolved_count'    : resolved_count,
            'rejected_count'    : rejected_count,
            'unread_count'      : unread_count,
            'unseen_notifs'     : unseen_notifs,
            'category_stats'    : category_stats,
            'recent_grievances' : recent_grievances,
            'notifications'     : notifications,
            'page_title'        : 'Grievance Dashboard',
        })

    else:
        # ── Employee stats ───────────────────────
        my_grievances  = Grievance.objects.filter(employee=user).order_by('-created_at')
        total          = my_grievances.count()
        pending_count  = my_grievances.filter(status='pending').count()
        reviewed_count = my_grievances.filter(status='reviewed').count()
        resolved_count = my_grievances.filter(status='resolved').count()
        rejected_count = my_grievances.filter(status='rejected').count()
        replied_count  = sum(1 for g in my_grievances if g.has_admin_reply)
        recent         = my_grievances[:6]

        return render(request, 'grievances/grievance_dashboard.html', {
            'is_admin'      : False,
            'total'         : total,
            'pending_count' : pending_count,
            'reviewed_count': reviewed_count,
            'resolved_count': resolved_count,
            'rejected_count': rejected_count,
            'replied_count' : replied_count,
            'my_grievances' : recent,
            'page_title'    : 'My Grievance Dashboard',
        })


# ─────────────────────────────────────────────
#  EMPLOYEE VIEWS
# ─────────────────────────────────────────────

@login_required
def employee_grievance_list(request):
    """Employee sees their own grievances."""
    grievances = Grievance.objects.filter(employee=request.user)
    return render(request, 'grievances/employee_list.html', {
        'grievances': grievances,
        'page_title': 'My Applications & Issues',
    })


@login_required
def grievance_create(request):
    """Employee submits a new grievance."""
    if request.method == 'POST':
        form = GrievanceForm(request.POST)
        if form.is_valid():
            grievance = form.save(commit=False)
            grievance.employee = request.user
            grievance.save()

            # Create admin notification
            AdminNotification.objects.create(grievance=grievance)

            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('grievance_list')
    else:
        form = GrievanceForm()

    return render(request, 'grievances/grievance_form.html', {
        'form': form,
        'action': 'Submit',
        'page_title': 'New Application / Issue',
    })


@login_required
def grievance_edit(request, pk):
    """Employee edits their own grievance (only if pending)."""
    grievance = get_object_or_404(Grievance, pk=pk, employee=request.user)

    if grievance.status != 'pending':
        messages.warning(request, 'You can only edit applications that are still pending.')
        return redirect('grievance_list')

    if request.method == 'POST':
        form = GrievanceForm(request.POST, instance=grievance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your application has been updated.')
            return redirect('grievance_list')
    else:
        form = GrievanceForm(instance=grievance)

    return render(request, 'grievances/grievance_form.html', {
        'form': form,
        'grievance': grievance,
        'action': 'Update',
        'page_title': 'Edit Application',
    })


@login_required
def grievance_delete(request, pk):
    """Employee deletes their own grievance (only if pending)."""
    grievance = get_object_or_404(Grievance, pk=pk, employee=request.user)

    if grievance.status != 'pending':
        messages.warning(request, 'You can only delete applications that are still pending.')
        return redirect('grievance_list')

    if request.method == 'POST':
        grievance.delete()
        messages.success(request, 'Application deleted successfully.')
        return redirect('grievance_list')

    return render(request, 'grievances/grievance_confirm_delete.html', {
        'grievance': grievance,
        'page_title': 'Delete Application',
    })


@login_required
def grievance_detail_employee(request, pk):
    """Employee views detail + replies on their own grievance."""
    grievance = get_object_or_404(Grievance, pk=pk, employee=request.user)
    replies = grievance.replies.all()
    return render(request, 'grievances/employee_detail.html', {
        'grievance': grievance,
        'replies': replies,
        'page_title': 'Application Detail',
    })


# ─────────────────────────────────────────────
#  ADMIN VIEWS
# ─────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_notification_list(request):
    """Admin dashboard notification panel."""
    notifications = AdminNotification.objects.select_related(
        'grievance', 'grievance__employee'
    ).order_by('-created_at')

    unseen_count = notifications.filter(is_seen=False).count()

    return render(request, 'grievances/admin_notifications.html', {
        'notifications': notifications,
        'unseen_count': unseen_count,
        'page_title': 'Employee Grievance Notifications',
    })


@login_required
@user_passes_test(is_admin)
def admin_grievance_detail(request, pk):
    """Admin views grievance detail and can reply via email."""
    grievance = get_object_or_404(Grievance, pk=pk)

    # Mark notification as seen
    if hasattr(grievance, 'notification'):
        grievance.notification.is_seen = True
        grievance.notification.save()

    # Mark as read by admin
    grievance.is_read_by_admin = True
    grievance.save(update_fields=['is_read_by_admin'])

    replies = grievance.replies.all()
    reply_form = AdminReplyForm()

    if request.method == 'POST':
        reply_form = AdminReplyForm(request.POST)
        new_status = request.POST.get('status')

        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.grievance = grievance
            reply.replied_by = request.user
            reply.replied_by_admin = True

            # Send email to employee
            employee_email = grievance.employee.email
            email_sent = False

            if employee_email:
                try:
                    host_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@mantech.com')
                    send_mail(
                        subject=f'[Mantech HRMS] Reply to your application: {grievance.subject}',
                        message=f"""Dear {grievance.employee.get_full_name() or grievance.employee.username},

Your application has received a response from the HR/Admin team.

--- Your Application ---
Category : {grievance.get_category_display()}
Subject  : {grievance.subject}
Status   : {new_status.title() if new_status else grievance.get_status_display()}

--- Admin Reply ---
{reply.message}

---
Please log in to the Mantech HRMS portal to view the full conversation.

Regards,
Mantech HR Team
""",
                        from_email=host_email,
                        recipient_list=[employee_email],
                        fail_silently=False,
                    )
                    email_sent = True
                except Exception as e:
                    messages.warning(request, f'Reply saved but email could not be sent: {str(e)}')

            reply.email_sent = email_sent
            reply.save()

            # Update grievance status if changed
            if new_status and new_status in ['pending', 'reviewed', 'resolved', 'rejected']:
                grievance.status = new_status
                grievance.save(update_fields=['status'])

            if email_sent:
                messages.success(request, f'Reply sent and email delivered to {employee_email}.')
            else:
                messages.success(request, 'Reply saved. (No email address found for employee.)')

            return redirect('admin_grievance_detail', pk=pk)

    return render(request, 'grievances/admin_detail.html', {
        'grievance': grievance,
        'replies': replies,
        'reply_form': reply_form,
        'page_title': f'Grievance #{grievance.id} — {grievance.subject}',
    })


@login_required
@user_passes_test(is_admin)
def admin_mark_all_seen(request):
    """AJAX endpoint to mark all notifications as seen."""
    if request.method == 'POST':
        AdminNotification.objects.filter(is_seen=False).update(is_seen=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
@user_passes_test(is_admin)
def admin_unseen_count(request):
    """AJAX endpoint for live notification badge count."""
    count = AdminNotification.objects.filter(is_seen=False).count()
    return JsonResponse({'count': count})