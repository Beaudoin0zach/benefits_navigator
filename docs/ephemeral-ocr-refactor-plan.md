# Ephemeral OCR Refactor Plan

**Date:** 2026-01-22
**Author:** Staff Engineer
**Status:** Planning Phase

---

## Executive Summary

This document outlines a security-driven refactor to eliminate long-term storage of raw OCR text from the VA Benefits Navigator database. The goal is to minimize PHI breach risk while preserving product functionality, reliability, and observability.

**Current State:** OCR text is stored redundantly in 3 database fields, creating unnecessary PHI exposure.

**Target State:** OCR text is ephemeral (memory-only during processing), with only structured AI outputs persisted.

---

## Phase 1: Impact Analysis

### 1.1 OCR Text Storage Locations

| Field | Model | File | Purpose |
|-------|-------|------|---------|
| `ocr_text` | Document | `claims/models.py:75` | Primary OCR storage |
| `raw_text` | DecisionLetterAnalysis | `agents/models.py:77` | Duplicate for analysis |
| `raw_text` | RatingAnalysis | `agents/models.py:320` | Duplicate for analysis |

**Total PHI Fields:** 3 (redundant storage of same data)

### 1.2 Usage by Category

#### Models (3 files)
| File | Line | Usage | Risk | Strategy |
|------|------|-------|------|----------|
| `claims/models.py` | 75-78 | Field definition | HIGH | Remove after migration |
| `claims/models.py` | 150-169 | `mark_completed()` accepts `ocr_text` | MEDIUM | Update signature |
| `agents/models.py` | 77 | DecisionLetterAnalysis.raw_text | HIGH | Remove field |
| `agents/models.py` | 320 | RatingAnalysis.raw_text | HIGH | Remove field |

#### Celery Tasks (1 file, 9 usages)
| File | Line | Usage | Risk | Strategy |
|------|------|-------|------|----------|
| `claims/tasks.py` | 98-101 | Saves OCR to document | HIGH | Keep in memory only |
| `claims/tasks.py` | 111 | Passes to AI service | LOW | Already in-memory |
| `claims/tasks.py` | 137 | Logs OCR length | LOW | Keep (non-PHI) |
| `claims/tasks.py` | 212-222 | Check/OCR if missing | HIGH | Re-OCR on retry |
| `claims/tasks.py` | 231, 247 | Uses for analysis | LOW | Pass in-memory |
| `claims/tasks.py` | 395-405 | Rating analysis OCR | HIGH | Re-OCR on retry |
| `claims/tasks.py` | 416-461 | Analysis storage | HIGH | Don't store raw_text |

#### GraphQL API (1 file, 3 usages)
| File | Line | Usage | Risk | Strategy |
|------|------|-------|------|----------|
| `benefits_navigator/schema.py` | 197 | Type definition | HIGH | Remove field |
| `benefits_navigator/schema.py` | 459 | Fetch and sanitize | HIGH | Return empty/removed |
| `benefits_navigator/schema.py` | 472 | Return to client | HIGH | Remove from response |

#### Templates (2 files)
| File | Line | Usage | Risk | Strategy |
|------|------|-------|------|----------|
| `templates/claims/document_detail.html` | 106-108 | Display to user | MEDIUM | Remove section |
| `templates/vso/shared_document_review.html` | 190-203 | Display to VSO | MEDIUM | Remove section |

#### Admin (2 files)
| File | Line | Usage | Risk | Strategy |
|------|------|-------|------|----------|
| `claims/admin.py` | 29 | Admin fieldset | HIGH | Remove from display |
| `agents/admin.py` | 28 | Search field | HIGH | Remove from search |

#### Tests (15+ usages)
| File | Lines | Impact |
|------|-------|--------|
| `claims/tests.py` | 98, 783-821, 947, 1131, 1181, 1244-1302, 1350, 1555, 1608 | Update test fixtures |
| `conftest.py` | 187 | Update fixture |
| `agents/tests.py` | 130, 905 | Update fixtures |

