# Benefits Navigator - Session Notes

## Latest Session (January 11, 2026 - Evening)

### Documentation App Templates Completed

Created all frontend templates for the searchable documentation system:

1. **Search Page** (`templates/documentation/search.html`)
   - Main search interface with HTMX live search
   - Category cards for browsing (Forms, Exam Guides, Legal References)

2. **VA Forms** (`templates/documentation/form_list.html`, `form_detail.html`)
   - List view with workflow stage filtering
   - Detail view with instructions, tips, common mistakes, deadlines
   - Related forms and exam guides

3. **C&P Exam Guides** (`templates/documentation/exam_guide_list.html`, `exam_guide_detail.html`)
   - List view with category filtering
   - Detail view with what to expect, key questions, documentation needed, tips

4. **Legal References** (`templates/documentation/legal_reference_list.html`, `legal_reference_detail.html`)
   - List view with type filtering and pagination
   - Detail view with summary, key points, relevance
   - Legal disclaimers throughout

5. **HTMX Search Partial** (`templates/documentation/partials/search_results.html`)
   - Real-time search results for forms, guides, and legal refs

6. **Navigation** - Added "Documentation" link to base template

### All Pages Tested and Working
- `/docs/` - Search page (200 OK)
- `/docs/forms/` - Forms list (200 OK)
- `/docs/forms/21-526EZ/` - Form detail (200 OK)
- `/docs/exam-guides/` - Exam guides list (200 OK)
- `/docs/legal/` - Legal references list (200 OK)

### Data Loaded
- 8 VA forms loaded from `va_forms.json` fixture

---

## Current State (January 2025)

### Completed Features

#### Path B: VSO/Organization Platform
- **Organization Models**: Organization, OrganizationMembership, OrganizationInvitation
- **Organization Flow**: Create org, list orgs, org dashboard
- **Invitation System**: Full invite flow with email notifications, accept/decline, role assignment
- **Feature Flags**: `FEATURE_ORGANIZATIONS`, `FEATURE_ORG_ROLES`, `FEATURE_ORG_INVITATIONS`

#### Security & Infrastructure
- Media access control (signed URLs)
- Content Security Policy headers
- File validation with libmagic
- Audit logging foundation

#### Freemium Foundation
- Usage tracking models
- Stripe integration scaffolding

---

## Next Priority: Searchable Documentation System

### Recommended Document Types (Priority Order)

#### Tier 1: High Impact, Ship Soon

| Document Type | Value | Implementation Notes |
|---------------|-------|---------------------|
| **C&P Clinician's Guide** | Exam prep checklists, what examiners look for | Ingest and surface condition-specific expectations. Help veterans prepare for exams. |
| **VA Forms + Instructions** | Map forms to workflow steps | Each claim stage → correct form with instructions and deadlines |

**Key Forms to Map:**
- `21-526EZ` - Initial disability claim
- `21-0995` - Supplemental claim
- `20-0996` - Higher-Level Review (HLR)
- `10182` - Board Appeal (Notice of Disagreement)
- `21-4138` - Statement in Support of Claim
- `21-0781` - PTSD stressor statement
- `21-0781a` - PTSD secondary to personal assault

#### Tier 2: Valuable, Requires Maintenance

| Document Type | Value | Implementation Notes |
|---------------|-------|---------------------|
| **CAVC Precedential Decisions** | Appeals context, legal precedents | Curated summaries with links to full opinions. Mark as informational. |
| **VAOPGCPREC Opinions** | VA General Counsel precedent opinions | Date-stamped summaries, note applicability. "Legal references" section with disclaimers. |

**Important**: These require clear disclaimers ("informational only, not legal advice") and periodic updates.

#### Tier 3: Advanced/Deferred

| Document Type | Value | Implementation Notes |
|---------------|-------|---------------------|
| **BVA Decision Pattern Mining** | ML-based insights from Board decisions | Complex: data access, labeling, model drift. Defer until core features solid. |

---

## Proposed Data Model

