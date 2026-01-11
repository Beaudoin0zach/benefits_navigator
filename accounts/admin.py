"""
Django admin configuration for accounts app
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Subscription, NotificationPreferences


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    list_display = ['email', 'first_name', 'last_name', 'is_verified', 'is_premium', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'is_verified', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Stripe', {'fields': ('stripe_customer_id',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile"""
    list_display = ['user', 'branch_of_service', 'disability_rating', 'age']
    list_filter = ['branch_of_service']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin for Subscription"""
    list_display = ['user', 'plan_type', 'status', 'current_period_end', 'cancel_at_period_end']
    list_filter = ['plan_type', 'status', 'cancel_at_period_end']
    search_fields = ['user__email', 'stripe_subscription_id', 'stripe_customer_id']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NotificationPreferences)
class NotificationPreferencesAdmin(admin.ModelAdmin):
    """Admin for NotificationPreferences"""
    list_display = [
        'user', 'email_enabled', 'deadline_reminders', 'exam_reminders',
        'deadline_reminder_days', 'emails_sent_count', 'last_email_sent'
    ]
    list_filter = ['email_enabled', 'deadline_reminders', 'exam_reminders', 'weekly_summary']
    search_fields = ['user__email']
    raw_id_fields = ['user']
    readonly_fields = ['last_email_sent', 'emails_sent_count', 'created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Toggles', {
            'fields': ('email_enabled', 'deadline_reminders', 'exam_reminders', 'claim_updates', 'weekly_summary')
        }),
        ('Timing Preferences', {
            'fields': ('deadline_reminder_days', 'exam_reminder_days')
        }),
        ('Statistics', {
            'fields': ('last_email_sent', 'emails_sent_count'),
            'classes': ('collapse',)
        }),
    )
