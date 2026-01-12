# Path B: VSO Platform (B2B)

Veteran Service Organizations using the platform to assist multiple veterans.

## Overview

| Aspect | Details |
|--------|---------|
| **Target User** | VSOs, law firms, nonprofits |
| **Business Model** | Per-seat or flat org pricing |
| **Go-to-Market** | Direct sales, VSO conferences, referrals |
| **Key Value** | Streamlined casework, audit trail, team collaboration |

## User Roles

```
Organization
    ├── Admin
    │   ├── Manage users
    │   ├── View all data
    │   ├── Access audit logs
    │   └── Billing management
    │
    ├── Caseworker
    │   ├── View assigned veterans
    │   ├── Upload on behalf of veterans
    │   ├── Run analyses
    │   └── Add notes
    │
    └── Veteran (invited)
        ├── View own data
        ├── Upload documents
        └── Communicate with caseworker
```

## Phases

### Phase 1: Organization Foundation (Current)

**Goal:** Basic multi-tenant structure

- [ ] **Organization Model**
  ```python
  class Organization:
      name: str
      slug: str (unique)
      org_type: enum (vso, law_firm, nonprofit)
      stripe_customer_id: str
      plan: enum (starter, pro, enterprise)
      seats: int
      settings: JSON (mfa_required, retention_days, etc.)
  ```

- [ ] **Membership Model**
  ```python
  class OrganizationMembership:
      user: FK(User)
      organization: FK(Organization)
      role: enum (admin, caseworker, veteran)
      invited_by: FK(User)
      invited_at: datetime
      accepted_at: datetime
  ```

- [ ] **Org Creation Flow**
  - User signs up
  - Selects "Create Organization"
  - Enters org details
  - Becomes org admin

- [ ] **Invitation System**
  - Admin invites by email
  - Invite token with expiry
  - Role assignment on invite
  - Accept/decline flow

### Phase 2: Data Scoping & Assignment

**Goal:** Proper data isolation and sharing

- [ ] **Org-Scoped Data**
  - Documents belong to user AND optionally org
  - Claims can be org-visible or personal
  - Clear "shared with org" indicator

- [ ] **Caseworker Assignment**
  ```python
  class VeteranAssignment:
      veteran: FK(User)
      caseworker: FK(User)
      organization: FK(Organization)
      assigned_at: datetime
      notes: text
  ```

- [ ] **Permission Boundaries**
  - Veterans see only their data
  - Caseworkers see assigned veterans
  - Admins see all org data
  - No cross-org visibility

### Phase 3: Org Billing

**Goal:** Organization-level subscriptions

- [ ] **Org Stripe Integration**
  - Org-level customer ID
  - Subscription tied to org, not user
  - Seat-based pricing

- [ ] **Pricing Tiers**
  | Tier | Price | Seats | Features |
  |------|-------|-------|----------|
  | Starter | $99/mo | 5 | Basic features |
  | Pro | $299/mo | 20 | + Audit export, priority support |
  | Enterprise | Custom | Unlimited | + SSO, dedicated support |

- [ ] **Seat Management**
  - Track active seats
  - Warn when approaching limit
  - Self-serve seat purchase

- [ ] **Org Members Bypass Individual Limits**
  - No freemium restrictions for org members
  - Usage tracked at org level

### Phase 4: Admin Dashboard

**Goal:** VSO self-service management

- [ ] **Org Admin Dashboard**
  - Overview stats (users, documents, activity)
  - Quick actions (invite, assign, deactivate)

- [ ] **User Management**
  - Invite new users
  - Change roles
  - Deactivate users (preserves data)
  - Resend invitations

- [ ] **Usage Reporting**
  - Documents uploaded per user/period
  - AI analyses run
  - Storage consumption
  - Activity timeline

- [ ] **Audit Log Export**
  - Filter by date, user, action
  - Export to CSV/JSON
  - Include IP, timestamp, resource

- [ ] **Org Settings**
  - Require MFA for all users
  - Data retention period
  - Allowed domains for invites
  - Default caseworker assignment

### Future Phases

- [ ] **SSO/SAML Integration**
  - Connect to org IdP
  - Auto-provision users
  - Role mapping

- [ ] **MFA Enforcement**
  - Org-level MFA requirement
  - TOTP support
  - Backup codes

- [ ] **API Access**
  - API keys for org
  - Webhook notifications
  - Bulk operations

## Technical Notes

### Feature Flags

Path B features are flag-gated and disabled by default:

```python
FEATURES = {
    'organizations': False,  # Enable to show org features
    'org_roles': False,      # Enable role-based permissions
    'org_invitations': False,
    'caseworker_assignment': False,
    'org_billing': False,
    'org_admin_dashboard': False,
    'audit_export': False,
}
```

Enable via environment:
```bash
FEATURE_ORGANIZATIONS=true
FEATURE_ORG_ROLES=true
```

### Database Queries

Org-aware queries check membership:

```python
# Get user's organizations
user.memberships.all()

# Get org's members
org.memberships.filter(role='caseworker')

# Get documents visible to caseworker
Document.objects.filter(
    Q(user=request.user) |  # Own documents
    Q(organization=caseworker_org, user__in=assigned_veterans)
)
```

### URL Structure

```
/org/                      # Org selection (if multiple)
/org/<slug>/               # Org dashboard
/org/<slug>/members/       # Member list
/org/<slug>/invite/        # Invite form
/org/<slug>/settings/      # Org settings
/org/<slug>/billing/       # Billing management
/org/<slug>/audit/         # Audit log
```

## VSO Requirements Checklist

Before piloting with a VSO, ensure:

- [ ] Data protection baseline (TLS, encryption at rest, access controls)
- [ ] Role separation working correctly
- [ ] Audit logging captures all key actions
- [ ] Audit export available
- [ ] Retention policy documented
- [ ] Privacy policy published
- [ ] Support/incident procedures documented
- [ ] Backup/restore tested
