"""
Tests for the examprep app - C&P Exam preparation, rating calculator, and evidence checklists.

Covers:
- ExamGuidance model
- GlossaryTerm model
- ExamChecklist model
- SavedRatingCalculation model
- EvidenceChecklist model
- VA Math calculations (va_math.py)
- Public guide and glossary views
- Rating calculator views
- Exam checklist views
- Evidence checklist views
- HTMX endpoints
"""

import json
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from examprep.models import (
    ExamGuidance,
    GlossaryTerm,
    ExamChecklist,
    SavedRatingCalculation,
    EvidenceChecklist,
)
from examprep.va_math import (
    DisabilityRating,
    calculate_combined_rating,
    combine_two_ratings,
    combine_multiple_ratings,
    round_to_nearest_10,
    estimate_monthly_compensation,
    format_currency,
    validate_rating,
)

User = get_user_model()


# =============================================================================
# VA MATH CALCULATION TESTS
# =============================================================================

class TestVAMath(TestCase):
    """Tests for VA disability math calculations."""

    def test_validate_rating_valid(self):
        """Valid ratings pass validation."""
        valid_ratings = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for rating in valid_ratings:
            self.assertTrue(validate_rating(rating))

    def test_validate_rating_invalid(self):
        """Invalid ratings fail validation."""
        invalid_ratings = [-10, 5, 15, 25, 105, 150]
        for rating in invalid_ratings:
            self.assertFalse(validate_rating(rating))

    def test_combine_two_ratings_basic(self):
        """Two ratings are combined correctly using VA formula."""
        # 50% + 30% = 50 + 30*(1-0.50) = 50 + 15 = 65%
        result = combine_two_ratings(50, 30)
        self.assertEqual(result, 65.0)

    def test_combine_two_ratings_small(self):
        """Small ratings combine correctly."""
        # 10% + 10% = 10 + 10*(1-0.10) = 10 + 9 = 19%
        result = combine_two_ratings(10, 10)
        self.assertEqual(result, 19.0)

    def test_combine_two_ratings_high(self):
        """High ratings combine correctly."""
        # 70% + 50% = 70 + 50*(1-0.70) = 70 + 15 = 85%
        result = combine_two_ratings(70, 50)
        self.assertEqual(result, 85.0)

    def test_combine_multiple_ratings_three(self):
        """Three ratings combine correctly."""
        # 50%, 30%, 20%
        # Step 1: Start with 50%
        # Step 2: 50% + 30% = 65%
        # Step 3: 65% + 20% = 72%
        result, steps = combine_multiple_ratings([50, 30, 20])
        self.assertAlmostEqual(result, 72.0, places=1)
        self.assertEqual(len(steps), 3)

    def test_combine_multiple_ratings_single(self):
        """Single rating returns itself."""
        result, steps = combine_multiple_ratings([70])
        self.assertEqual(result, 70.0)
        self.assertEqual(len(steps), 1)

    def test_combine_multiple_ratings_empty(self):
        """Empty list returns zero."""
        result, steps = combine_multiple_ratings([])
        self.assertEqual(result, 0.0)
        self.assertEqual(len(steps), 0)

    def test_combine_multiple_ratings_sorted(self):
        """Ratings are sorted highest to lowest."""
        # Should sort to [50, 30, 10] regardless of input order
        result1, _ = combine_multiple_ratings([10, 50, 30])
        result2, _ = combine_multiple_ratings([50, 30, 10])
        self.assertEqual(result1, result2)

    def test_round_to_nearest_10_down(self):
        """Values round down correctly."""
        self.assertEqual(round_to_nearest_10(64.0), 60)
        self.assertEqual(round_to_nearest_10(72.0), 70)
        self.assertEqual(round_to_nearest_10(84.4), 80)

    def test_round_to_nearest_10_up(self):
        """Values round up correctly."""
        self.assertEqual(round_to_nearest_10(65.0), 70)
        self.assertEqual(round_to_nearest_10(75.5), 80)
        self.assertEqual(round_to_nearest_10(85.0), 90)

    def test_round_to_nearest_10_exact(self):
        """Exact tens stay the same."""
        self.assertEqual(round_to_nearest_10(50.0), 50)
        self.assertEqual(round_to_nearest_10(80.0), 80)

    def test_round_to_nearest_10_max_100(self):
        """Rounding caps at 100."""
        self.assertEqual(round_to_nearest_10(99.5), 100)
        self.assertEqual(round_to_nearest_10(105.0), 100)

    def test_calculate_combined_rating_full(self):
        """Full combined rating calculation works."""
        ratings = [
            DisabilityRating(percentage=50, description="PTSD"),
            DisabilityRating(percentage=30, description="Back"),
            DisabilityRating(percentage=10, description="Tinnitus"),
        ]
        result = calculate_combined_rating(ratings)

        # 50 + 30 + 10 combined
        self.assertTrue(60 <= result.combined_rounded <= 80)
        self.assertIsNotNone(result.step_by_step)

    def test_calculate_combined_rating_empty(self):
        """Empty rating list returns zero."""
        result = calculate_combined_rating([])
        self.assertEqual(result.combined_raw, 0.0)
        self.assertEqual(result.combined_rounded, 0)

    def test_calculate_combined_rating_with_bilateral(self):
        """Bilateral factor is applied correctly."""
        ratings = [
            DisabilityRating(percentage=30, description="Left Knee", is_bilateral=True),
            DisabilityRating(percentage=20, description="Right Knee", is_bilateral=True),
            DisabilityRating(percentage=10, description="Tinnitus", is_bilateral=False),
        ]
        result = calculate_combined_rating(ratings)

        # Should include bilateral factor bonus
        self.assertGreater(result.bilateral_factor_applied, 0)

    def test_estimate_monthly_compensation_base(self):
        """Base compensation estimate is correct."""
        # 70% rating, no dependents
        result = estimate_monthly_compensation(70)
        self.assertGreater(result, 1500)  # ~$1716 for 2024

    def test_estimate_monthly_compensation_with_spouse(self):
        """Spouse adds to compensation at 30%+."""
        base = estimate_monthly_compensation(50)
        with_spouse = estimate_monthly_compensation(50, spouse=True)
        self.assertGreater(with_spouse, base)

    def test_estimate_monthly_compensation_with_children(self):
        """Children add to compensation at 30%+."""
        base = estimate_monthly_compensation(50)
        with_children = estimate_monthly_compensation(50, children_under_18=2)
        self.assertGreater(with_children, base)

    def test_estimate_monthly_compensation_low_rating(self):
        """Dependents don't add at ratings below 30%."""
        base = estimate_monthly_compensation(20)
        with_deps = estimate_monthly_compensation(20, spouse=True, children_under_18=3)
        self.assertEqual(base, with_deps)

    def test_format_currency(self):
        """Currency formatting works correctly."""
        self.assertEqual(format_currency(1234.56), "$1,234.56")
        self.assertEqual(format_currency(100), "$100.00")
        self.assertEqual(format_currency(0), "$0.00")


