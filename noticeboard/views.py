# views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import NoticeBoard
from .forms import NoticeBoardForm
from accounts.permissions import is_admin


def visible_notices_for(user, base_qs=None):
    """
    Staff/admins see every notice (they manage the board). Everyone else
    only sees notices targeted at 'All Employees' or at their own
    department, matching notice_type against EmployeeProfile.department.
    """
    qs = base_qs if base_qs is not None else NoticeBoard.objects.all()

    if user.is_staff or user.is_superuser:
        return qs

    department = getattr(getattr(user, 'employee_profile', None), 'department', None)

    if department:
        return qs.filter(Q(notice_type='all') | Q(notice_type=department))

    return qs.filter(notice_type='all')


@login_required
def notice_dashboard(request):

    notices = visible_notices_for(request.user)

    form = NoticeBoardForm()

    if request.method == "POST":

        if not is_admin(request.user):
            messages.error(request, "Only admins can create notices.")
            return redirect("notice_dashboard")

        form = NoticeBoardForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Notice created successfully."
            )

            return redirect("notice_dashboard")

    context = {
        "form": form,
        "notices": notices
    }

    return render(
        request,
        "noticeboard/notice_dashboard.html",
        context
    )


@login_required
def notice_overview(request, notice_id):

    notice = get_object_or_404(
        NoticeBoard,
        id=notice_id
    )

    context = {
        "notice": notice
    }

    return render(
        request,
        "noticeboard/notice_overview.html",
        context
    )

# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import NoticeBoard
from .forms import NoticeBoardForm


@login_required
@user_passes_test(is_admin)
def notice_edit(request, notice_id):

    notice = get_object_or_404(
        NoticeBoard,
        id=notice_id
    )

    form = NoticeBoardForm(
        request.POST or None,
        instance=notice
    )

    if request.method == "POST":

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Notice updated successfully."
            )

            return redirect("notice_dashboard")

    context = {
        "form": form,
        "notice": notice
    }

    return render(
        request,
        "noticeboard/notice_edit.html",
        context
    )
# views.py

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .models import NoticeBoard


@login_required
@user_passes_test(is_admin)
def notice_delete(request, notice_id):

    notice = get_object_or_404(
        NoticeBoard,
        id=notice_id
    )

    notice.delete()

    messages.success(
        request,
        "Notice deleted successfully."
    )

    return redirect("notice_dashboard")