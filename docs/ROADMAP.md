# VA Benefits Navigator - Development Roadmap

This document tracks the dual-path development strategy for the VA Benefits Navigator.

## Development Paths

| Path | Target | Model | Status |
|------|--------|-------|--------|
| **Path A** | Individual Veterans | B2C, Freemium | MVP Complete |
| **Path B** | VSO Organizations | B2B, Per-seat | Phase 1 In Progress |

## Current Focus

**Phase: Shared Foundation + Path B Phase 1**

Building infrastructure that benefits both paths while establishing the Organization model for VSO support.

---

## Path A: Direct-to-Veteran (B2C)

**Status:** MVP Complete, Iterating

See [PATH_A.md](./PATH_A.md) for detailed tracking.

### Completed
- [x] User authentication (email-based, django-allauth)
- [x] Document upload with OCR and AI analysis
- [x] Freemium model (3 docs/month, 100MB storage)
- [x] Usage tracking and enforcement
- [x] Stripe individual billing
- [x] Denial decoder
- [x] C&P exam prep guides
- [x] VA rating calculator
- [x] Journey dashboard

### In Progress
- [ ] Onboarding flow improvements
- [ ] Usage warning UX (approaching limits)
- [ ] Email sequences (welcome, engagement)

### Planned
- [ ] Mobile-responsive improvements
- [ ] Saved rating calculations
- [ ] Export to PDF

---

## Path B: VSO Platform (B2B)

**Status:** Phase 1 In Progress

See [PATH_B.md](./PATH_B.md) for detailed tracking.

### Phase 1: Organization Foundation (Current)
- [ ] Organization model
- [ ] OrganizationMembership model
- [ ] Role system (admin, caseworker, veteran)
- [ ] Org creation flow
- [ ] Invitation system

### Phase 2: Data Scoping & Assignment
- [ ] Org-scoped documents/claims
- [ ] Caseworker-veteran assignment
- [ ] Shared vs. personal documents
- [ ] Permission boundaries

### Phase 3: Org Billing
- [ ] Org-level Stripe subscription
- [ ] Seat-based pricing
- [ ] Org members bypass individual limits
- [ ] Billing admin UI

### Phase 4: Admin Dashboard
- [ ] Org admin dashboard
- [ ] User management (invite, deactivate, roles)
- [ ] Usage reporting
- [ ] Audit log export
- [ ] Org settings (MFA requirement, retention)

### Future
- [ ] SSO/SAML integration
- [ ] MFA enforcement
- [ ] API access for integrations

---

## Shared Infrastructure

See [SHARED.md](./SHARED.md) for detailed tracking.

### Completed
- [x] Security hardening (CSP, media protection, magic bytes)
- [x] Usage tracking model
- [x] Audit logging
- [x] Feature flags system

### In Progress
- [ ] Health check endpoints
- [ ] Monitoring and alerting

### Planned
- [ ] Privacy policy page
- [ ] Consent flow
- [ ] Retention policy enforcement
- [ ] Backup/restore testing
- [ ] Admin runbook

---

## Feature Flags

Features are controlled via flags in `settings.py`. Path B features are disabled by default and enabled progressively.

```python
FEATURES = {
    # Path A (enabled)
    'freemium_limits': True,
    'stripe_individual': True,
    'usage_tracking': True,

    # Path B (progressive)
    'organizations': False,
    'org_roles': False,
    'org_invitations': False,
    'caseworker_assignment': False,
    'org_billing': False,
    'org_admin_dashboard': False,
    'audit_export': False,
}
```

Enable via environment variables:
```bash
FEATURE_ORGANIZATIONS=true
FEATURE_ORG_ROLES=true
```

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| Path A MVP | - | Complete |
| Security Hardening | - | Complete |
| Freemium Model | - | Complete |
| Path B Phase 1 | - | In Progress |
| VSO Pilot Ready | - | Planned |
| First VSO Partnership | - | Planned |

---

## Development Guidelines

### Branch Naming
- `feature/path-a/*` - Path A features
- `feature/path-b/*` - Path B features
- `feature/shared/*` - Shared infrastructure
- `fix/*` - Bug fixes
- `docs/*` - Documentation

### Todo Labels
- `[A]` - Path A (Direct-to-Veteran)
- `[B]` - Path B (VSO Platform)
- `[S]` - Shared infrastructure

### Testing
- All changes must pass existing tests
- Path B features should be tested with flags on AND off
- Both paths must work simultaneously
