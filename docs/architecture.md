VA Benefits Navigator – Architecture Map
=======================================

Path A – Veterans (end users)
-----------------------------
- Entry: `benefits_navigator/urls.py` maps `/` → `core.views.home` (`templates/core/home.html`). Authenticated users move into:
  - Claims: `/claims/` (`claims/urls.py`) → document upload/detail/status/share views (`claims/views.py`) with templates under `templates/claims/…`.
  - AI agents: `/agents/…` (`agents/urls.py`) → analyzer/generator views (`agents/views.py`) with templates under `templates/agents/…`.
  - Exam prep & calculators: `/exam-prep/…` (`examprep/urls.py`) templates under `templates/examprep/…`.
  - Appeals workflow: `/appeals/…` (`appeals/urls.py`) templates under `templates/appeals/…`.
  - Dashboard & journey: `/dashboard/`, `/journey/…` (`core/views.py`) templates under `templates/core/…`.
- APIs used:
  - GraphQL endpoint `/graphql/` (`benefits_navigator/urls.py`, schema in `benefits_navigator/schema.py`) exposing user, documents, claims, journey data.
  - HTMX/JSON polling: document/rating/denial status (`claims/views.document_status`, `claims.views.rating_analyzer_status`, `claims.views.denial_decoder_status`), journey timeline/notes, exam calculators.
- Background jobs:
  - Document pipeline: `claims/tasks.py:process_document_task` → OCR (`claims/services/ocr_service.py`) → AI analysis (`claims/services/ai_service.py`).
  - Denial decoder: `claims/tasks.py:decode_denial_letter_task` (DecisionLetterAnalyzer + DenialDecoderService).
  - Rating analyzer: `claims/tasks.py:analyze_rating_decision_task` (RatingDecisionAnalyzer or SimpleRatingAnalyzer).
  - Cleanup/retention: `claims/tasks.cleanup_old_documents`, `core/tasks.enforce_data_retention`, `core/tasks.create_default_retention_policies`, reminders/email tasks in `core/tasks.py`.
  - M21 scraping jobs (shared but feeds Path A intelligence): `agents/tasks.py` scraping/refreshing KnowVA content into DB.

Path B – VSOs (case workers/advocates)
--------------------------------------
- Entry: `/vso/` (`benefits_navigator/urls.py` → `vso/urls.py`) guarded by `vso.permissions.vso_staff_required`.
- Flow:
  - Dashboard and case list/detail: `vso.views.dashboard`, `case_list`, `case_detail` with templates under `templates/vso/…`.
  - Case updates and notes via POST/HTMX endpoints (`vso.views.case_update_status`, `add_case_note`, `complete_action_item`) and partial renders (`case_notes_partial`, `case_documents_partial`).
  - Document/analysis review: `vso.views.shared_document_review` consumes veteran-shared documents and attached AI analyses.
  - Invitations: `vso.views.invite_veteran`, `resend_invitation`, `cancel_invitation`, `accept_invitation`.
- Data/API surfaces:
  - Models: `vso.models.VeteranCase`, `CaseNote`, `SharedDocument`, `SharedAnalysis`, `CaseChecklist`, `ChecklistItem`; membership/organization from `accounts.models.Organization*`.
  - Templates: `templates/vso/dashboard.html`, `case_list.html`, `case_detail.html`, `shared_document_review.html`, invitation templates.
  - No dedicated REST/GraphQL endpoints; relies on server-rendered/HTMX views scoped by organization membership.

Cross-cutting data & persistence
--------------------------------
- Users/profiles/subscriptions: `accounts.models.User`, `UserProfile` (AI consent), `Subscription`, `UsageTracking`, organizations/invitations/memberships.
- Claims documents & AI outputs: `claims.models.Document` (OCR text, AI summaries), optional `Claim`; AI outputs in `agents.models.DecisionLetterAnalysis`, `DenialDecoding`, `RatingAnalysis`, `EvidenceGapAnalysis`, `PersonalStatement`.
- Journey/feedback/support/audit: `core.models` (Journey events/milestones/deadlines, Feedback, SupportRequest, AuditLog, DataRetentionPolicy, ProcessingFailure).
- Appeals tracking: `appeals.models.Appeal`, `AppealGuidance`, `AppealDocument`, `AppealNote`, `AppealStep`.
- Knowledge base (M21): `agents.models.M21ManualSection`, `M21TopicIndex`, scrape jobs.

OpenAI boundaries
-----------------
- Document analyzer: `claims/services/ai_service.py:AIService.analyze_document` builds prompts per document_type and calls `openai.chat.completions.create`.
- Rating decision analyzer: `claims/services/rating_analysis_service.py:RatingDecisionAnalyzer._extract_data/_generate_analysis` (via `BaseAgent._call_openai`) and `SimpleRatingAnalyzer.analyze`.
- Agent tools: `agents/services.py` → `BaseAgent._call_openai` used by `DecisionLetterAnalyzer`, `EvidenceGapAnalyzer`, `PersonalStatementGenerator`, `DenialDecoderService.decode_denial`.
- Prompt construction lives alongside these services; parsing is `_parse_json_response` in `BaseAgent` (strips code fences, JSON loads) or `_parse_analysis` in `AIService` (wraps raw text).

Request/data flow sketches
--------------------------
Path A (Claims upload & analysis):
`/claims/upload` → `claims.views.document_upload` → `claims.forms.DocumentUploadForm` (AI consent + file validation) → save `claims.models.Document` → queue `process_document_task` → OCR (`ocr_service`) → AI (`AIService` or rating/denial analyzers) → persist AI fields/analysis models → user polls via HTMX status endpoints → renders `templates/claims/document_detail.html` and result pages.

Path A (Agent tools – pasted text):
`/agents/decision-analyzer` (form) → POST `/agents/decision-analyzer/analyze/` → `agents.views.decision_analyzer_submit` → create `AgentInteraction` → `DecisionLetterAnalyzer.analyze` (OpenAI) → save `DecisionLetterAnalysis` → render result template.

Path B (VSO case management):
`/vso/` → `vso.views.dashboard` (org-scoped) → case list/detail → interactions (notes/status/checklists) via HTMX endpoints → document review flow pulls `vso.models.SharedDocument` and related `agents` analyses → renders `templates/vso/shared_document_review.html`. Invitations flow generates tokens and emails; acceptance connects veteran to `VeteranCase`.