### 1.3 API Exposure Analysis

| Endpoint | Exposes OCR? | Current Mitigation | Action |
|----------|--------------|-------------------|--------|
| GraphQL `document_analysis` | YES | PII redaction + truncation | Remove field entirely |
| REST API | NO | N/A | None |
| Templates (HTML) | YES | None | Remove display |
| Admin | YES | Staff-only access | Remove from view |

### 1.4 Post-Analysis Usage

**Question:** Is OCR text used after AI analysis completes?

**Answer:** Yes, but only for:
1. **User verification** - Users can review extracted text in document detail
2. **VSO review** - VSOs can see extracted text when reviewing shared documents
3. **Re-analysis** - If user wants to re-run analysis (rare)

**Key Insight:** None of these require *persisted* OCR text. Options:
- Re-OCR on demand (recommended - file is always available)
- Display message: "Text extracted during processing" without showing content

---

## Phase 2: Ephemeral OCR Pipeline Design

### 2.1 Current Flow (Problematic)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT FLOW                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Upload → Document.save() → Celery Task                                 │
│                                │                                         │
│                                ▼                                         │
│                        OCR Service                                       │
│                                │                                         │
│                                ▼                                         │
│                   ┌────────────────────────┐                            │
│                   │ document.ocr_text = X  │ ← PHI PERSISTED            │
│                   │ document.save()        │                            │
│                   └────────────────────────┘                            │
│                                │                                         │
│                                ▼                                         │
│                        AI Service                                        │
│                                │                                         │
│                                ▼                                         │
│                   ┌────────────────────────┐                            │
│                   │ analysis.raw_text = X  │ ← PHI PERSISTED (AGAIN!)   │
│                   │ analysis.save()        │                            │
│                   └────────────────────────┘                            │
│                                                                          │
│  PHI persisted in: Document.ocr_text, Analysis.raw_text                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 New Flow (Ephemeral)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEW FLOW                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Upload → Document.save() → Celery Task                                 │
│                                │                                         │
│                                ▼                                         │
│                        OCR Service                                       │
│                                │                                         │
│                                ▼                                         │
│                   ┌────────────────────────┐                            │
│                   │ ocr_text = result      │ ← IN-MEMORY ONLY           │
│                   │ (variable, not saved)  │                            │
│                   └────────────────────────┘                            │
│                                │                                         │
│                                ▼                                         │
│                        AI Service(ocr_text)                             │
│                                │                                         │
│                                ▼                                         │
│                   ┌────────────────────────┐                            │
│                   │ analysis.summary = Y   │ ← ONLY STRUCTURED OUTPUT   │
│                   │ analysis.conditions    │    NO RAW TEXT             │
│                   │ analysis.save()        │                            │
│                   └────────────────────────┘                            │
│                                │                                         │
│                                ▼                                         │
│                   ┌────────────────────────┐                            │
│                   │ document.ocr_status =  │ ← METADATA ONLY            │
│                   │   'processed'          │                            │
│                   │ document.ocr_length    │                            │
│                   │ document.save()        │                            │
│                   └────────────────────────┘                            │
│                                                                          │
│  PHI persisted: NONE (only structured AI outputs + metadata)            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Retry Strategy

**Problem:** If a task fails mid-processing, how do we retry without persisted OCR?

**Solution:** Re-OCR from the original file.

```python
# New task structure
@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id):
    document = Document.objects.get(id=document_id)

    # ALWAYS extract fresh from file (idempotent)
    ocr_result = ocr_service.extract_text(document.file.path)
    ocr_text = ocr_result['text']  # In-memory only

    # Update metadata (no PHI)
    document.ocr_confidence = ocr_result.get('confidence')
    document.ocr_length = len(ocr_text)  # Length only, not content
    document.page_count = ocr_result.get('page_count', 0)
    document.save(update_fields=['ocr_confidence', 'ocr_length', 'page_count'])

    # Pass directly to AI (in-memory)
    ai_result = ai_service.analyze_document(text=ocr_text, ...)

    # Store only structured output
    document.ai_summary = ai_result['analysis']
    document.save(update_fields=['ai_summary', ...])
```

