# Path A: Direct-to-Veteran (B2C)

Individual veterans using the platform for their own claims journey.

## Overview

| Aspect | Details |
|--------|---------|
| **Target User** | Individual veterans |
| **Business Model** | Freemium → Premium ($19/mo) |
| **Go-to-Market** | SEO, content marketing, veteran communities |
| **Key Value** | AI-powered claims assistance without needing a VSO |

## User Journey

```
Veteran discovers site
        ↓
    Signs up (free)
        ↓
    Uploads first document
        ↓
    Gets AI analysis
        ↓
    Uses exam prep guides
        ↓
    Hits free tier limit
        ↓
    Upgrades to Premium (or continues limited)
```

## Features

### Core (Complete)
- [x] Email-based authentication
- [x] Document upload (PDF, images)
- [x] OCR text extraction (Tesseract)
- [x] AI analysis (OpenAI GPT-3.5)
- [x] Denial letter decoder
- [x] C&P exam prep guides (7 conditions)
- [x] VA rating calculator
- [x] Journey dashboard with timeline
- [x] Deadline tracking

### Freemium Model (Complete)
- [x] Usage tracking (documents, storage, features)
- [x] Free tier limits:
  - 3 documents/month
  - 100 MB storage
  - 2 denial decodes/month
  - 5 AI analyses/month
- [x] Premium unlimited access
- [x] Stripe billing integration
- [x] Upgrade prompts

### In Progress
- [ ] **Onboarding Flow**
  - Welcome wizard
  - Profile completion prompts
  - First document guidance

- [ ] **Usage Warning UX**
  - "2 of 3 uploads remaining" badges
  - Warning when approaching limits
  - Soft-block with upgrade CTA

### Planned
- [ ] **Email Sequences**
  - Welcome series
  - Re-engagement for inactive users
  - Deadline reminders
  - Weekly journey summary (opt-in)

- [ ] **Mobile Experience**
  - Responsive upload flow
  - Mobile-friendly document viewer
  - Touch-friendly rating calculator

- [ ] **Export Features**
  - Export analysis to PDF
  - Export rating calculation breakdown
  - Export evidence checklist

- [ ] **Personalization**
  - Condition-specific dashboards
  - Recommended next steps
  - Similar veteran success stories (anonymized)

## Metrics to Track

| Metric | Description |
|--------|-------------|
| **Signups** | New user registrations |
| **Activation** | Users who upload first document |
| **Retention** | Users returning after 7/30 days |
| **Conversion** | Free → Premium upgrade rate |
| **MRR** | Monthly recurring revenue |
| **Churn** | Premium cancellation rate |

## Technical Notes

### Database Queries
Path A users have no organization, so queries are simple:
```python
Document.objects.filter(user=request.user)
```

### Feature Flags
Path A features are always enabled:
```python
FEATURES = {
    'freemium_limits': True,
    'stripe_individual': True,
    'usage_tracking': True,
}
```

### Upgrade Path
Free users can upgrade at any time via `/accounts/upgrade/`. Premium users can manage subscription via Stripe Customer Portal.
