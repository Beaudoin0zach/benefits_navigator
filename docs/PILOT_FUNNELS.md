# Pilot User Funnels

This document defines the two primary user journeys for pilot testing.

## Overview

| Path | Description | Auth Required | Key Features |
|------|-------------|---------------|--------------|
| **Path A** | Document upload → AI analysis | Yes | OCR, AI analysis, email notifications |
| **Path B** | Rating calculator → exam guides | Partial | VA math, save/share, PDF export |

---

## Path A: Document Analysis Flow

**Target User**: Veteran with VA documents (decision letters, medical records) wanting analysis.

### User Journey

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Sign Up   │────▶│   Upload    │────▶│  Processing │────▶│   Results   │
│   /Login    │     │  Document   │     │  (async)    │     │  + Email    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   Dashboard          File Select         OCR → AI           View Analysis
                      + Doc Type          Analysis           on Dashboard
```

### Step-by-Step

| Step | URL | Action | Success Criteria |
|------|-----|--------|------------------|
| 1 | `/accounts/signup/` | Create account | Redirect to dashboard |
| 2 | `/claims/upload/` | Upload PDF/image | File accepted, processing starts |
| 3 | `/claims/document/<id>/` | View document | Status shows "processing" → "completed" |
| 4 | (email) | Receive notification | Email arrives within 2 min |
| 5 | `/dashboard/` | View dashboard | Document appears in recent list |

### Key URLs

- Upload: `/claims/upload/`
- Document List: `/claims/`
- Document Detail: `/claims/document/<id>/`
- Dashboard: `/dashboard/`

### Acceptance Criteria

- [ ] PDF upload completes without error
- [ ] Image upload (JPG/PNG) completes without error
- [ ] OCR extracts text successfully
- [ ] AI analysis generates summary
- [ ] Email notification sent (if enabled)
- [ ] Document appears on dashboard
- [ ] Can download original file
- [ ] Can view inline (if PDF)

---

## Path B: Rating Calculator Flow

**Target User**: Veteran wanting to understand their combined disability rating.

### User Journey

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Visit     │────▶│   Enter     │────▶│   View      │────▶│   Save/     │
│ Calculator  │     │  Ratings    │     │  Results    │     │   Share     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   Public Page         Add 30%, 20%       Combined: 44%      PDF Export
                       bilateral, etc     Monthly: $xxx       Share Link
```

### Step-by-Step

| Step | URL | Action | Auth | Success Criteria |
|------|-----|--------|------|------------------|
| 1 | `/exam-prep/rating-calculator/` | Visit calculator | No | Page loads |
| 2 | (same) | Add ratings (e.g., 30%, 20%) | No | Ratings appear in list |
| 3 | (same) | Click "Calculate" | No | Combined rating shown |
| 4 | `/exam-prep/rating-calculator/save/` | Save calculation | Yes | Saved to account |
| 5 | `/exam-prep/rating-calculator/share/` | Share calculation | No | Share URL generated |
| 6 | `/exam-prep/rating-calculator/export-pdf/` | Export PDF | No | PDF downloads |

### Key URLs

- Calculator: `/exam-prep/rating-calculator/`
- Saved Calculations: `/exam-prep/rating-calculator/saved/`
- Share: `/exam-prep/shared/<token>/`
- Exam Guides: `/exam-prep/`
- Glossary: `/exam-prep/glossary/`

### Acceptance Criteria

- [ ] Can add multiple disability ratings
- [ ] Bilateral factor checkbox works
- [ ] Combined rating calculates correctly (VA math)
- [ ] Monthly compensation estimates display
- [ ] Can save calculation (requires login)
- [ ] Can share via URL (works anonymous)
- [ ] PDF export includes all details
- [ ] Exam guides accessible from calculator

---

## Test Scenarios

### Path A Test Cases

```python
# Test Case A1: Basic Document Upload
1. Login as pilot user
2. Navigate to /claims/upload/
3. Select a PDF file (< 10MB)
4. Choose document type: "Decision Letter"
5. Submit form
6. Verify redirect to document detail
7. Wait for status: "completed"
8. Verify AI summary is populated

# Test Case A2: Image Upload (OCR)
1. Login as pilot user
2. Upload JPG image of text
3. Verify OCR extracts text
4. Verify AI analysis runs

# Test Case A3: Email Notification
1. Ensure notification preferences enabled
2. Upload document
3. Wait for processing
4. Check email inbox for notification
5. Click link in email → document detail

# Test Case A4: Dashboard Integration
1. Upload 3 documents
2. Navigate to /dashboard/
3. Verify recent documents section shows uploads
4. Click document → goes to detail page
```

### Path B Test Cases

```python
# Test Case B1: Basic Calculation
1. Navigate to /exam-prep/rating-calculator/
2. Add rating: 30% - "Knee injury"
3. Add rating: 20% - "Back pain"
4. Click Calculate
5. Verify combined: 44% (not 50%)
6. Verify VA math explanation shown

# Test Case B2: Bilateral Factor
1. Add rating: 30% - "Left knee" (bilateral)
2. Add rating: 20% - "Right knee" (bilateral)
3. Calculate
4. Verify bilateral factor applied (+10% of bilateral sum)

# Test Case B3: Save Calculation
1. Calculate ratings (as above)
2. Click "Save"
3. Login if prompted
4. Enter name: "My Current Rating"
5. Submit
6. Verify appears in saved calculations list

# Test Case B4: Share Calculation
1. Calculate ratings
2. Click "Share"
3. Copy share URL
4. Open in incognito window
5. Verify calculation displays correctly
6. Verify share link expires info shown

# Test Case B5: PDF Export
1. Calculate ratings
2. Click "Export PDF"
3. Verify PDF downloads
4. Open PDF - verify all data present
```

---

## Pilot Account Setup

### Create Pilot Users

```bash
# Create pilot test accounts
python manage.py setup_pilot_accounts
```

This creates:
- `pilot_a@test.com` - Path A tester (document focus)
- `pilot_b@test.com` - Path B tester (calculator focus)
- `pilot_both@test.com` - Both paths tester

All accounts:
- Password: `PilotTest2026!`
- Email verified
- Notifications enabled

### Sample Data

The pilot setup also creates:
- Sample exam checklists
- Sample saved calculations
- Sample journey milestones

---

## Monitoring Pilot Usage

### Key Metrics to Track

**Path A:**
- Documents uploaded per user
- Processing success rate
- OCR confidence scores
- AI analysis completion rate
- Email delivery rate

**Path B:**
- Calculations performed
- Save rate (calculated → saved)
- Share rate (calculated → shared)
- PDF export count
- Guide views

### Admin Views

- Feedback: `/admin/core/feedback/`
- Documents: `/admin/claims/document/`
- Saved Calculations: `/admin/examprep/savedratingcalculation/`
- User Activity: `/admin/core/auditlog/`

### Sentry Monitoring

All errors automatically tracked in Sentry with:
- User context (if authenticated)
- Request path
- Stack trace

---

## Known Limitations

### Path A
- OCR may struggle with handwritten text
- Large files (>10MB) rejected
- Processing may take 1-2 minutes
- OpenAI costs per document (~$0.01-0.05)

### Path B
- Uses 2024 compensation rates
- Bilateral factor simplified (complex groupings not supported)
- No automatic rate updates (annual manual update needed)

---

## Support During Pilot

- Feedback widget on all pages (thumbs up/down + comments)
- Support email: configured in settings
- GitHub issues: https://github.com/Beaudoin0zach/benefits_navigator/issues
