# admin.py

from django.contrib import admin
from .models import NoticeBoard


@admin.register(NoticeBoard)
class NoticeBoardAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'notice_type',
        'message_type',
        'is_active',
        'created_at'
    )

    list_filter = (
        'notice_type',
        'message_type',
        'is_active'
    )

    search_fields = (
        'title',
        'message'
    )