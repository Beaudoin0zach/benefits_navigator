"""
Regression Tripwires — Fast, deterministic tests for critical invariants.

These tests run under pytest without Playwright, BDD, or external services.
They ensure architectural decisions (OCR field removal, route integrity) are not reverted.

Run with: pytest tests/test_regression_tripwires.py -v
"""

import pytest
from django.urls import reverse, resolve, NoReverseMatch
from django.urls.exceptions import Resolver404


# =============================================================================
# Goal A: Ensure removed OCR/PHI fields cannot reappear in database
# =============================================================================

class TestPHIFieldRemovalInvariants:
    """
    Validates that PHI-containing fields remain removed from database models.

    The Ephemeral OCR Refactor removed these fields to protect PHI:
    - Document.ocr_text (claims app)
    - DecisionLetterAnalysis.raw_text (agents app)
    - RatingAnalysis.raw_text (agents app)

    These tests use Django model _meta to check DATABASE field definitions only.
    We check for fields with a 'column' attribute (actual DB columns), not
    arbitrary Python attributes which could be properties or cached values.
    """

    def _get_db_field_names(self, model_class):
        """Extract database column field names from Django model _meta."""
        return {f.name for f in model_class._meta.get_fields() if hasattr(f, 'column')}

    # -------------------------------------------------------------------------
    # Document.ocr_text removal
    # -------------------------------------------------------------------------

    def test_document_model_has_no_ocr_text_db_field(self):
        """Document must not have ocr_text as a database field."""
        from claims.models import Document

        db_fields = self._get_db_field_names(Document)

        assert 'ocr_text' not in db_fields, (
            "REGRESSION: Document.ocr_text database field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor to protect PHI. "
            "Raw OCR text must not be persisted to the database."
        )

    def test_document_has_required_ocr_metadata_fields(self):
        """Document must have ocr_length and ocr_status for observability."""
        from claims.models import Document

        db_fields = self._get_db_field_names(Document)

        assert 'ocr_length' in db_fields, (
            "Document.ocr_length field is missing. "
            "This metadata field replaced ocr_text for observability without PHI."
        )
        assert 'ocr_status' in db_fields, (
            "Document.ocr_status field is missing. "
            "This metadata field replaced ocr_text for observability without PHI."
        )

    # -------------------------------------------------------------------------
    # DecisionLetterAnalysis.raw_text removal
    # -------------------------------------------------------------------------

    def test_decision_letter_analysis_has_no_raw_text_db_field(self):
        """DecisionLetterAnalysis must not have raw_text as a database field."""
        from agents.models import DecisionLetterAnalysis

        db_fields = self._get_db_field_names(DecisionLetterAnalysis)

        assert 'raw_text' not in db_fields, (
            "REGRESSION: DecisionLetterAnalysis.raw_text database field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor to protect PHI."
        )

    # -------------------------------------------------------------------------
    # RatingAnalysis.raw_text removal
    # -------------------------------------------------------------------------

    def test_rating_analysis_has_no_raw_text_db_field(self):
        """RatingAnalysis must not have raw_text as a database field."""
        from agents.models import RatingAnalysis

        db_fields = self._get_db_field_names(RatingAnalysis)

        assert 'raw_text' not in db_fields, (
            "REGRESSION: RatingAnalysis.raw_text database field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor to protect PHI."
        )


# =============================================================================
# Goal B: URL Resolution Integrity (no DB required)
# =============================================================================

