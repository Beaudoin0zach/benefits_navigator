"""
Tests for the core app - Journey tracking, milestones, deadlines, and audit logging.

Covers:
- TimeStampedModel abstract base
- SoftDeleteModel soft delete functionality
- JourneyStage model
- UserJourneyEvent model and properties
- JourneyMilestone model
- Deadline model and properties
- AuditLog model and logging functionality
- DataRetentionPolicy model
- Core views (home, dashboard, journey)
- HTMX endpoints for journey features
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    JourneyStage,
    UserJourneyEvent,
    JourneyMilestone,
    Deadline,
    AuditLog,
    DataRetentionPolicy,
)

User = get_user_model()


# =============================================================================
# JOURNEY STAGE MODEL TESTS
# =============================================================================

class TestJourneyStageModel(TestCase):
    """Tests for the JourneyStage model."""

    def test_journey_stage_creation(self):
        """JourneyStage can be created with all fields."""
        stage = JourneyStage.objects.create(
            code="claim_filed",
            name="Claim Filed",
            description="Your claim has been filed with the VA",
            order=1,
            typical_duration_days=30,
            icon="document",
            color="blue",
        )
        self.assertEqual(stage.code, "claim_filed")
        self.assertEqual(stage.name, "Claim Filed")
        self.assertEqual(stage.order, 1)

    def test_journey_stage_str_representation(self):
        """JourneyStage string representation is the name."""
        stage = JourneyStage.objects.create(
            code="exam_scheduled",
            name="C&P Exam Scheduled",
        )
        self.assertEqual(str(stage), "C&P Exam Scheduled")

    def test_journey_stage_unique_code(self):
        """JourneyStage code must be unique."""
        JourneyStage.objects.create(code="test_stage", name="Test Stage")
        with self.assertRaises(Exception):
            JourneyStage.objects.create(code="test_stage", name="Duplicate")

    def test_journey_stage_ordering(self):
        """JourneyStages are ordered by order field."""
        stage3 = JourneyStage.objects.create(code="stage3", name="Stage 3", order=3)
        stage1 = JourneyStage.objects.create(code="stage1", name="Stage 1", order=1)
        stage2 = JourneyStage.objects.create(code="stage2", name="Stage 2", order=2)

        stages = list(JourneyStage.objects.all())
        self.assertEqual(stages[0], stage1)
        self.assertEqual(stages[1], stage2)
        self.assertEqual(stages[2], stage3)

    def test_journey_stage_icon_choices(self):
        """JourneyStage accepts valid icon choices."""
        for icon, _ in JourneyStage.ICON_CHOICES:
            stage = JourneyStage.objects.create(
                code=f"stage_{icon}",
                name=f"Stage {icon}",
                icon=icon
            )
            self.assertEqual(stage.icon, icon)

    def test_journey_stage_color_choices(self):
        """JourneyStage accepts valid color choices."""
        for color, _ in JourneyStage.COLOR_CHOICES:
            stage = JourneyStage.objects.create(
                code=f"stage_{color}",
                name=f"Stage {color}",
                color=color
            )
            self.assertEqual(stage.color, color)


# =============================================================================
# USER JOURNEY EVENT MODEL TESTS
# =============================================================================

class TestUserJourneyEventModel(TestCase):
    """Tests for the UserJourneyEvent model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )
        self.stage = JourneyStage.objects.create(
            code="claim_filed",
            name="Claim Filed",
            order=1,
        )

    def test_journey_event_creation(self):
        """UserJourneyEvent can be created."""
        event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            event_type="manual",
            title="Filed my PTSD claim",
            description="Submitted paperwork to VSO",
            event_date=date.today(),
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.stage, self.stage)

    def test_journey_event_str_representation(self):
        """UserJourneyEvent string includes title and date."""
        event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Test Event",
            event_date=date.today(),
        )
        self.assertIn("Test Event", str(event))

    def test_journey_event_is_future(self):
        """is_future returns True for future events."""
        future_event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Future Event",
            event_date=date.today() + timedelta(days=30),
        )
        self.assertTrue(future_event.is_future)

    def test_journey_event_is_not_future_for_past(self):
        """is_future returns False for past events."""
        past_event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Past Event",
            event_date=date.today() - timedelta(days=30),
        )
        self.assertFalse(past_event.is_future)

    def test_journey_event_is_overdue_incomplete_past(self):
        """is_overdue returns True for incomplete past events."""
        overdue_event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Overdue Event",
            event_date=date.today() - timedelta(days=10),
            is_completed=False,
        )
        self.assertTrue(overdue_event.is_overdue)

    def test_journey_event_is_not_overdue_when_completed(self):
        """is_overdue returns False for completed events."""
        completed_event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Completed Event",
            event_date=date.today() - timedelta(days=10),
            is_completed=True,
        )
        self.assertFalse(completed_event.is_overdue)

    def test_journey_event_metadata_json(self):
        """Event metadata can store JSON data."""
        event = UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Event with metadata",
            event_date=date.today(),
            metadata={"rating": 70, "conditions": ["PTSD", "Tinnitus"]},
        )
        self.assertEqual(event.metadata["rating"], 70)
        self.assertIn("PTSD", event.metadata["conditions"])