**Trade-off:** Re-OCR on retry is slower but:
- OCR is fast (~5-10s for typical documents)
- Retries are rare (<5% of documents)
- Security benefit outweighs performance cost

### 2.4 Failure Handling

| Failure Point | Current Behavior | New Behavior |
|---------------|------------------|--------------|
| OCR fails | Retry task, re-OCR | Same (no change) |
| AI fails after OCR | Retry, use persisted OCR | Retry, re-OCR from file |
| Worker crash | Retry, use persisted OCR | Retry, re-OCR from file |
| File deleted | Fail permanently | Same (no change) |

**New error state:** If file is deleted before processing completes, mark as `failed` with message "Original file unavailable for processing."

### 2.5 Idempotency Preservation

| Operation | Idempotent? | Notes |
|-----------|-------------|-------|
| OCR extraction | ✅ Yes | Same file → same text |
| AI analysis | ⚠️ Mostly | Small variations due to model temperature |
| Metadata save | ✅ Yes | Overwrites with same values |

**Key:** Always start from the original file, not database state.

---

## Phase 3: Data Model & Migration Plan

### 3.1 Decision: Remove vs Encrypt

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Remove field** | No PHI at rest, simpler | Breaking change, no user review | ✅ **Recommended** |
| **Encrypt + TTL** | Users can review | Still stores PHI, complexity | ❌ Reject |
| **Keep (status quo)** | No changes needed | PHI exposure risk | ❌ Reject |

**Decision:** Remove `ocr_text` and `raw_text` fields entirely.

**UX Impact:** Users can no longer view extracted text. Mitigation:
- Show message: "Text was extracted and analyzed. Download original document to view."
- Or: Add "Re-extract text" button that OCRs on demand (not persisted)

### 3.2 Fields to Remove

```python
# claims/models.py
- ocr_text = models.TextField(...)  # REMOVE

# agents/models.py (DecisionLetterAnalysis)
- raw_text = models.TextField(...)  # REMOVE

# agents/models.py (RatingAnalysis)
- raw_text = models.TextField(...)  # REMOVE
```

### 3.3 Fields to Add (Metadata Only)

```python
# claims/models.py
+ ocr_length = models.IntegerField('Extracted text length', default=0)
+ ocr_status = models.CharField(
+     max_length=20,
+     choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
+     default='pending'
+ )
```

### 3.4 Migration Strategy

**Step 1: Add new metadata fields (non-breaking)**
```python
# Migration 0002_add_ocr_metadata.py
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='document',
            name='ocr_length',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='document',
            name='ocr_status',
            field=models.CharField(default='pending', max_length=20),
        ),
    ]
```

**Step 2: Deploy code that writes to new fields (backward compatible)**
- Update tasks to write `ocr_length` and `ocr_status`
- Old code still works

**Step 3: Backfill existing records**
```python
# Management command
Document.objects.filter(ocr_text__isnull=False).update(
    ocr_status='completed',
    ocr_length=Length('ocr_text')
)
```

**Step 4: Remove reads of ocr_text**
- Update templates, GraphQL, admin
- Deploy

**Step 5: Remove field from model (breaking)**
```python
# Migration 0003_remove_ocr_text.py
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField(model_name='document', name='ocr_text'),
        migrations.RemoveField(model_name='decisionletteranalysis', name='raw_text'),
        migrations.RemoveField(model_name='ratinganalysis', name='raw_text'),
    ]
```

### 3.5 Rollback Plan

| Step | Rollback |
|------|----------|
| Add metadata fields | Remove fields (data loss: none) |
| Update code to use metadata | Revert code |
| Backfill | No rollback needed (additive) |
| Remove ocr_text reads | Revert code |
| Remove ocr_text field | **CANNOT ROLLBACK** - data is gone |