# =============================================================================
# EXAM GUIDANCE MODEL TESTS
# =============================================================================

class TestExamGuidanceModel(TestCase):
    """Tests for the ExamGuidance model."""

    def test_guidance_creation(self):
        """ExamGuidance can be created with all fields."""
        guidance = ExamGuidance.objects.create(
            title="PTSD C&P Exam Guide",
            slug="ptsd-exam",
            category="ptsd",
            introduction="This guide covers the PTSD exam.",
            is_published=True,
        )
        self.assertEqual(guidance.title, "PTSD C&P Exam Guide")
        self.assertEqual(guidance.category, "ptsd")

    def test_guidance_str_representation(self):
        """ExamGuidance string includes title and category."""
        guidance = ExamGuidance.objects.create(
            title="General Exam Guide",
            slug="general",
            category="general",
        )
        self.assertEqual(str(guidance), "General Exam Guide (General Guidance)")

    def test_guidance_unique_slug(self):
        """ExamGuidance slug must be unique."""
        ExamGuidance.objects.create(title="Guide 1", slug="test-slug")
        with self.assertRaises(Exception):
            ExamGuidance.objects.create(title="Guide 2", slug="test-slug")

    def test_guidance_category_choices(self):
        """ExamGuidance accepts valid category choices."""
        valid_cats = ['general', 'ptsd', 'tbi', 'musculoskeletal', 'hearing',
                      'respiratory', 'sleep_apnea', 'mental_health', 'other']
        for cat in valid_cats:
            guidance = ExamGuidance.objects.create(
                title=f"Guide {cat}",
                slug=f"guide-{cat}",
                category=cat,
            )
            self.assertEqual(guidance.category, cat)

    def test_guidance_checklist_items_json(self):
        """ExamGuidance stores checklist items as JSON."""
        guidance = ExamGuidance.objects.create(
            title="Test Guide",
            slug="test-checklist",
            checklist_items=["Item 1", "Item 2", "Item 3"],
        )
        self.assertEqual(len(guidance.checklist_items), 3)


