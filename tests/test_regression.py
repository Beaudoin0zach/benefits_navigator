"""
Regression Tests - Tripwires for Critical Invariants

These tests ensure that critical architectural decisions are not accidentally reverted.
They should be fast and deterministic.
"""

import pytest
from django.test import Client
from django.urls import reverse, NoReverseMatch


# =============================================================================
# OCR Field Removal Tripwires (Ephemeral OCR Refactor)
# =============================================================================

class TestOCRFieldsRemoved:
    """
    Ensure OCR text fields remain removed from models.

    The Ephemeral OCR Refactor (PR 6) removed these PHI-containing fields:
    - Document.ocr_text
    - DecisionLetterAnalysis.raw_text
    - RatingAnalysis.raw_text

    If any of these fields reappear, it indicates a regression that could
    expose Protected Health Information (PHI).
    """

    def test_document_has_no_ocr_text_field(self):
        """Document model must not have ocr_text field (PHI protection)."""
        from claims.models import Document

        # Check that ocr_text is not a field on the model
        field_names = [f.name for f in Document._meta.get_fields()]
        assert 'ocr_text' not in field_names, (
            "REGRESSION: Document.ocr_text field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor to protect PHI. "
            "Raw OCR text must not be persisted to the database."
        )

    def test_document_has_no_ocr_text_attribute(self):
        """Document instances must not have ocr_text attribute."""
        from claims.models import Document

        # Verify attribute doesn't exist on model class
        assert not hasattr(Document, 'ocr_text'), (
            "REGRESSION: Document.ocr_text attribute exists. "
            "This was removed for PHI protection."
        )

    def test_decision_letter_analysis_has_no_raw_text_field(self):
        """DecisionLetterAnalysis model must not have raw_text field (PHI protection)."""
        from agents.models import DecisionLetterAnalysis

        field_names = [f.name for f in DecisionLetterAnalysis._meta.get_fields()]
        assert 'raw_text' not in field_names, (
            "REGRESSION: DecisionLetterAnalysis.raw_text field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor to protect PHI."
        )

    def test_rating_analysis_has_no_raw_text_field(self):
        """RatingAnalysis model must not have raw_text field (PHI protection)."""
        from agents.models import RatingAnalysis

        field_names = [f.name for f in RatingAnalysis._meta.get_fields()]
        assert 'raw_text' not in field_names, (
            "REGRESSION: RatingAnalysis.raw_text field has reappeared. "
            "This field was removed in the Ephemeral OCR Refactor to protect PHI."
        )

    def test_document_has_ocr_metadata_fields(self):
        """Document model must have OCR metadata fields (observability without PHI)."""
        from claims.models import Document

        field_names = [f.name for f in Document._meta.get_fields()]

        assert 'ocr_length' in field_names, (
            "Document.ocr_length field is missing. "
            "This metadata field is required for observability."
        )
        assert 'ocr_status' in field_names, (
            "Document.ocr_status field is missing. "
            "This metadata field is required for observability."
        )


# =============================================================================
# Route Integrity Tripwires
# =============================================================================

@pytest.mark.django_db
class TestCriticalRouteIntegrity:
    """
    Ensure critical public routes resolve correctly.

    These tests validate that key routes exist and return expected status codes
    under default feature flags. They prevent silent route loss in refactors.
    """

    @pytest.fixture
    def client(self):
        return Client()

    # -------------------------------------------------------------------------
    # Public Routes (should return 200 without authentication)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("url,expected_status", [
        ('/', 200),
        ('/health/', 200),
        ('/exam-prep/', 200),
        ('/exam-prep/rating-calculator/', 200),
        ('/exam-prep/smc-calculator/', 200),
        ('/exam-prep/tdiu-calculator/', 200),
        ('/exam-prep/secondary-conditions/', 200),
        ('/exam-prep/glossary/', 200),
        ('/appeals/', 200),
        ('/appeals/find-your-path/', 200),
        ('/accounts/login/', 200),
        ('/accounts/signup/', 200),
    ])
    def test_public_route_accessible(self, client, url, expected_status):
        """Critical public routes must be accessible without authentication."""
        response = client.get(url)
        assert response.status_code == expected_status, (
            f"Route {url} returned {response.status_code}, expected {expected_status}. "
            f"This route should be publicly accessible."
        )

    # -------------------------------------------------------------------------
    # Protected Routes (should redirect to login without authentication)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("url", [
        '/dashboard/',
        '/journey/',
        '/claims/',
        '/claims/upload/',
        '/claims/decode/',
        '/exam-prep/my-checklists/',
        '/appeals/my-appeals/',
    ])
    def test_protected_route_redirects_anonymous(self, client, url):
        """Protected routes must redirect anonymous users to login."""
        response = client.get(url)
        assert response.status_code in [301, 302], (
            f"Route {url} returned {response.status_code}, expected redirect. "
            f"This protected route should redirect anonymous users."
        )
        assert '/accounts/login/' in response.url or '/login/' in response.url, (
            f"Route {url} redirected to {response.url}, expected login page."
        )

    # -------------------------------------------------------------------------
    # Named URL Patterns (ensure reverse() works)
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("url_name,kwargs", [
        ('home', {}),
        ('claims:document_list', {}),
        ('claims:document_upload', {}),
        ('claims:denial_decoder', {}),
        ('examprep:guide_list', {}),
        ('examprep:rating_calculator', {}),
        ('examprep:smc_calculator', {}),
        ('examprep:tdiu_calculator', {}),
        ('examprep:glossary_list', {}),
        ('examprep:secondary_conditions_hub', {}),
        ('appeals:home', {}),
        ('appeals:decision_tree', {}),
        ('appeals:appeal_list', {}),
    ])
    def test_named_url_resolves(self, url_name, kwargs):
        """Named URL patterns must resolve without error."""
        try:
            url = reverse(url_name, kwargs=kwargs)
            assert url is not None
        except NoReverseMatch as e:
            pytest.fail(
                f"Named URL '{url_name}' failed to resolve: {e}. "
                f"This URL pattern may have been removed or renamed."
            )
