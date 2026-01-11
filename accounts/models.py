"""
Accounts app models - User authentication, profiles, and subscriptions
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import date

from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Set username to email as fallback
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Uses email as the primary identifier instead of username
    """
    email = models.EmailField('Email address', unique=True)
    phone_number = models.CharField('Phone number', max_length=20, blank=True)
    is_verified = models.BooleanField('Email verified', default=False)
    stripe_customer_id = models.CharField('Stripe customer ID', max_length=255, blank=True)

    # Make username optional since we're using email
    username = models.CharField('Username', max_length=150, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Remove email from required fields since it's USERNAME_FIELD

    # Use custom manager
    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    @property
    def is_premium(self):
        """Check if user has an active premium subscription"""
        try:
            return self.subscription.is_active
        except Subscription.DoesNotExist:
            return False

    @property
    def full_name(self):
        """Return user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email


class UserProfile(TimeStampedModel):
    """
    Extended user profile information
    One-to-one relationship with User
    """

    BRANCH_CHOICES = [
        ('army', 'Army'),
        ('navy', 'Navy'),
        ('air_force', 'Air Force'),
        ('marines', 'Marines'),
        ('coast_guard', 'Coast Guard'),
        ('space_force', 'Space Force'),
        ('national_guard', 'National Guard'),
        ('reserves', 'Reserves'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    branch_of_service = models.CharField(
        'Branch of service',
        max_length=20,
        choices=BRANCH_CHOICES,
        blank=True
    )
    date_of_birth = models.DateField('Date of birth', null=True, blank=True)
    va_file_number = models.CharField(
        'VA file number',
        max_length=20,
        blank=True,
        help_text='Optional - Your VA claim number'
    )
    disability_rating = models.IntegerField(
        'Current disability rating (%)',
        null=True,
        blank=True,
        help_text='Your current combined VA disability rating'
    )
    bio = models.TextField('Biography', blank=True, help_text='Optional personal information')

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile for {self.user.email}"

    @property
    def age(self):
        """Calculate user's age"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class Subscription(TimeStampedModel):
    """
    User subscription management
    Tracks Stripe subscription information
    """

    PLAN_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('incomplete', 'Incomplete'),
        ('trialing', 'Trialing'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    stripe_subscription_id = models.CharField(
        'Stripe subscription ID',
        max_length=255,
        blank=True
    )
    stripe_customer_id = models.CharField(
        'Stripe customer ID',
        max_length=255,
        blank=True
    )
    plan_type = models.CharField(
        'Plan type',
        max_length=20,
        choices=PLAN_CHOICES,
        default='free'
    )
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    current_period_end = models.DateTimeField(
        'Current period end',
        null=True,
        blank=True,
        help_text='When the current billing period ends'
    )
    cancel_at_period_end = models.BooleanField(
        'Cancel at period end',
        default=False,
        help_text='Whether subscription is set to cancel at end of current period'
    )
    trial_end = models.DateTimeField(
        'Trial end',
        null=True,
        blank=True,
        help_text='When free trial ends'
    )

    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"{self.user.email} - {self.plan_type} ({self.status})"

    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['active', 'trialing']

    @property
    def is_trial(self):
        """Check if subscription is in trial period"""
        return self.status == 'trialing' and self.trial_end and self.trial_end > timezone.now()

    @property
    def days_until_renewal(self):
        """Calculate days until subscription renews or expires"""
        if self.current_period_end:
            delta = self.current_period_end - timezone.now()
            return delta.days
        return None


class NotificationPreferences(TimeStampedModel):
    """
    User notification preferences for email reminders and alerts.
    """

    REMINDER_TIMING_CHOICES = [
        (30, '30 days before'),
        (14, '14 days before'),
        (7, '7 days before'),
        (3, '3 days before'),
        (1, '1 day before'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # Email notification toggles
    email_enabled = models.BooleanField(
        'Enable email notifications',
        default=True,
        help_text='Master switch for all email notifications'
    )
    deadline_reminders = models.BooleanField(
        'Deadline reminders',
        default=True,
        help_text='Receive reminders about upcoming deadlines'
    )
    exam_reminders = models.BooleanField(
        'C&P exam reminders',
        default=True,
        help_text='Receive reminders about upcoming C&P exams'
    )
    claim_updates = models.BooleanField(
        'Claim status updates',
        default=True,
        help_text='Receive updates about claim status changes'
    )
    weekly_summary = models.BooleanField(
        'Weekly summary',
        default=False,
        help_text='Receive a weekly summary of your claims journey'
    )

    # Timing preferences
    deadline_reminder_days = models.IntegerField(
        'Remind me before deadline',
        choices=REMINDER_TIMING_CHOICES,
        default=7,
        help_text='How many days before a deadline to send reminder'
    )
    exam_reminder_days = models.IntegerField(
        'Remind me before exam',
        choices=REMINDER_TIMING_CHOICES,
        default=7,
        help_text='How many days before a C&P exam to send reminder'
    )

    # Tracking
    last_email_sent = models.DateTimeField(
        'Last email sent',
        null=True,
        blank=True
    )
    emails_sent_count = models.IntegerField(
        'Total emails sent',
        default=0
    )

    class Meta:
        verbose_name = 'Notification Preferences'
        verbose_name_plural = 'Notification Preferences'

    def __str__(self):
        status = 'enabled' if self.email_enabled else 'disabled'
        return f"Notifications for {self.user.email} ({status})"

    def should_send_deadline_reminder(self, days_until_deadline: int) -> bool:
        """Check if a deadline reminder should be sent based on user preferences."""
        if not self.email_enabled or not self.deadline_reminders:
            return False
        return days_until_deadline <= self.deadline_reminder_days

    def should_send_exam_reminder(self, days_until_exam: int) -> bool:
        """Check if an exam reminder should be sent based on user preferences."""
        if not self.email_enabled or not self.exam_reminders:
            return False
        return days_until_exam <= self.exam_reminder_days


# Signal to create user profile automatically when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)
        NotificationPreferences.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile whenever the User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