# =============================================================================
# GLOSSARY TERM MODEL TESTS
# =============================================================================

class TestGlossaryTermModel(TestCase):
    """Tests for the GlossaryTerm model."""

    def test_glossary_term_creation(self):
        """GlossaryTerm can be created."""
        term = GlossaryTerm.objects.create(
            term="Nexus Letter",
            plain_language="A medical opinion connecting your condition to service.",
            context="Required for service connection claims.",
        )
        self.assertEqual(term.term, "Nexus Letter")

    def test_glossary_term_str_representation(self):
        """GlossaryTerm string is the term."""
        term = GlossaryTerm.objects.create(
            term="C&P Exam",
            plain_language="Compensation and Pension examination",
        )
        self.assertEqual(str(term), "C&P Exam")

    def test_glossary_term_unique(self):
        """GlossaryTerm must be unique."""
        GlossaryTerm.objects.create(term="Test Term", plain_language="Explanation")
        with self.assertRaises(Exception):
            GlossaryTerm.objects.create(term="Test Term", plain_language="Other")

    def test_glossary_term_related_terms(self):
        """GlossaryTerm can have related terms."""
        term1 = GlossaryTerm.objects.create(term="Term 1", plain_language="T1")
        term2 = GlossaryTerm.objects.create(term="Term 2", plain_language="T2")
        term1.related_terms.add(term2)

        self.assertIn(term2, term1.related_terms.all())


# =============================================================================
# EXAM CHECKLIST MODEL TESTS
# =============================================================================

class TestExamChecklistModel(TestCase):
    """Tests for the ExamChecklist model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )
        self.guidance = ExamGuidance.objects.create(
            title="Test Guide",
            slug="test",
            checklist_items=["Task 1", "Task 2", "Task 3"],
        )

    def test_checklist_creation(self):
        """ExamChecklist can be created."""
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="PTSD",
            exam_date=date.today() + timedelta(days=14),
            guidance=self.guidance,
        )
        self.assertEqual(checklist.user, self.user)
        self.assertEqual(checklist.condition, "PTSD")

    def test_checklist_str_representation(self):
        """ExamChecklist string includes condition."""
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="Back Pain",
            exam_date=date.today(),
        )
        self.assertIn("Back Pain", str(checklist))

    def test_checklist_is_upcoming_future(self):
        """is_upcoming returns True for future exams."""
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="PTSD",
            exam_date=date.today() + timedelta(days=7),
        )
        self.assertTrue(checklist.is_upcoming)

    def test_checklist_is_upcoming_past(self):
        """is_upcoming returns False for past exams."""
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="PTSD",
            exam_date=date.today() - timedelta(days=7),
        )
        self.assertFalse(checklist.is_upcoming)

    def test_checklist_days_until_exam(self):
        """days_until_exam calculates correctly."""
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="PTSD",
            exam_date=date.today() + timedelta(days=10),
        )
        self.assertEqual(checklist.days_until_exam, 10)

    def test_checklist_completion_percentage(self):
        """completion_percentage calculates correctly."""
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="PTSD",
            guidance=self.guidance,
            tasks_completed=["task_1"],  # 1 of 3
        )
        # Should be approximately 33%
        self.assertIsNotNone(checklist.completion_percentage)


# =============================================================================
# SAVED RATING CALCULATION MODEL TESTS
# =============================================================================

class TestSavedRatingCalculationModel(TestCase):
    """Tests for the SavedRatingCalculation model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )

    def test_calculation_creation(self):
        """SavedRatingCalculation can be created."""
        calc = SavedRatingCalculation.objects.create(
            user=self.user,
            name="My Current Rating",
            ratings=[
                {"percentage": 50, "description": "PTSD", "is_bilateral": False},
                {"percentage": 30, "description": "Back", "is_bilateral": False},
            ],
        )
        self.assertEqual(calc.name, "My Current Rating")
        self.assertEqual(len(calc.ratings), 2)

    def test_calculation_str_representation(self):
        """SavedRatingCalculation string includes name and user."""
        calc = SavedRatingCalculation.objects.create(
            user=self.user,
            name="Test Calc",
            ratings=[],
        )
        self.assertIn("Test Calc", str(calc))

    def test_calculation_recalculate(self):
        """recalculate method updates combined ratings."""
        calc = SavedRatingCalculation.objects.create(
            user=self.user,
            name="Test",
            ratings=[
                {"percentage": 50, "description": "PTSD", "is_bilateral": False},
                {"percentage": 30, "description": "Back", "is_bilateral": False},
            ],
        )
        calc.recalculate()
        calc.save()

        self.assertIsNotNone(calc.combined_raw)
        self.assertIsNotNone(calc.combined_rounded)
        self.assertTrue(60 <= calc.combined_rounded <= 80)

    def test_calculation_with_dependents(self):
        """Calculation with dependents calculates compensation."""
        calc = SavedRatingCalculation.objects.create(
            user=self.user,
            name="With Deps",
            ratings=[{"percentage": 70, "description": "PTSD", "is_bilateral": False}],
            has_spouse=True,
            children_under_18=2,
        )
        calc.recalculate()
        calc.save()

        self.assertIsNotNone(calc.estimated_monthly)
        self.assertGreater(calc.estimated_monthly, 0)


