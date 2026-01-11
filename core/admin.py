from django.contrib import admin
from .models import (
    JourneyStage,
    UserJourneyEvent,
    JourneyMilestone,
    Deadline,
    AuditLog,
    DataRetentionPolicy,
    SupportiveMessage,
)


@admin.register(JourneyStage)
class JourneyStageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'icon', 'color']
    list_filter = ['color', 'icon']
    search_fields = ['code', 'name']
    ordering = ['order']


@admin.register(UserJourneyEvent)
class UserJourneyEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'stage', 'event_date', 'is_completed', 'event_type']
    list_filter = ['is_completed', 'event_type', 'stage']
    search_fields = ['title', 'user__email']
    date_hierarchy = 'event_date'
    raw_id_fields = ['user', 'claim', 'appeal']


@admin.register(JourneyMilestone)
class JourneyMilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'milestone_type', 'date']
    list_filter = ['milestone_type']
    search_fields = ['title', 'user__email']
    date_hierarchy = 'date'
    raw_id_fields = ['user']


@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'deadline_date', 'priority', 'is_completed', 'reminder_sent']
    list_filter = ['priority', 'is_completed', 'reminder_sent']
    search_fields = ['title', 'user__email']
    date_hierarchy = 'deadline_date'
    raw_id_fields = ['user', 'claim', 'appeal']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user_email', 'action', 'resource_type', 'success', 'ip_address']
    list_filter = ['action', 'success', 'resource_type']
    search_fields = ['user_email', 'ip_address', 'request_path']
    date_hierarchy = 'timestamp'
    readonly_fields = [
        'timestamp', 'user', 'user_email', 'action', 'ip_address',
        'user_agent', 'request_path', 'request_method', 'resource_type',
        'resource_id', 'details', 'success', 'error_message'
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ['data_type', 'retention_days', 'is_active', 'last_cleanup']
    list_filter = ['is_active', 'data_type']


@admin.register(SupportiveMessage)
class SupportiveMessageAdmin(admin.ModelAdmin):
    list_display = ['context', 'message_preview', 'tone', 'icon', 'is_active', 'order']
    list_filter = ['context', 'tone', 'is_active']
    search_fields = ['message']
    ordering = ['context', 'order']
    list_editable = ['is_active', 'order']

    fieldsets = (
        (None, {
            'fields': ('context', 'message', 'tone')
        }),
        ('Display', {
            'fields': ('icon', 'order', 'is_active')
        }),
    )

    def message_preview(self, obj):
        return obj.message[:75] + '...' if len(obj.message) > 75 else obj.message
    message_preview.short_description = 'Message'
