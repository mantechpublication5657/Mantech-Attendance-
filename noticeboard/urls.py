# urls.py

from django.urls import path
from . import views

urlpatterns = [

    path(
        'notice-dashboard/',
        views.notice_dashboard,
        name='notice_dashboard'
    ),
    # urls.py

    path(
        'notice/<int:notice_id>/',
        views.notice_overview,
        name='notice_overview'
    ),
    # urls.py

path(
    'notice/edit/<int:notice_id>/',
    views.notice_edit,
    name='notice_edit'
),
# urls.py

path(
    'notice/delete/<int:notice_id>/',
    views.notice_delete,
    name='notice_delete'
),
]