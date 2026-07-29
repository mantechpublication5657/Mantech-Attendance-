# views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import NoticeBoard
from .forms import NoticeBoardForm


@login_required
def notice_dashboard(request):

    notices = NoticeBoard.objects.all()

    form = NoticeBoardForm()

    if request.method == "POST":

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
    
# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import NoticeBoard
from .forms import NoticeBoardForm


@login_required
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
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import NoticeBoard


@login_required
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