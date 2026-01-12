import csv
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import (
    JourneyStage,
    UserJourneyEvent,
    JourneyMilestone,
    Deadline,
    AuditLog,
    DataRetentionPolicy,
    SupportiveMessage,
    Feedback,
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


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'rating_icon', 'category', 'page_title_short',
        'user_display', 'status', 'has_comment'
    ]
    list_filter = ['rating', 'category', 'status', 'created_at']
    search_fields = ['page_url', 'page_title', 'comment', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'created_at', 'updated_at', 'user', 'page_url', 'page_title',
        'rating', 'category', 'comment', 'user_agent', 'session_key'
    ]
    raw_id_fields = ['reviewed_by']
    actions = ['export_to_csv', 'mark_reviewed', 'mark_addressed']

    fieldsets = (
        ('Feedback Details', {
            'fields': ('rating', 'category', 'comment', 'page_url', 'page_title')
        }),
        ('Submitter', {
            'fields': ('user', 'user_agent', 'session_key')
        }),
        ('Admin', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rating_icon(self, obj):
        icons = {
            'positive': '👍',
            'negative': '👎',
            'neutral': '➖',
        }
        return icons.get(obj.rating, '?')
    rating_icon.short_description = 'Rating'

    def page_title_short(self, obj):
        if obj.page_title:
            return obj.page_title[:40] + '...' if len(obj.page_title) > 40 else obj.page_title
        return obj.page_url[:40]
    page_title_short.short_description = 'Page'

    def user_display(self, obj):
        return obj.user.email if obj.user else 'Anonymous'
    user_display.short_description = 'User'

    def has_comment(self, obj):
        return bool(obj.comment)
    has_comment.boolean = True
    has_comment.short_description = 'Comment?'

    @admin.action(description='Export selected feedback to CSV')
    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="feedback_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Date', 'Rating', 'Category', 'Page URL', 'Page Title',
            'Comment', 'User', 'Status', 'Admin Notes'
        ])

        for feedback in queryset:
            writer.writerow([
                feedback.created_at.strftime('%Y-%m-%d %H:%M'),
                feedback.get_rating_display(),
                feedback.get_category_display(),
                feedback.page_url,
                feedback.page_title,
                feedback.comment,
                feedback.user.email if feedback.user else 'Anonymous',
                feedback.get_status_display(),
                feedback.admin_notes,
            ])

        return response

    @admin.action(description='Mark selected as Reviewed')
    def mark_reviewed(self, request, queryset):
        queryset.update(
            status='reviewed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )

    @admin.action(description='Mark selected as Addressed')
    def mark_addressed(self, request, queryset):
        queryset.update(
            status='addressed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
