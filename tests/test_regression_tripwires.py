"""
Regression Tripwires — Fast, deterministic tests for critical invariants.

These tests run under pytest without Playwright, BDD, or external services.
They ensure architectural decisions (OCR field removal, route integrity) are not reverted.

Run with: pytest tests/test_regression_tripwires.py -v
"""

import pytest
from django.test import Client


# =============================================================================
# Goal A: Ensure removed OCR fields cannot reappear
# =============================================================================

class TestOCRFieldRemovalTripwires:
    """
    Validates that PHI-containing OCR fields remain removed from models.

    The Ephemeral OCR Refactor removed these fields to protect PHI:
    - Document.ocr_text (claims app)
    - DecisionLetterAnalysis.raw_text (agents app)
    - RatingAnalysis.raw_text (agents app)

    These tests use Django model _meta to check field definitions,
    not just hasattr, ensuring DB field reintroduction triggers failure.
    """

    def _get_model_field_names(self, model_class):
        """Extract field names from Django model _meta (excludes relations by default)."""
        return {f.name for f in model_class._meta.get_fields() if hasattr(f, 'column')}

    def _get_all_field_names(self, model_class):
        """Extract all field names including reverse relations."""
        return {f.name for f in model_class._meta.get_fields()}

    # -------------------------------------------------------------------------
    # Document.ocr_text removal
    # -------------------------------------------------------------------------

    def test_document_model_has_no_ocr_text_db_field(self):
        """Document must not have ocr_text as a database field."""
        from claims.models import Document

        db_fields = self._get_model_field_names(Document)

        assert 'ocr_text' not in db_fields, (
            "REGRESSION: Document.ocr_text database field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor (PR 6) to protect PHI. "
            "Raw OCR text must not be persisted to the database."
        )

    def test_document_model_has_no_ocr_text_in_meta(self):
        """Document._meta must not include ocr_text in any form."""
        from claims.models import Document

        all_fields = self._get_all_field_names(Document)

        assert 'ocr_text' not in all_fields, (
            "REGRESSION: Document.ocr_text found in model _meta.get_fields(). "
            "This field must not exist in any form (DB field, property, or relation)."
        )

    def test_document_has_required_ocr_metadata_fields(self):
        """Document must have ocr_length and ocr_status for observability."""
        from claims.models import Document

        db_fields = self._get_model_field_names(Document)

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

        db_fields = self._get_model_field_names(DecisionLetterAnalysis)

        assert 'raw_text' not in db_fields, (
            "REGRESSION: DecisionLetterAnalysis.raw_text database field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor (PR 6) to protect PHI."
        )

    def test_decision_letter_analysis_has_no_raw_text_in_meta(self):
        """DecisionLetterAnalysis._meta must not include raw_text."""
        from agents.models import DecisionLetterAnalysis

        all_fields = self._get_all_field_names(DecisionLetterAnalysis)

        assert 'raw_text' not in all_fields, (
            "REGRESSION: DecisionLetterAnalysis.raw_text found in model _meta.get_fields()."
        )

    # -------------------------------------------------------------------------
    # RatingAnalysis.raw_text removal
    # -------------------------------------------------------------------------

    def test_rating_analysis_has_no_raw_text_db_field(self):
        """RatingAnalysis must not have raw_text as a database field."""
        from agents.models import RatingAnalysis

        db_fields = self._get_model_field_names(RatingAnalysis)

        assert 'raw_text' not in db_fields, (
            "REGRESSION: RatingAnalysis.raw_text database field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor (PR 6) to protect PHI."
        )

    def test_rating_analysis_has_no_raw_text_in_meta(self):
        """RatingAnalysis._meta must not include raw_text."""
        from agents.models import RatingAnalysis

        all_fields = self._get_all_field_names(RatingAnalysis)

        assert 'raw_text' not in all_fields, (
            "REGRESSION: RatingAnalysis.raw_text found in model _meta.get_fields()."
        )