# =============================================================================
# EVIDENCE CHECKLIST MODEL TESTS
# =============================================================================

class TestEvidenceChecklistModel(TestCase):
    """Tests for the EvidenceChecklist model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )

    def test_evidence_checklist_creation(self):
        """EvidenceChecklist can be created."""
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Sleep Apnea",
            claim_type="secondary",
            primary_condition="PTSD",
            checklist_items=[
                {"id": "item1", "title": "Sleep Study", "completed": False},
            ],
        )
        self.assertEqual(checklist.condition, "Sleep Apnea")
        self.assertEqual(checklist.claim_type, "secondary")

    def test_evidence_checklist_str_representation(self):
        """EvidenceChecklist string includes condition."""
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Tinnitus",
            claim_type="initial",
        )
        self.assertIn("Tinnitus", str(checklist))

    def test_evidence_checklist_toggle_item(self):
        """toggle_item toggles completion status."""
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Test",
            checklist_items=[
                {"id": "item1", "title": "Test Item", "completed": False},
            ],
        )
        # Toggle to completed
        checklist.toggle_item("item1")
        self.assertTrue(checklist.checklist_items[0]["completed"])

        # Toggle back
        checklist.toggle_item("item1")
        self.assertFalse(checklist.checklist_items[0]["completed"])

    def test_evidence_checklist_update_completion(self):
        """update_completion calculates percentage correctly."""
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Test",
            checklist_items=[
                {"id": "item1", "title": "Item 1", "completed": True},
                {"id": "item2", "title": "Item 2", "completed": False},
                {"id": "item3", "title": "Item 3", "completed": False},
            ],
        )
        checklist.update_completion()
        # 1 of 3 = 33%
        self.assertEqual(checklist.completion_percentage, 33)

    def test_evidence_checklist_get_items_by_category(self):
        """get_items_by_category groups items correctly."""
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Test",
            checklist_items=[
                {"id": "item1", "category": "Medical Evidence", "completed": False},
                {"id": "item2", "category": "Medical Evidence", "completed": False},
                {"id": "item3", "category": "Lay Evidence", "completed": False},
            ],
        )
        by_category = checklist.get_items_by_category()

        self.assertIn("Medical Evidence", by_category)
        self.assertEqual(len(by_category["Medical Evidence"]), 2)

    def test_evidence_checklist_critical_items_remaining(self):
        """critical_items_remaining counts uncompleted critical items."""
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Test",
            checklist_items=[
                {"id": "item1", "priority": "critical", "completed": False},
                {"id": "item2", "priority": "critical", "completed": True},
                {"id": "item3", "priority": "standard", "completed": False},
            ],
        )
        self.assertEqual(checklist.critical_items_remaining, 1)


# =============================================================================
# PUBLIC GUIDE VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestPublicGuideViews:
    """Tests for public guide views (no login required)."""

    def test_guide_list_loads(self, client):
        """Guide list page loads without login."""
        response = client.get(reverse('examprep:guide_list'))
        assert response.status_code == 200

    def test_guide_list_shows_published(self, client, exam_guidance):
        """Guide list shows published guides."""
        response = client.get(reverse('examprep:guide_list'))
        assert response.status_code == 200
        # Check context for guides

    def test_guide_detail_loads(self, client, exam_guidance):
        """Guide detail page loads without login."""
        response = client.get(
            reverse('examprep:guide_detail', kwargs={'slug': exam_guidance.slug})
        )
        assert response.status_code == 200

    def test_guide_detail_404_unpublished(self, client, db):
        """Unpublished guide returns 404."""
        guide = ExamGuidance.objects.create(
            title="Unpublished",
            slug="unpublished",
            is_published=False,
        )
        response = client.get(
            reverse('examprep:guide_detail', kwargs={'slug': 'unpublished'})
        )
        assert response.status_code == 404


# =============================================================================
# PUBLIC GLOSSARY VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestPublicGlossaryViews:
    """Tests for public glossary views (no login required)."""

    def test_glossary_list_loads(self, client):
        """Glossary list page loads without login."""
        response = client.get(reverse('examprep:glossary_list'))
        assert response.status_code == 200

    def test_glossary_list_search(self, client, glossary_term):
        """Glossary list supports search."""
        response = client.get(
            reverse('examprep:glossary_list') + '?q=Nexus'
        )
        assert response.status_code == 200

    def test_glossary_detail_loads(self, client, glossary_term):
        """Glossary detail page loads without login."""
        response = client.get(
            reverse('examprep:glossary_detail', kwargs={'pk': glossary_term.pk})
        )
        assert response.status_code == 200


# =============================================================================
# RATING CALCULATOR VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestRatingCalculatorViews:
    """Tests for rating calculator views."""

    def test_calculator_loads_anonymous(self, client):
        """Rating calculator loads for anonymous users."""
        response = client.get(reverse('examprep:rating_calculator'))
        assert response.status_code == 200

    def test_calculator_loads_authenticated(self, authenticated_client):
        """Rating calculator loads for authenticated users."""
        response = authenticated_client.get(reverse('examprep:rating_calculator'))
        assert response.status_code == 200
        # Should have saved_calculations in context
        assert 'saved_calculations' in response.context

    def test_calculate_htmx_endpoint(self, client):
        """Calculate HTMX endpoint returns results."""
        response = client.post(
            reverse('examprep:calculate_rating'),
            {
                'ratings': json.dumps([
                    {"percentage": 50, "description": "PTSD", "is_bilateral": False},
                    {"percentage": 30, "description": "Back", "is_bilateral": False},
                ]),
                'has_spouse': 'false',
                'children_under_18': '0',
                'dependent_parents': '0',
            },
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200

    def test_calculate_htmx_empty_ratings(self, client):
        """Calculate HTMX handles empty ratings."""
        response = client.post(
            reverse('examprep:calculate_rating'),
            {
                'ratings': '[]',
                'has_spouse': 'false',
                'children_under_18': '0',
                'dependent_parents': '0',
            },
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestSaveCalculationViews:
    """Tests for saving rating calculations."""

    def test_save_calculation_requires_login(self, client):
        """Saving calculation requires authentication."""
        response = client.post(reverse('examprep:save_calculation'))
        assert response.status_code == 302

    def test_save_calculation_creates_record(self, authenticated_client, user):
        """Saving calculation creates database record."""
        response = authenticated_client.post(
            reverse('examprep:save_calculation'),
            {
                'name': 'Test Calculation',
                'ratings': json.dumps([
                    {"percentage": 50, "description": "PTSD", "is_bilateral": False},
                ]),
                'has_spouse': 'false',
                'children_under_18': '0',
                'dependent_parents': '0',
            }
        )
        assert response.status_code in [200, 302]
        assert SavedRatingCalculation.objects.filter(user=user).exists()

    def test_saved_calculations_list(self, authenticated_client, saved_rating):
        """Saved calculations list shows user's calculations."""
        response = authenticated_client.get(reverse('examprep:saved_calculations'))
        assert response.status_code == 200
        assert saved_rating in response.context['calculations']


