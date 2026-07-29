# from django.contrib import admin
# from .models import Grievance, GrievanceReply, AdminNotification


# class GrievanceReplyInline(admin.TabularInline):
#     model = GrievanceReply
#     extra = 0
#     readonly_fields = ('replied_by', 'replied_by_admin', 'email_sent', 'created_at')


# @admin.register(Grievance)
# class GrievanceAdmin(admin.ModelAdmin):
#     list_display = ('id', 'employee', 'category', 'subject', 'status', 'is_read_by_admin', 'created_at')
#     list_filter = ('status', 'category', 'is_read_by_admin')
#     search_fields = ('subject', 'message', 'employee__username', 'employee__email')
#     readonly_fields = ('created_at', 'updated_at')
#     inlines = [GrievanceReplyInline]
#     ordering = ('-created_at',)


# @admin.register(AdminNotification)
# class AdminNotificationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'grievance', 'is_seen', 'created_at')
#     list_filter = ('is_seen',)
#     ordering = ('-created_at',)


from django.contrib import admin

from .models import (
    Grievance,
    GrievanceReply,
    AdminNotification
)


class GrievanceReplyInline(admin.TabularInline):

    model = GrievanceReply

    extra = 1

    # Hide replied_by field from admin
    exclude = ('replied_by',)


@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'employee',
        'category',
        'status',
        'created_at'
    )

    list_filter = (
        'category',
        'status'
    )

    search_fields = (
        'subject',
        'employee__username'
    )

    inlines = [GrievanceReplyInline]

    def save_formset(
        self,
        request,
        form,
        formset,
        change
    ):

        instances = formset.save(commit=False)

        for instance in instances:

            # Auto assign logged-in admin
            if not instance.replied_by_id:

                instance.replied_by = request.user

            # Mark as admin reply
            instance.replied_by_admin = True

            instance.save()

        formset.save_m2m()


@admin.register(GrievanceReply)
class GrievanceReplyAdmin(admin.ModelAdmin):

    list_display = (
        'grievance',
        'replied_by',
        'replied_by_admin',
        'created_at'
    )


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):

    list_display = (
        'grievance',
        'is_seen',
        'created_at'
    )