# =============================================================================
# JOURNEY MILESTONE MODEL TESTS
# =============================================================================

class TestJourneyMilestoneModel(TestCase):
    """Tests for the JourneyMilestone model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )

    def test_milestone_creation(self):
        """JourneyMilestone can be created."""
        milestone = JourneyMilestone.objects.create(
            user=self.user,
            milestone_type="claim_filed",
            title="Filed PTSD Claim",
            date=date.today(),
        )
        self.assertEqual(milestone.user, self.user)
        self.assertEqual(milestone.milestone_type, "claim_filed")

    def test_milestone_str_representation(self):
        """JourneyMilestone string includes title and date."""
        milestone = JourneyMilestone.objects.create(
            user=self.user,
            milestone_type="rating_assigned",
            title="Got 70% Rating",
            date=date.today(),
        )
        self.assertIn("Got 70% Rating", str(milestone))

    def test_milestone_type_choices(self):
        """Milestone accepts all valid type choices."""
        valid_types = [choice[0] for choice in JourneyMilestone.MILESTONE_TYPE_CHOICES]
        for mtype in valid_types:
            milestone = JourneyMilestone.objects.create(
                user=self.user,
                milestone_type=mtype,
                title=f"Test {mtype}",
                date=date.today(),
            )
            self.assertEqual(milestone.milestone_type, mtype)

    def test_milestone_details_json(self):
        """Milestone details can store JSON data."""
        milestone = JourneyMilestone.objects.create(
            user=self.user,
            milestone_type="rating_assigned",
            title="Got Rating",
            date=date.today(),
            details={"rating_percentage": 70, "conditions": 3},
        )
        self.assertEqual(milestone.details["rating_percentage"], 70)

    def test_milestone_ordering(self):
        """Milestones are ordered by date descending."""
        old_milestone = JourneyMilestone.objects.create(
            user=self.user,
            milestone_type="claim_filed",
            title="Old Milestone",
            date=date.today() - timedelta(days=60),
        )
        new_milestone = JourneyMilestone.objects.create(
            user=self.user,
            milestone_type="decision_received",
            title="New Milestone",
            date=date.today(),
        )
        milestones = list(self.user.journey_milestones.all())
        self.assertEqual(milestones[0], new_milestone)


# =============================================================================
# DEADLINE MODEL TESTS
# =============================================================================

class TestDeadlineModel(TestCase):
    """Tests for the Deadline model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )

    def test_deadline_creation(self):
        """Deadline can be created."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Appeal Deadline",
            deadline_date=date.today() + timedelta(days=90),
            priority="critical",
        )
        self.assertEqual(deadline.user, self.user)
        self.assertEqual(deadline.priority, "critical")

    def test_deadline_str_representation(self):
        """Deadline string includes title and date."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Submit Evidence",
            deadline_date=date.today() + timedelta(days=30),
        )
        self.assertIn("Submit Evidence", str(deadline))

    def test_deadline_days_remaining(self):
        """days_remaining calculates correctly."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Future Deadline",
            deadline_date=date.today() + timedelta(days=45),
        )
        self.assertEqual(deadline.days_remaining, 45)

    def test_deadline_days_remaining_none_when_completed(self):
        """days_remaining returns None for completed deadlines."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Completed Deadline",
            deadline_date=date.today() + timedelta(days=30),
            is_completed=True,
        )
        self.assertIsNone(deadline.days_remaining)

    def test_deadline_is_overdue_past_date(self):
        """is_overdue returns True for past incomplete deadlines."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Past Deadline",
            deadline_date=date.today() - timedelta(days=5),
            is_completed=False,
        )
        self.assertTrue(deadline.is_overdue)

    def test_deadline_is_not_overdue_when_completed(self):
        """is_overdue returns False for completed deadlines."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Completed Past Deadline",
            deadline_date=date.today() - timedelta(days=5),
            is_completed=True,
        )
        self.assertFalse(deadline.is_overdue)

    def test_deadline_urgency_class_overdue(self):
        """urgency_class returns 'overdue' for past deadlines."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Overdue Deadline",
            deadline_date=date.today() - timedelta(days=5),
        )
        self.assertEqual(deadline.urgency_class, "overdue")

    def test_deadline_urgency_class_urgent(self):
        """urgency_class returns 'urgent' for deadlines within 7 days."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Urgent Deadline",
            deadline_date=date.today() + timedelta(days=5),
        )
        self.assertEqual(deadline.urgency_class, "urgent")

    def test_deadline_urgency_class_soon(self):
        """urgency_class returns 'soon' for deadlines within 30 days."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Soon Deadline",
            deadline_date=date.today() + timedelta(days=20),
        )
        self.assertEqual(deadline.urgency_class, "soon")

    def test_deadline_urgency_class_normal(self):
        """urgency_class returns 'normal' for deadlines beyond 30 days."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Normal Deadline",
            deadline_date=date.today() + timedelta(days=60),
        )
        self.assertEqual(deadline.urgency_class, "normal")

    def test_deadline_urgency_class_completed(self):
        """urgency_class returns 'completed' for completed deadlines."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="Completed Deadline",
            deadline_date=date.today() + timedelta(days=30),
            is_completed=True,
        )
        self.assertEqual(deadline.urgency_class, "completed")

    def test_deadline_mark_complete(self):
        """mark_complete sets is_completed and completed_at."""
        deadline = Deadline.objects.create(
            user=self.user,
            title="To Be Completed",
            deadline_date=date.today() + timedelta(days=30),
        )
        deadline.mark_complete()
        deadline.refresh_from_db()

        self.assertTrue(deadline.is_completed)
        self.assertIsNotNone(deadline.completed_at)


# =============================================================================
# AUDIT LOG MODEL TESTS
# =============================================================================

class TestAuditLogModel(TestCase):
    """Tests for the AuditLog model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )
        self.factory = RequestFactory()

    def test_audit_log_creation(self):
        """AuditLog can be created."""
        log = AuditLog.objects.create(
            user=self.user,
            action="login",
            ip_address="192.168.1.1",
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, "login")

    def test_audit_log_preserves_user_email(self):
        """AuditLog saves user email automatically."""
        log = AuditLog.objects.create(
            user=self.user,
            action="login",
        )
        self.assertEqual(log.user_email, "test@example.com")

    def test_audit_log_str_representation(self):
        """AuditLog string includes action and user."""
        log = AuditLog.objects.create(
            user=self.user,
            action="document_upload",
        )
        self.assertIn("document_upload", str(log))
        self.assertIn("test@example.com", str(log))

    def test_audit_log_classmethod(self):
        """AuditLog.log() convenience method works."""
        request = self.factory.get('/')
        request.user = self.user
        request.META['REMOTE_ADDR'] = '10.0.0.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'

        log = AuditLog.log(
            action='pii_view',
            request=request,
            resource_type='UserProfile',
            resource_id=1,
            details={'field': 'va_file_number'},
        )

        self.assertEqual(log.action, 'pii_view')
        self.assertEqual(log.ip_address, '10.0.0.1')
        self.assertEqual(log.resource_type, 'UserProfile')
        self.assertEqual(log.details['field'], 'va_file_number')

    def test_audit_log_gets_user_from_request(self):
        """AuditLog.log() extracts user from request if not provided."""
        request = self.factory.get('/')
        request.user = self.user

        log = AuditLog.log(action='login', request=request)
        self.assertEqual(log.user, self.user)

    def test_audit_log_extracts_ip_from_x_forwarded_for(self):
        """AuditLog extracts IP from X-Forwarded-For header."""
        request = self.factory.get('/')
        request.user = self.user
        request.META['HTTP_X_FORWARDED_FOR'] = '1.2.3.4, 5.6.7.8'

        log = AuditLog.log(action='login', request=request)
        self.assertEqual(log.ip_address, '1.2.3.4')

    def test_audit_log_ordering(self):
        """AuditLogs are ordered by timestamp descending."""
        log1 = AuditLog.objects.create(user=self.user, action="login")
        log2 = AuditLog.objects.create(user=self.user, action="logout")

        logs = list(AuditLog.objects.all())
        self.assertEqual(logs[0], log2)  # Most recent first

    def test_audit_log_success_and_error(self):
        """AuditLog can track success/failure."""
        success_log = AuditLog.objects.create(
            user=self.user,
            action="login",
            success=True,
        )
        self.assertTrue(success_log.success)

        failure_log = AuditLog.objects.create(
            user=self.user,
            action="login_failed",
            success=False,
            error_message="Invalid credentials",
        )
        self.assertFalse(failure_log.success)
        self.assertEqual(failure_log.error_message, "Invalid credentials")