class TestURLResolutionIntegrity:
    """
    Validates that named URLs resolve and paths map to views.

    These tests use Django's URL resolver only - no HTTP requests, no DB access.
    They prevent silent route loss from URL configuration changes.
    """

    # -------------------------------------------------------------------------
    # Named URL patterns must resolve
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("url_name,kwargs", [
        # Core routes
        ("home", {}),
        ("health_check", {}),
        # Claims routes
        ("claims:document_list", {}),
        ("claims:document_upload", {}),
        ("claims:denial_decoder", {}),
        # Agent routes
        ("agents:home", {}),
        ("agents:decision_analyzer", {}),
        ("agents:evidence_gap", {}),
        ("agents:statement_generator", {}),
        # Exam prep routes
        ("examprep:guide_list", {}),
        ("examprep:rating_calculator", {}),
        ("examprep:smc_calculator", {}),
        ("examprep:tdiu_calculator", {}),
        ("examprep:glossary_list", {}),
        ("examprep:secondary_conditions_hub", {}),
        # Appeals routes
        ("appeals:home", {}),
        ("appeals:decision_tree", {}),
        # VSO routes
        ("vso:dashboard", {}),
        # Auth routes
        ("account_login", {}),
        ("account_signup", {}),
    ])
    def test_named_url_resolves(self, url_name, kwargs):
        """Named URLs must resolve without NoReverseMatch error."""
        try:
            url = reverse(url_name, kwargs=kwargs)
            assert url is not None and url != ""
        except NoReverseMatch as e:
            pytest.fail(
                f"Named URL '{url_name}' failed to resolve: {e}. "
                f"This URL pattern may have been removed or renamed."
            )

    # -------------------------------------------------------------------------
    # Critical paths must resolve to views
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("path", [
        "/",
        "/health/",
        "/claims/",
        "/claims/upload/",
        "/claims/decode/",
        "/agents/",
        "/agents/decision-analyzer/",
        "/agents/evidence-gap/",
        "/agents/statement-generator/",
        "/exam-prep/",
        "/exam-prep/rating-calculator/",
        "/appeals/",
        "/vso/",
        "/accounts/login/",
        "/accounts/signup/",
    ])
    def test_path_resolves_to_view(self, path):
        """URL paths must resolve to a view function (not raise Resolver404)."""
        try:
            match = resolve(path)
            assert match.func is not None, f"Path '{path}' resolved but has no view function."
        except Resolver404:
            pytest.fail(
                f"Path '{path}' raised Resolver404. "
                f"This route does not exist in URL configuration."
            )


# =============================================================================
# Goal C: Route HTTP Behavior (requires DB for auth checks)
# =============================================================================

@pytest.mark.django_db
class TestRouteHTTPBehavior:
    """
    Validates HTTP response behavior for critical routes.

    Rules:
    - Core public routes (/, /health/) must return 200
    - Auth-required routes must return 302 redirect to login with next= parameter
    - Other public routes should "not 404" (may be monetized later)

    These tests use Django test client and require DB for auth middleware.
    """

    @pytest.fixture
    def client(self):
        """Django test client for anonymous requests."""
        from django.test import Client
        return Client()

    # -------------------------------------------------------------------------
    # Core public routes (must remain 200)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("path", [
        "/",
        "/health/",
        "/accounts/login/",
        "/accounts/signup/",
    ])
    def test_core_public_route_returns_200(self, client, path):
        """Core public routes must return 200 for anonymous users."""
        response = client.get(path)

        assert response.status_code == 200, (
            f"Route '{path}' returned {response.status_code}, expected 200. "
            f"This core route must remain publicly accessible."
        )

    # -------------------------------------------------------------------------
    # Public routes (should not 404, but may be gated in future)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("path", [
        "/exam-prep/",
        "/exam-prep/rating-calculator/",
        "/exam-prep/smc-calculator/",
        "/exam-prep/tdiu-calculator/",
        "/exam-prep/secondary-conditions/",
        "/exam-prep/glossary/",
        "/appeals/",
        "/appeals/find-your-path/",
    ])
    def test_public_route_exists(self, client, path):
        """Public routes must exist (not 404). May return 200 or redirect."""
        response = client.get(path)

        assert response.status_code != 404, (
            f"Route '{path}' returned 404. "
            f"This route should exist. If intentionally removed, update this test."
        )

    # -------------------------------------------------------------------------
    # Auth-required routes (must redirect to login with next=)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("path", [
        "/dashboard/",
        "/journey/",
        "/claims/",
        "/claims/upload/",
        "/claims/decode/",
        "/agents/decision-analyzer/",
        "/agents/evidence-gap/",
        "/agents/statement-generator/",
        "/exam-prep/my-checklists/",
        "/appeals/my-appeals/",
        "/vso/",
    ])
    def test_protected_route_redirects_to_login(self, client, path):
        """
        Protected routes must redirect anonymous users to login.

        Assertions:
        - Response is 302 redirect (not 404 or 200)
        - Redirect URL contains /login/ or /accounts/login/
        - Redirect URL includes next= parameter pointing back to original path
        """
        response = client.get(path)

        # Must be a redirect
        assert response.status_code in (301, 302), (
            f"Route '{path}' returned {response.status_code}, expected 302 redirect. "
            f"Protected routes must redirect anonymous users to login."
        )

        # Get redirect location
        redirect_url = response.get('Location', '')

        # Must redirect to login
        assert '/accounts/login/' in redirect_url or '/login/' in redirect_url, (
            f"Route '{path}' redirected to '{redirect_url}', expected login page."
        )

        # Must include next= parameter
        assert f'next=' in redirect_url, (
            f"Route '{path}' redirect missing next= parameter. "
            f"Got: '{redirect_url}'. Login redirect should preserve original destination."
        )
