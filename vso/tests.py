"""
Tests for VSO app - Organization scoping and access control.

Covers:
- Multi-org user access scoping
- Organization selection for multi-org users
- VSO dashboard and case management permissions
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.models import Organization, OrganizationMembership
from vso.views import (
    get_user_staff_memberships,
    get_user_organization,
    requires_org_selection,
)

User = get_user_model()


# =============================================================================
# MULTI-ORG SCOPING TESTS
# =============================================================================

class TestGetUserStaffMemberships(TestCase):
    """Tests for get_user_staff_memberships function."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="vsostaff@example.com",
            password="TestPass123!"
        )
        self.org1 = Organization.objects.create(
            name="VSO Org 1",
            slug="vso-org-1",
            org_type="vso",
        )
        self.org2 = Organization.objects.create(
            name="VSO Org 2",
            slug="vso-org-2",
            org_type="vso",
        )

    def test_returns_empty_for_unauthenticated(self):
        """Unauthenticated user gets empty queryset."""
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        result = get_user_staff_memberships(anon)
        self.assertEqual(result.count(), 0)

    def test_returns_empty_for_user_with_no_memberships(self):
        """User with no memberships gets empty queryset."""
        result = get_user_staff_memberships(self.user)
        self.assertEqual(result.count(), 0)

    def test_returns_admin_membership(self):
        """Returns membership where user is admin."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        result = get_user_staff_memberships(self.user)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().organization, self.org1)

    def test_returns_caseworker_membership(self):
        """Returns membership where user is caseworker."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='caseworker',
            is_active=True,
        )
        result = get_user_staff_memberships(self.user)
        self.assertEqual(result.count(), 1)

    def test_excludes_member_role(self):
        """Does not return membership where user is just a member."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='member',
            is_active=True,
        )
        result = get_user_staff_memberships(self.user)
        self.assertEqual(result.count(), 0)

    def test_excludes_inactive_memberships(self):
        """Does not return inactive memberships."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=False,  # Inactive
        )
        result = get_user_staff_memberships(self.user)
        self.assertEqual(result.count(), 0)

    def test_returns_multiple_memberships(self):
        """Returns all active staff memberships."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role='caseworker',
            is_active=True,
        )
        result = get_user_staff_memberships(self.user)
        self.assertEqual(result.count(), 2)


class TestGetUserOrganization(TestCase):
    """Tests for get_user_organization function."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="vsouser@example.com",
            password="TestPass123!"
        )
        self.org1 = Organization.objects.create(
            name="Primary VSO",
            slug="primary-vso",
            org_type="vso",
        )
        self.org2 = Organization.objects.create(
            name="Secondary VSO",
            slug="secondary-vso",
            org_type="vso",
        )

    def test_returns_none_for_user_with_no_memberships(self):
        """User with no memberships gets None."""
        result = get_user_organization(self.user)
        self.assertIsNone(result)

    def test_returns_org_for_single_membership(self):
        """User with single membership gets that org automatically."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        result = get_user_organization(self.user)
        self.assertEqual(result, self.org1)

    def test_multi_org_user_without_slug_returns_none(self):
        """Multi-org user without explicit selection gets None."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role='caseworker',
            is_active=True,
        )
        # No org_slug provided - should return None
        result = get_user_organization(self.user)
        self.assertIsNone(result)

    def test_multi_org_user_with_valid_slug_returns_org(self):
        """Multi-org user with valid slug gets that org."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role='caseworker',
            is_active=True,
        )
        result = get_user_organization(self.user, org_slug="secondary-vso")
        self.assertEqual(result, self.org2)

    def test_multi_org_user_with_invalid_slug_returns_none(self):
        """Multi-org user with invalid slug gets None."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role='caseworker',
            is_active=True,
        )
        result = get_user_organization(self.user, org_slug="non-existent-org")
        self.assertIsNone(result)

    def test_cannot_access_org_without_membership(self):
        """User cannot select org they don't belong to."""
        # User has membership in org1 only
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        # Try to access org2 via slug
        result = get_user_organization(self.user, org_slug="secondary-vso")
        self.assertIsNone(result)