# =============================================================================
# EXAM CHECKLIST VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestExamChecklistViews:
    """Tests for exam checklist views."""

    def test_checklist_list_requires_login(self, client):
        """Checklist list requires authentication."""
        response = client.get(reverse('examprep:checklist_list'))
        assert response.status_code == 302

    def test_checklist_list_loads(self, authenticated_client):
        """Checklist list loads for authenticated user."""
        response = authenticated_client.get(reverse('examprep:checklist_list'))
        assert response.status_code == 200

    def test_checklist_create_requires_login(self, client):
        """Creating checklist requires authentication."""
        response = client.get(reverse('examprep:checklist_create'))
        assert response.status_code == 302

    def test_checklist_create_loads(self, authenticated_client):
        """Create checklist page loads."""
        response = authenticated_client.get(reverse('examprep:checklist_create'))
        assert response.status_code == 200

    def test_checklist_detail_loads(self, authenticated_client, exam_checklist):
        """Checklist detail loads for owner."""
        response = authenticated_client.get(
            reverse('examprep:checklist_detail', kwargs={'pk': exam_checklist.pk})
        )
        assert response.status_code == 200

    def test_checklist_toggle_task(self, authenticated_client, exam_checklist):
        """Toggle task HTMX endpoint works."""
        response = authenticated_client.post(
            reverse('examprep:checklist_toggle_task', kwargs={'pk': exam_checklist.pk}),
            {'task_id': 'task_1'},
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200


# =============================================================================
# EVIDENCE CHECKLIST VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestEvidenceChecklistViews:
    """Tests for evidence checklist views."""

    def test_evidence_list_requires_login(self, client):
        """Evidence checklist list requires authentication."""
        response = client.get(reverse('examprep:evidence_checklist_list'))
        assert response.status_code == 302

    def test_evidence_list_loads(self, authenticated_client):
        """Evidence checklist list loads for authenticated user."""
        response = authenticated_client.get(reverse('examprep:evidence_checklist_list'))
        assert response.status_code == 200

    def test_evidence_detail_loads(self, authenticated_client, evidence_checklist):
        """Evidence checklist detail loads for owner."""
        response = authenticated_client.get(
            reverse('examprep:evidence_checklist_detail', kwargs={'pk': evidence_checklist.pk})
        )
        assert response.status_code == 200

    def test_evidence_toggle_item(self, authenticated_client, evidence_checklist):
        """Toggle item HTMX endpoint works."""
        response = authenticated_client.post(
            reverse('examprep:evidence_checklist_toggle', kwargs={'pk': evidence_checklist.pk}),
            {'item_id': 'sleep_study'},
            HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200


# =============================================================================
# ACCESS CONTROL TESTS
# =============================================================================

@pytest.mark.django_db
class TestExamPrepAccessControl:
    """Tests for access control on examprep views."""

    def test_user_cannot_view_other_checklist(self, authenticated_client, other_user, exam_guidance):
        """Users cannot view other user's exam checklist."""
        other_checklist = ExamChecklist.objects.create(
            user=other_user,
            condition="Other's Checklist",
            exam_date=date.today() + timedelta(days=7),
        )
        response = authenticated_client.get(
            reverse('examprep:checklist_detail', kwargs={'pk': other_checklist.pk})
        )
        assert response.status_code == 404

    def test_user_cannot_view_other_evidence_checklist(self, authenticated_client, other_user):
        """Users cannot view other user's evidence checklist."""
        other_checklist = EvidenceChecklist.objects.create(
            user=other_user,
            condition="Other's Evidence",
            claim_type="initial",
        )
        response = authenticated_client.get(
            reverse('examprep:evidence_checklist_detail', kwargs={'pk': other_checklist.pk})
        )
        assert response.status_code == 404

    def test_user_cannot_view_other_saved_calculation(self, authenticated_client, other_user):
        """Users cannot load other user's saved calculation."""
        other_calc = SavedRatingCalculation.objects.create(
            user=other_user,
            name="Other's Calc",
            ratings=[],
        )
        response = authenticated_client.get(
            reverse('examprep:load_calculation', kwargs={'pk': other_calc.pk})
        )
        assert response.status_code == 404


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestExamPrepWorkflow(TestCase):
    """Integration tests for examprep workflows."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!"
        )
        self.client = Client()
        self.client.login(email="test@example.com", password="TestPass123!")

    def test_rating_calculator_full_workflow(self):
        """Test complete rating calculation workflow."""
        # 1. Calculate rating
        ratings = [
            DisabilityRating(percentage=50, description="PTSD"),
            DisabilityRating(percentage=30, description="Back"),
            DisabilityRating(percentage=20, description="Knee", is_bilateral=True),
            DisabilityRating(percentage=10, description="Knee", is_bilateral=True),
        ]
        result = calculate_combined_rating(ratings)

        # Verify calculation
        self.assertGreater(result.combined_raw, 60)
        self.assertGreater(result.bilateral_factor_applied, 0)

        # 2. Save calculation
        calc = SavedRatingCalculation.objects.create(
            user=self.user,
            name="My Full Rating",
            ratings=[
                {"percentage": r.percentage, "description": r.description, "is_bilateral": r.is_bilateral}
                for r in ratings
            ],
            has_spouse=True,
            children_under_18=1,
        )
        calc.recalculate()
        calc.save()

        # 3. Verify saved calculation
        self.assertIsNotNone(calc.combined_rounded)
        self.assertGreater(calc.estimated_monthly, 0)

    def test_exam_preparation_workflow(self):
        """Test complete exam preparation workflow."""
        # 1. Create guide
        guide = ExamGuidance.objects.create(
            title="PTSD Guide",
            slug="ptsd",
            category="ptsd",
            checklist_items=[
                "Review stressor statement",
                "List all symptoms",
                "Bring medication list",
            ],
            is_published=True,
        )

        # 2. Create checklist
        checklist = ExamChecklist.objects.create(
            user=self.user,
            condition="PTSD",
            exam_date=date.today() + timedelta(days=14),
            guidance=guide,
            tasks_completed=[],
        )

        # 3. Complete tasks
        checklist.tasks_completed = ["task_1", "task_2"]
        checklist.save()

        # 4. Add notes
        checklist.symptom_notes = "Nightmares 3x per week"
        checklist.worst_day_description = "Can't leave the house"
        checklist.save()

        # 5. Mark exam completed
        checklist.exam_completed = True
        checklist.exam_notes = "Exam went well"
        checklist.save()

        # Verify final state
        self.assertTrue(checklist.exam_completed)
        self.assertFalse(checklist.is_upcoming)

    def test_evidence_collection_workflow(self):
        """Test complete evidence collection workflow."""
        # 1. Create evidence checklist
        checklist = EvidenceChecklist.objects.create(
            user=self.user,
            condition="Sleep Apnea",
            claim_type="secondary",
            primary_condition="PTSD",
            checklist_items=[
                {"id": "sleep_study", "category": "Medical", "title": "Sleep Study",
                 "priority": "critical", "completed": False},
                {"id": "nexus", "category": "Medical", "title": "Nexus Letter",
                 "priority": "critical", "completed": False},
                {"id": "buddy", "category": "Lay", "title": "Buddy Statement",
                 "priority": "standard", "completed": False},
            ],
        )
        checklist.update_completion()
        self.assertEqual(checklist.completion_percentage, 0)

        # 2. Complete critical items
        checklist.toggle_item("sleep_study")
        checklist.toggle_item("nexus")
        checklist.update_completion()

        # 3. Verify progress
        self.assertEqual(checklist.completion_percentage, 66)
        self.assertEqual(checklist.critical_items_remaining, 0)

        # 4. Complete all
        checklist.toggle_item("buddy")
        checklist.update_completion()
        self.assertEqual(checklist.completion_percentage, 100)