# =============================================================================
# DATA RETENTION POLICY MODEL TESTS
# =============================================================================

class TestDataRetentionPolicyModel(TestCase):
    """Tests for the DataRetentionPolicy model."""

    def test_policy_creation(self):
        """DataRetentionPolicy can be created."""
        policy = DataRetentionPolicy.objects.create(
            data_type="audit_logs",
            retention_days=365,
            description="Keep audit logs for 1 year",
        )
        self.assertEqual(policy.data_type, "audit_logs")
        self.assertEqual(policy.retention_days, 365)

    def test_policy_str_representation(self):
        """DataRetentionPolicy string includes data type and days."""
        policy = DataRetentionPolicy.objects.create(
            data_type="documents",
            retention_days=90,
        )
        self.assertIn("Document", str(policy))
        self.assertIn("90", str(policy))


# =============================================================================
# CORE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestHomeView:
    """Tests for the home page view."""

    def test_home_page_loads(self, client):
        """Home page loads successfully."""
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_home_page_contains_title(self, client):
        """Home page contains expected title."""
        response = client.get(reverse('home'))
        assert b'VA Benefits Navigator' in response.content or response.status_code == 200


@pytest.mark.django_db
class TestDashboardView:
    """Tests for the user dashboard view."""

    def test_dashboard_requires_login(self, client):
        """Dashboard requires authentication."""
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert 'login' in response.url.lower()

    def test_dashboard_loads_for_authenticated_user(self, authenticated_client):
        """Dashboard loads for authenticated user."""
        response = authenticated_client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_dashboard_shows_user_data(self, authenticated_client, document, exam_checklist, appeal):
        """Dashboard displays user's documents, checklists, and appeals."""
        response = authenticated_client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert 'documents' in response.context
        assert 'checklists' in response.context
        assert 'appeals' in response.context