class TestRequiresOrgSelection(TestCase):
    """Tests for requires_org_selection function."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="multiorg@example.com",
            password="TestPass123!"
        )
        self.org1 = Organization.objects.create(
            name="Org One",
            slug="org-one",
            org_type="vso",
        )
        self.org2 = Organization.objects.create(
            name="Org Two",
            slug="org-two",
            org_type="vso",
        )

    def test_false_for_no_memberships(self):
        """User with no memberships doesn't need selection."""
        result = requires_org_selection(self.user)
        self.assertFalse(result)

    def test_false_for_single_membership(self):
        """User with single membership doesn't need selection."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        result = requires_org_selection(self.user)
        self.assertFalse(result)

    def test_true_for_multiple_memberships(self):
        """User with multiple memberships needs selection."""
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org2,
            role='caseworker',
            is_active=True,
        )
        result = requires_org_selection(self.user)
        self.assertTrue(result)


# =============================================================================
# VIEW TESTS
# =============================================================================

@pytest.mark.django_db
class TestSelectOrganizationView:
    """Tests for the organization selection view."""

    def test_redirects_unauthenticated_user(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get(reverse('vso:select_organization'))
        assert response.status_code == 302
        assert 'login' in response.url.lower() or 'accounts' in response.url.lower()

    def test_shows_org_selection_for_multi_org_user(self, client, db):
        """Multi-org user sees organization selection page."""
        user = User.objects.create_user(
            email="multiselect@example.com",
            password="TestPass123!"
        )
        org1 = Organization.objects.create(
            name="Select Org 1",
            slug="select-org-1",
            org_type="vso",
        )
        org2 = Organization.objects.create(
            name="Select Org 2",
            slug="select-org-2",
            org_type="vso",
        )
        OrganizationMembership.objects.create(
            user=user,
            organization=org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=user,
            organization=org2,
            role='caseworker',
            is_active=True,
        )

        client.login(email="multiselect@example.com", password="TestPass123!")
        response = client.get(reverse('vso:select_organization'))

        assert response.status_code == 200
        assert b"Select Org 1" in response.content
        assert b"Select Org 2" in response.content

    def test_post_sets_session_and_redirects(self, client, db):
        """POST with org_slug sets session and redirects."""
        user = User.objects.create_user(
            email="postselect@example.com",
            password="TestPass123!"
        )
        org = Organization.objects.create(
            name="Post Org",
            slug="post-org",
            org_type="vso",
        )
        OrganizationMembership.objects.create(
            user=user,
            organization=org,
            role='admin',
            is_active=True,
        )

        client.login(email="postselect@example.com", password="TestPass123!")
        response = client.post(
            reverse('vso:select_organization'),
            {'org_slug': 'post-org'}
        )

        assert response.status_code == 302
        # Session should have the selected org
        assert client.session.get('selected_org_slug') == 'post-org'


@pytest.mark.django_db
class TestVSODashboardOrgScoping:
    """Tests for VSO dashboard organization scoping."""

    def test_dashboard_redirects_multi_org_user_without_selection(self, client, db):
        """Multi-org user without selection is redirected to select org."""
        user = User.objects.create_user(
            email="dashredirect@example.com",
            password="TestPass123!"
        )
        org1 = Organization.objects.create(
            name="Dash Org 1",
            slug="dash-org-1",
            org_type="vso",
        )
        org2 = Organization.objects.create(
            name="Dash Org 2",
            slug="dash-org-2",
            org_type="vso",
        )
        OrganizationMembership.objects.create(
            user=user,
            organization=org1,
            role='admin',
            is_active=True,
        )
        OrganizationMembership.objects.create(
            user=user,
            organization=org2,
            role='caseworker',
            is_active=True,
        )

        client.login(email="dashredirect@example.com", password="TestPass123!")
        response = client.get(reverse('vso:dashboard'))

        # Should redirect to org selection
        assert response.status_code == 302
        assert 'select' in response.url.lower()

    def test_dashboard_accessible_for_single_org_user(self, client, db):
        """Single-org user can access dashboard directly."""
        user = User.objects.create_user(
            email="singledash@example.com",
            password="TestPass123!"
        )
        org = Organization.objects.create(
            name="Single Dash Org",
            slug="single-dash-org",
            org_type="vso",
        )
        OrganizationMembership.objects.create(
            user=user,
            organization=org,
            role='admin',
            is_active=True,
        )

        client.login(email="singledash@example.com", password="TestPass123!")
        response = client.get(reverse('vso:dashboard'))

        # Should be accessible (200 or 302 to a valid page, not org selection)
        if response.status_code == 302:
            assert 'select' not in response.url.lower()
        else:
            assert response.status_code == 200
