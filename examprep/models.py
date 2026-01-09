"""
Exam Prep app models - C&P Exam preparation content and tracking
"""

from django.db import models
from django.conf import settings
from django.urls import reverse

from core.models import TimeStampedModel


class ExamGuidance(TimeStampedModel):
    """
    C&P Exam preparation guidance content
    Structured content for condition-specific exam preparation
    """

    CATEGORY_CHOICES = [
        ('general', 'General Guidance'),
        ('ptsd', 'PTSD'),
        ('tbi', 'Traumatic Brain Injury'),
        ('musculoskeletal', 'Musculoskeletal (Back, Knee, Shoulder)'),
        ('hearing', 'Hearing Loss / Tinnitus'),
        ('respiratory', 'Respiratory Conditions'),
        ('sleep_apnea', 'Sleep Apnea'),
        ('mental_health', 'Mental Health (non-PTSD)'),
        ('other', 'Other Conditions'),
    ]

    # Basic info
    title = models.CharField('Title', max_length=200)
    slug = models.SlugField('URL slug', unique=True)
    category = models.CharField(
        'Category',
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='general'
    )

    # Structured content sections
    introduction = models.TextField(
        'Introduction',
        help_text='Brief overview of this exam type',
        blank=True
    )
    what_exam_measures = models.TextField(
        'What This Exam Measures',
        help_text='Plain-language explanation of DBQ form',
        blank=True
    )
    physical_tests = models.TextField(
        'Physical Tests Performed',
        help_text='Description of tests examiner will perform',
        blank=True
    )
    questions_to_expect = models.TextField(
        'Questions to Expect',
        help_text='Sample questions examiner may ask',
        blank=True
    )
    preparation_tips = models.TextField(
        'Preparation Tips',
        help_text='How to prepare (before exam)',
        blank=True
    )
    day_of_guidance = models.TextField(
        'Day-of Guidance',
        help_text='What to do on exam day',
        blank=True
    )
    common_mistakes = models.TextField(
        'Common Mistakes',
        help_text='What NOT to do',
        blank=True
    )
    after_exam = models.TextField(
        'After the Exam',
        help_text='What to do post-exam',
        blank=True
    )

    # Checklist items (JSON array of task objects)
    checklist_items = models.JSONField(
        'Checklist Items',
        default=list,
        help_text='Array of preparation tasks',
        blank=True
    )

    # Metadata
    order = models.IntegerField('Display order', default=0)
    is_published = models.BooleanField('Published', default=True)
    meta_description = models.CharField(
        'Meta Description',
        max_length=160,
        blank=True,
        help_text='For SEO'
    )

    class Meta:
        verbose_name = 'Exam Guidance'
        verbose_name_plural = 'Exam Guidance'
        ordering = ['order', 'category', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

    def get_absolute_url(self):
        return reverse('examprep:guide_detail', kwargs={'slug': self.slug})


class GlossaryTerm(TimeStampedModel):
    """
    VA terminology glossary
    Plain-language translations of VA jargon
    """

    term = models.CharField(
        'VA Term',
        max_length=100,
        unique=True,
        help_text='Official VA term or acronym'
    )
    plain_language = models.TextField(
        'Plain Language Definition',
        help_text='Simple explanation anyone can understand'
    )
    context = models.TextField(
        'When/Why This Matters',
        blank=True,
        help_text='Additional context about importance'
    )
    example = models.TextField(
        'Example',
        blank=True,
        help_text='Example usage or scenario'
    )

    # Related terms
    related_terms = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text='Other terms related to this one'
    )

    # Display options
    show_in_tooltips = models.BooleanField(
        'Show in Tooltips',
        default=True,
        help_text='Display as inline tooltip when term appears'
    )
    order = models.IntegerField('Display order', default=0)

    class Meta:
        verbose_name = 'Glossary Term'
        verbose_name_plural = 'Glossary Terms'
        ordering = ['term']

    def __str__(self):
        return self.term


class ExamChecklist(TimeStampedModel):
    """
    User's personalized exam preparation checklist
    Tracks completion of preparation tasks
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exam_checklists'
    )
    condition = models.CharField(
        'Condition',
        max_length=100,
        help_text='Condition for which exam is scheduled'
    )
    exam_date = models.DateField('Exam date', null=True, blank=True)

    # Link to guidance used
    guidance = models.ForeignKey(
        ExamGuidance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Associated exam guidance'
    )

    # Tasks completed (stored as JSON list of task IDs)
    tasks_completed = models.JSONField(
        'Completed tasks',
        default=list,
        help_text='List of task IDs that have been completed'
    )

    # User notes and preparation
    symptom_notes = models.TextField(
        'Symptom Notes',
        blank=True,
        help_text='Notes on symptoms to discuss'
    )
    worst_day_description = models.TextField(
        'Worst Day Description',
        blank=True,
        help_text='Description of worst days with this condition'
    )
    functional_limitations = models.TextField(
        'Functional Limitations',
        blank=True,
        help_text='How condition affects daily life/work'
    )
    questions_for_examiner = models.TextField(
        'Questions for Examiner',
        blank=True
    )

    # Post-exam documentation
    exam_completed = models.BooleanField('Exam Completed', default=False)
    exam_notes = models.TextField(
        'Post-Exam Notes',
        blank=True,
        help_text='What happened during exam'
    )

    # Reminders
    reminder_sent = models.BooleanField('Reminder Sent', default=False)

    class Meta:
        verbose_name = 'Exam Checklist'
        verbose_name_plural = 'Exam Checklists'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.condition} exam for {self.user.email}"

    @property
    def is_upcoming(self):
        """Check if exam is upcoming (within 30 days)"""
        if self.exam_date:
            from datetime import date, timedelta
            today = date.today()
            return today <= self.exam_date <= today + timedelta(days=30)
        return False

    @property
    def days_until_exam(self):
        """Calculate days until exam"""
        if self.exam_date:
            from datetime import date
            delta = self.exam_date - date.today()
            return delta.days
        return None

    @property
    def completion_percentage(self):
        """Calculate checklist completion percentage"""
        if self.guidance and self.guidance.checklist_items:
            total_tasks = len(self.guidance.checklist_items)
            if total_tasks == 0:
                return 0
            completed = len(self.tasks_completed)
            return int((completed / total_tasks) * 100)
        return 0