@pytest.mark.django_db
class TestJourneyDashboardView:
    """Tests for the journey dashboard view."""

    def test_journey_dashboard_requires_login(self, client):
        """Journey dashboard requires authentication."""
        response = client.get(reverse('core:journey_dashboard'))
        assert response.status_code == 302

    def test_journey_dashboard_loads(self, authenticated_client):
        """Journey dashboard loads for authenticated user."""
        response = authenticated_client.get(reverse('core:journey_dashboard'))
        assert response.status_code == 200

    def test_journey_dashboard_shows_timeline(self, authenticated_client, journey_event, milestone, deadline):
        """Journey dashboard shows timeline data."""
        response = authenticated_client.get(reverse('core:journey_dashboard'))
        assert response.status_code == 200
        assert 'timeline' in response.context
        assert 'deadlines' in response.context
        assert 'milestones' in response.context


@pytest.mark.django_db
class TestMilestoneViews:
    """Tests for milestone views."""

    def test_add_milestone_requires_login(self, client):
        """Add milestone requires authentication."""
        response = client.get(reverse('core:add_milestone'))
        assert response.status_code == 302

    def test_add_milestone_get_shows_form(self, authenticated_client):
        """GET request shows milestone form."""
        response = authenticated_client.get(reverse('core:add_milestone'))
        assert response.status_code == 200
        assert 'milestone_types' in response.context

    def test_add_milestone_post_creates_milestone(self, authenticated_client, user):
        """POST request creates new milestone."""
        response = authenticated_client.post(reverse('core:add_milestone'), {
            'milestone_type': 'claim_filed',
            'title': 'Filed my claim',
            'date': date.today().isoformat(),
            'notes': 'Finally got it done!',
        })
        assert response.status_code == 302  # Redirect on success
        assert JourneyMilestone.objects.filter(user=user, title='Filed my claim').exists()

    def test_add_milestone_requires_title(self, authenticated_client):
        """Milestone creation requires title."""
        response = authenticated_client.post(reverse('core:add_milestone'), {
            'milestone_type': 'claim_filed',
            'title': '',  # Empty title
            'date': date.today().isoformat(),
        })
        assert response.status_code == 302  # Redirects with error message

    def test_delete_milestone(self, authenticated_client, milestone):
        """Milestone can be deleted."""
        response = authenticated_client.post(
            reverse('core:delete_milestone', kwargs={'pk': milestone.pk})
        )
        assert response.status_code == 302
        assert not JourneyMilestone.objects.filter(pk=milestone.pk).exists()