# =============================================================================
# Goal B: Ensure critical routes resolve under default settings
# =============================================================================

@pytest.mark.django_db
class TestRouteIntegrityTripwires:
    """
    Validates that critical routes exist and return expected status codes.

    Rules:
    - Public routes must return 200
    - Auth-required routes must return 302 redirect to login (not 404)
    - AI-consent-required routes must return 302 redirect (not 404)
    - 404 indicates route was removed or misconfigured

    These tests use Django test client only (no Playwright, no external services).
    """

    @pytest.fixture
    def client(self):
        """Django test client for anonymous requests."""
        return Client()

    # -------------------------------------------------------------------------
    # Public routes (should return 200 without auth)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("path", [
        "/",
        "/health/",
    ])
    def test_public_route_returns_200(self, client, path):
        """Public routes must return 200 for anonymous users."""
        response = client.get(path)

        assert response.status_code == 200, (
            f"Route '{path}' returned {response.status_code}, expected 200. "
            f"Public routes must be accessible without authentication."
        )

    # -------------------------------------------------------------------------
    # Auth-required routes (should return 302 to login, not 404)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("path", [
        "/claims/upload/",
        "/claims/decode/",
        "/agents/decision-analyzer/",
        "/agents/evidence-gap/",
        "/agents/statement-generator/",
        "/vso/",
    ])
    def test_auth_required_route_redirects_not_404(self, client, path):
        """
        Auth-required routes must redirect anonymous users to login.

        A 404 indicates the route was removed or misconfigured.
        A 302/301 redirect to login is expected behavior.
        """
        response = client.get(path)

        # Must NOT be 404 (route missing)
        assert response.status_code != 404, (
            f"Route '{path}' returned 404. "
            f"This route should exist and redirect to login, not return 404."
        )

        # Should be a redirect (302 or 301)
        assert response.status_code in (301, 302), (
            f"Route '{path}' returned {response.status_code}, expected 302 redirect. "
            f"Auth-required routes should redirect anonymous users to login."
        )

        # Should redirect to login page
        redirect_url = response.url if hasattr(response, 'url') else response.get('Location', '')
        assert '/accounts/login/' in redirect_url or '/login/' in redirect_url, (
            f"Route '{path}' redirected to '{redirect_url}', expected login page redirect."
        )

    # -------------------------------------------------------------------------
    # Verify routes exist via Django URL resolver (no HTTP request needed)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("url_name,kwargs", [
        ("home", {}),
        ("health_check", {}),
        ("claims:document_list", {}),
        ("claims:document_upload", {}),
        ("claims:denial_decoder", {}),
        ("agents:home", {}),
        ("agents:decision_analyzer", {}),
        ("agents:evidence_gap", {}),
        ("agents:statement_generator", {}),
        ("vso:dashboard", {}),
    ])
    def test_named_url_resolves(self, url_name, kwargs):
        """Named URLs must resolve without NoReverseMatch error."""
        from django.urls import reverse, NoReverseMatch

        try:
            url = reverse(url_name, kwargs=kwargs)
            assert url is not None and url != ""
        except NoReverseMatch as e:
            pytest.fail(
                f"Named URL '{url_name}' failed to resolve: {e}. "
                f"This URL pattern may have been removed or renamed."
            )

    # -------------------------------------------------------------------------
    # Verify route paths resolve to views (not 404 at resolver level)
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
        "/vso/",
    ])
    def test_path_resolves_to_view(self, path):
        """URL paths must resolve to a view function (not raise Resolver404)."""
        from django.urls import resolve
        from django.urls.exceptions import Resolver404

        try:
            match = resolve(path)
            assert match.func is not None, f"Path '{path}' resolved but has no view function."
        except Resolver404:
            pytest.fail(
                f"Path '{path}' raised Resolver404. "
                f"This route does not exist in URL configuration."
            )