```python
# New models for documentation system

class DocumentCategory(models.Model):
    """Categories for organizing searchable documents"""
    name = models.CharField(max_length=100)  # e.g., "Forms", "C&P Guides", "Legal Precedents"
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For UI
    order = models.IntegerField(default=0)

class VAForm(models.Model):
    """VA forms with metadata and instructions"""
    form_number = models.CharField(max_length=20, unique=True)  # e.g., "21-526EZ"
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()  # Parsed/simplified instructions
    url = models.URLField()  # Link to official VA form
    workflow_stages = models.JSONField(default=list)  # Which stages use this form
    deadline_info = models.TextField(blank=True)  # Deadline requirements
    tips = models.TextField(blank=True)  # User-friendly tips
    last_updated = models.DateField()

class CPExamGuide(models.Model):
    """C&P exam preparation guides by condition"""
    condition = models.ForeignKey('claims.Condition', on_delete=models.CASCADE)
    dbq_form = models.CharField(max_length=50, blank=True)  # Associated DBQ
    what_to_expect = models.TextField()
    key_questions = models.JSONField(default=list)  # Questions examiner will ask
    documentation_needed = models.JSONField(default=list)
    tips = models.TextField()
    red_flags = models.TextField(blank=True)  # Common mistakes to avoid

class LegalReference(models.Model):
    """CAVC decisions and VAOPGCPREC opinions"""
    REFERENCE_TYPES = [
        ('cavc', 'CAVC Decision'),
        ('vaopgcprec', 'VA General Counsel Opinion'),
    ]
    reference_type = models.CharField(max_length=20, choices=REFERENCE_TYPES)
    citation = models.CharField(max_length=100)  # e.g., "38 C.F.R. § 3.303"
    title = models.CharField(max_length=300)
    summary = models.TextField()  # Plain-language summary
    relevance = models.TextField()  # When this applies
    date_issued = models.DateField()
    url = models.URLField(blank=True)
    conditions = models.ManyToManyField('claims.Condition', blank=True)

    class Meta:
        ordering = ['-date_issued']
```

---

## Implementation Approach

### Phase 1: Forms & Workflow Integration
1. Create `VAForm` model
2. Seed database with common forms (21-526EZ, 21-0995, 20-0996, 10182)
3. Map forms to claim journey stages
4. Add "Required Forms" section to claim detail view
5. Integrate with deadline tracking

### Phase 2: C&P Exam Guides
1. Create `CPExamGuide` model
2. Start with top 10-15 most common conditions
3. Parse C&P Clinician's Guide for key criteria
4. Add "Exam Prep" section to condition pages
5. Generate personalized exam prep checklists

### Phase 3: Legal References (with disclaimers)
1. Create `LegalReference` model
2. Curate initial set of key CAVC decisions
3. Add prominent disclaimers
4. Link to relevant conditions/situations
5. Consider admin-only initially for quality control

---

## Search Implementation Options

### Option A: PostgreSQL Full-Text Search
- Pros: No external dependencies, good for moderate scale
- Cons: Less sophisticated ranking

```python
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

# Example query
results = VAForm.objects.annotate(
    search=SearchVector('title', 'description', 'instructions'),
    rank=SearchRank(SearchVector('title', 'description', 'instructions'), query)
).filter(search=query).order_by('-rank')
```

### Option B: Django-Watson or Haystack
- Pros: More features, faceted search
- Cons: Additional complexity

### Option C: Vector Search (for AI-powered search)
- Pros: Semantic search, better for natural language queries
- Cons: Requires embedding infrastructure (pgvector or external)

**Recommendation**: Start with PostgreSQL full-text search, plan for vector search later when AI features expand.

---

## Next Session Tasks

### Immediate (Tier 1)
- [ ] Create documentation app structure
- [ ] Define VAForm and CPExamGuide models
- [ ] Run migrations
- [ ] Create admin interface for content management
- [ ] Seed initial form data (top 5-10 forms)
- [ ] Add search endpoint

### Follow-up
- [ ] Create user-facing search UI
- [ ] Integrate forms into claim workflow
- [ ] Build C&P exam prep feature
- [ ] Add legal references with disclaimers

---

## Source Documents to Obtain

1. **C&P Clinician's Guide** - VA's internal guide for examiners
2. **VA Forms** - Download from va.gov/find-forms
3. **M21-1 Adjudication Manual** - VA's claims processing manual
4. **38 CFR** - Code of Federal Regulations for veterans benefits
5. **CAVC Decisions** - uscourts.cavc.gov
6. **VAOPGCPREC** - va.gov/ogc/opinions.asp

---

## Technical Considerations

### Content Updates
- Forms change periodically; track `last_updated`
- Legal references need periodic review
- Consider admin approval workflow for content changes

### Disclaimers (Required)
```
LEGAL DISCLAIMER: This information is provided for educational purposes only
and does not constitute legal advice. For legal matters, consult with an
accredited VA claims agent, Veterans Service Organization, or attorney.
```

### Feature Flag
```
FEATURE_DOC_SEARCH=true
```