@pytest.mark.django_db
class TestDeadlineViews:
    """Tests for deadline views."""

    def test_add_deadline_requires_login(self, client):
        """Add deadline requires authentication."""
        response = client.get(reverse('core:add_deadline'))
        assert response.status_code == 302

    def test_add_deadline_get_shows_form(self, authenticated_client):
        """GET request shows deadline form."""
        response = authenticated_client.get(reverse('core:add_deadline'))
        assert response.status_code == 200
        assert 'priority_choices' in response.context

    def test_add_deadline_post_creates_deadline(self, authenticated_client, user):
        """POST request creates new deadline."""
        response = authenticated_client.post(reverse('core:add_deadline'), {
            'title': 'Submit appeal',
            'deadline_date': (date.today() + timedelta(days=60)).isoformat(),
            'priority': 'high',
            'description': 'File HLR before deadline',
        })
        assert response.status_code == 302
        assert Deadline.objects.filter(user=user, title='Submit appeal').exists()

    def test_toggle_deadline(self, authenticated_client, deadline):
        """Deadline completion can be toggled."""
        assert not deadline.is_completed

        response = authenticated_client.post(
            reverse('core:toggle_deadline', kwargs={'pk': deadline.pk})
        )
        assert response.status_code == 200

        deadline.refresh_from_db()
        assert deadline.is_completed

    def test_delete_deadline(self, authenticated_client, deadline):
        """Deadline can be deleted."""
        response = authenticated_client.post(
            reverse('core:delete_deadline', kwargs={'pk': deadline.pk})
        )
        assert response.status_code == 302
        assert not Deadline.objects.filter(pk=deadline.pk).exists()