**Safe Point:** Before Step 5, all changes are reversible.

**Recommendation:**
1. Keep `ocr_text` field for 30 days after Step 4
2. Set `ocr_text = NULL` for all records (clear data, keep field)
3. After 30 days with no issues, run Step 5

---

## Phase 4: Security Hardening

### 4.1 GraphQL Audit

**File:** `benefits_navigator/schema.py`

**Current (lines 197, 443-476):**
```python
@strawberry.type
class DocumentAnalysisType:
    ocr_text: str  # ← EXPOSES PHI
    ai_summary: Optional[str]

@strawberry.field
def document_analysis(...):
    sanitized_ocr = sanitize_graphql_text(d.ocr_text or '', MAX_OCR_TEXT_LENGTH)
    return DocumentAnalysisType(ocr_text=sanitized_ocr, ...)
```

**After:**
```python
@strawberry.type
class DocumentAnalysisType:
    # ocr_text: REMOVED
    ai_summary: Optional[str]
    ocr_status: str  # 'completed', 'failed', etc.
    ocr_length: int  # Character count only
```

### 4.2 Admin Audit

**File:** `claims/admin.py:29`
```python
# BEFORE
fieldsets = (
    ('OCR Results', {'fields': ('ocr_text', 'ocr_confidence')}),
)

# AFTER
fieldsets = (
    ('OCR Results', {'fields': ('ocr_status', 'ocr_length', 'ocr_confidence')}),
)
```

**File:** `agents/admin.py:28`
```python
# BEFORE
search_fields = ['user__email', 'summary', 'raw_text']

# AFTER
search_fields = ['user__email', 'summary']
```

### 4.3 Logging Audit

**Current logging in `claims/tasks.py:103`:**
```python
logger.info(f"OCR complete for document {document_id}. Extracted {len(ocr_result['text'])} characters")
```
✅ **Safe** - Only logs length, not content.

**Verify no PII leaks:**
- Search for `logger.*ocr_text`
- Search for `logger.*raw_text`
- Search for `print.*ocr_text`

### 4.4 Tests for OCR Leakage

```python
# tests/test_ocr_security.py

def test_graphql_does_not_expose_ocr_text():
    """Ensure GraphQL schema doesn't include ocr_text field."""
    query = """
        query { documentAnalysis(id: "1") { ocrText } }
    """
    response = client.execute(query)
    assert 'errors' in response  # Field doesn't exist

def test_api_response_excludes_ocr_text():
    """Ensure REST API doesn't include ocr_text."""
    response = client.get(f'/api/documents/{doc.id}/')
    assert 'ocr_text' not in response.json()
    assert 'raw_text' not in response.json()

def test_document_model_has_no_ocr_text_field():
    """Ensure model field was removed."""
    from claims.models import Document
    assert not hasattr(Document, 'ocr_text')
```

---

## Phase 5: Implementation Checklist

### PR 1: Add OCR Metadata Fields (Safe, Non-Breaking)

**Files Changed:**
- `claims/models.py` - Add `ocr_length`, `ocr_status` fields
- `claims/migrations/` - New migration

**What Changed:** Added metadata fields to track OCR status without storing content.

**Risk:** None - additive change only.

**Rollback:** Remove migration and fields.

---

### PR 2: Update Tasks for Ephemeral OCR (Backward Compatible)

**Files Changed:**
- `claims/tasks.py` - Refactor to not persist OCR text
- `claims/services/ai_service.py` - No changes needed (already accepts text param)

**What Changed:** Tasks now pass OCR text in-memory to AI services instead of persisting.

**Risk:** Low - still writes to old fields temporarily for backward compat.

**Rollback:** Revert to previous task code.

---

### PR 3: Remove OCR Display from UI (User-Facing)

**Files Changed:**
- `templates/claims/document_detail.html` - Remove OCR text section
- `templates/vso/shared_document_review.html` - Remove OCR text section
- `benefits_navigator/schema.py` - Remove `ocr_text` from GraphQL type

**What Changed:** Users can no longer view extracted text in UI.

**Risk:** Medium - UX change. Users may complain.

**Rollback:** Restore template sections (data still exists at this point).

---

### PR 4: Remove OCR Fields from Admin

**Files Changed:**
- `claims/admin.py` - Remove `ocr_text` from fieldset
- `agents/admin.py` - Remove `raw_text` from search

**What Changed:** Admin no longer displays or searches PHI text.

**Risk:** Low - internal tooling change.

**Rollback:** Restore admin configuration.

---

### PR 5: Clear Existing OCR Data (Data Deletion)

**Files Changed:**
- Management command to set `ocr_text = ''` for all documents
- Management command to set `raw_text = ''` for all analyses

**What Changed:** Existing PHI text data cleared from database.

**Risk:** HIGH - Data loss (intentional). **Point of no return for data.**

**Rollback:** Cannot recover data. Ensure backups exist before running.

---

### PR 6: Remove OCR Fields from Models (Schema Change)

**Files Changed:**
- `claims/models.py` - Remove `ocr_text` field
- `agents/models.py` - Remove `raw_text` fields
- Migrations to drop columns

**What Changed:** Database schema no longer includes PHI text fields.

**Risk:** HIGH - Irreversible schema change.

**Rollback:** Can re-add fields but data is gone.

---

### PR 7: Update Tests and Documentation

**Files Changed:**
- `claims/tests.py` - Update fixtures, remove ocr_text references
- `agents/tests.py` - Update fixtures
- `conftest.py` - Update document fixture
- `docs/` - Update architecture docs
- `CLAUDE.md` - Update data flow documentation

**What Changed:** Tests and docs reflect new architecture.

**Risk:** None - documentation only.

---

## Monitoring & Verification

### Success Criteria

1. ✅ No `ocr_text` or `raw_text` in database schema
2. ✅ No PHI text in GraphQL responses
3. ✅ No PHI text in admin views
4. ✅ No PHI text in logs
5. ✅ Document processing still works (test with upload)
6. ✅ AI analysis quality unchanged
7. ✅ Retry behavior works correctly

### Alerts to Add

```python
# core/alerting.py

# Alert if OCR text accidentally persisted
ALERTS['ocr_text_persisted'] = {
    'condition': lambda: Document.objects.filter(ocr_text__isnull=False, ocr_text__gt='').exists(),
    'message': 'OCR text found in database - security policy violation',
    'severity': 'critical',
}
```

---

## Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Discovery | ✅ Complete | None |
| Phase 2: Design | ✅ Complete | Phase 1 |
| Phase 3: Migration Plan | ✅ Complete | Phase 2 |
| Phase 4: Security Audit | 1 day | Phase 2 |
| Phase 5: Implementation | 5-7 days | Phases 1-4 |

**Total:** ~2 weeks including testing and deployment

---

## Appendix: Files Index

| File | Changes Required |
|------|------------------|
| `claims/models.py` | Remove `ocr_text`, add metadata fields |
| `claims/tasks.py` | Refactor all 3 task functions |
| `claims/admin.py` | Remove `ocr_text` from display |
| `claims/forms.py` | None |
| `claims/views.py` | None |
| `agents/models.py` | Remove `raw_text` from 2 models |
| `agents/admin.py` | Remove `raw_text` from search |
| `benefits_navigator/schema.py` | Remove `ocr_text` from GraphQL |
| `templates/claims/document_detail.html` | Remove OCR display section |
| `templates/vso/shared_document_review.html` | Remove OCR display section |
| `claims/tests.py` | Update 15+ test fixtures |
| `agents/tests.py` | Update test fixtures |
| `conftest.py` | Update document fixture |