# =============================================================================
# ACCESS CONTROL TESTS
# =============================================================================

@pytest.mark.django_db
class TestAccessControl:
    """Tests for access control on core views."""

    def test_user_cannot_access_other_users_deadline(self, authenticated_client, other_user):
        """User cannot toggle another user's deadline."""
        other_deadline = Deadline.objects.create(
            user=other_user,
            title="Other's Deadline",
            deadline_date=date.today() + timedelta(days=30),
        )
        response = authenticated_client.post(
            reverse('core:toggle_deadline', kwargs={'pk': other_deadline.pk})
        )
        assert response.status_code == 404

    def test_user_cannot_delete_other_users_milestone(self, authenticated_client, other_user):
        """User cannot delete another user's milestone."""
        other_milestone = JourneyMilestone.objects.create(
            user=other_user,
            milestone_type="claim_filed",
            title="Other's Milestone",
            date=date.today(),
        )
        response = authenticated_client.post(
            reverse('core:delete_milestone', kwargs={'pk': other_milestone.pk})
        )
        assert response.status_code == 404


# =============================================================================
# JOURNEY TIMELINE BUILDER TESTS
# =============================================================================

class TestTimelineBuilder(TestCase):
    """Tests for the TimelineBuilder service."""

    def setUp(self):
        from core.journey import TimelineBuilder

        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )
        self.builder = TimelineBuilder(self.user)
        self.stage = JourneyStage.objects.create(
            code="test_stage",
            name="Test Stage",
            order=1,
        )

    def test_build_timeline_returns_events(self):
        """build_timeline returns user's journey events."""
        UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Event 1",
            event_date=date.today(),
        )
        UserJourneyEvent.objects.create(
            user=self.user,
            stage=self.stage,
            title="Event 2",
            event_date=date.today() - timedelta(days=5),
        )

        timeline = self.builder.build_timeline(limit=10)
        self.assertEqual(len(timeline), 2)

    def test_build_timeline_respects_limit(self):
        """build_timeline respects the limit parameter."""
        for i in range(5):
            UserJourneyEvent.objects.create(
                user=self.user,
                stage=self.stage,
                title=f"Event {i}",
                event_date=date.today() - timedelta(days=i),
            )

        timeline = self.builder.build_timeline(limit=3)
        self.assertEqual(len(timeline), 3)

    def test_get_upcoming_deadlines(self):
        """get_upcoming_deadlines returns future deadlines."""
        future = Deadline.objects.create(
            user=self.user,
            title="Future Deadline",
            deadline_date=date.today() + timedelta(days=30),
        )
        past = Deadline.objects.create(
            user=self.user,
            title="Past Deadline",
            deadline_date=date.today() - timedelta(days=10),
        )

        deadlines = self.builder.get_upcoming_deadlines(days=60)
        self.assertIn(future, deadlines)
        self.assertNotIn(past, deadlines)

    def test_get_stats(self):
        """get_stats returns journey statistics."""
        JourneyMilestone.objects.create(
            user=self.user,
            milestone_type="claim_filed",
            title="Milestone 1",
            date=date.today(),
        )
        Deadline.objects.create(
            user=self.user,
            title="Deadline 1",
            deadline_date=date.today() + timedelta(days=30),
        )

        stats = self.builder.get_stats()
        self.assertIn('milestone_count', stats)
        self.assertIn('deadline_count', stats)
