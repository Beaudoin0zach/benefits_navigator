VA Benefits Navigator – Contracts
=================================

Path A (Veterans) contracts
---------------------------
- Document upload → processing
  - Entry: `claims.views.document_upload` accepts POST with `file`, `document_type`, `ai_consent`. Requires authenticated user.
  - Validation: `claims.forms.DocumentUploadForm` enforces file type/size (settings `MAX_DOCUMENT_SIZE`, `ALLOWED_DOCUMENT_TYPES`), python-magic content check, page-count cap (`MAX_DOCUMENT_PAGES`), usage limits (`accounts.models.UsageTracking`), and AI consent (`UserProfile.ai_processing_consent`).
  - Side-effects: creates `claims.models.Document` with status `uploading`; queues `claims.tasks.process_document_task(document_id)`.
  - Expectation: background task sets `Document.status` to processing/analyzing/completed/failed and fills OCR/AI fields. Frontend polls `claims.views.document_status` (HTMX/JSON) and renders `templates/claims/partials/document_status.html`.
- Denial decoder flow
  - Entry: `claims.views.denial_decoder_upload` (POST file) → queues `claims.tasks.decode_denial_letter_task(document_id)`.
  - Task contract: requires `UserProfile.ai_processing_consent`; performs OCR if needed, runs `agents.services.DecisionLetterAnalyzer.analyze`, writes `AgentInteraction`, `DecisionLetterAnalysis`, optionally `DenialDecoding`; marks document complete or failed.
  - Status polling via `claims.views.denial_decoder_status`; results rendered in `templates/claims/denial_decoder_result.html`.
- Rating analyzer flow
  - Entry: `claims.views.rating_analyzer_upload` (POST file) → queues `claims.tasks.analyze_rating_decision_task(document_id, use_simple_format=False)`.
  - Task contract: requires AI consent; OCR if absent; uses `RatingDecisionAnalyzer` (structured) or `SimpleRatingAnalyzer` (markdown). Writes `AgentInteraction` + `agents.models.RatingAnalysis`; updates document status.
  - Status polling via `claims.views.rating_analyzer_status`; results page `templates/claims/rating_analyzer_result.html`.
- Document sharing to VSOs
  - Entry: `claims.views.document_share` (POST case_id, include_ai_analysis) with authenticated veteran.
  - Preconditions: veteran must belong to active `vso.models.VeteranCase` (not closed). Duplicate shares blocked.
  - Side-effects: creates `vso.models.SharedDocument(status='pending', include_ai_analysis=bool)`; VSO review via `vso.views.shared_document_review`.

Path B (VSOs) contracts
-----------------------
- Access control: All `vso.views.*` (except `accept_invitation`) wrapped by `vso.permissions.vso_staff_required` which checks active `accounts.models.OrganizationMembership` (role admin|caseworker) scoped to organization.
- Case CRUD:
  - `vso.views.case_create` requires title + veteran email; requires existing user (placeholder creation rejected). Creates `vso.models.VeteranCase` + initial `CaseNote`.
  - `vso.views.case_update_status`/`add_case_note`/`complete_action_item` expect POST, scoped to organization of authenticated staff; add CaseNote entries and status transitions; optional visibility to veteran.
- Invitations:
  - `vso.views.invite_veteran` accepts email, optional case metadata; creates `accounts.models.OrganizationInvitation` token and stores pending case data in session; sends email via `_send_veteran_invitation_email`.
  - Resend/cancel require staff in same org and pending invitation.
  - Acceptance (`vso.views.accept_invitation`) requires login; email must match invitation; sets `accepted_at`, optionally creates `VeteranCase` from session data, adds CaseNote.

OpenAI wrapper contracts
------------------------
- `agents/services.py:BaseAgent._call_openai(system_prompt, user_prompt, temperature=0.3) -> (content:str, tokens:int)`  
  - Uses `OpenAI(api_key=settings.OPENAI_API_KEY).chat.completions.create(model=settings.OPENAI_MODEL, max_tokens=settings.OPENAI_MAX_TOKENS)`. No retries or timeout override.  
  - `_parse_json_response` extracts JSON (strips code fences).  
  - Implementations must sanitize user input (`sanitize_user_input`), keep outputs JSON-loadable, and attach `_tokens_used`/`_cost_estimate` when returning dicts.
- `claims/services/ai_service.py:AIService.analyze_document(text, document_type) -> {'analysis': dict, 'model': str, 'tokens_used': int}`  
  - Builds system/user prompts per document_type (decision letters use `RATING_DECISION_*` prompts). Sanitizes text via `sanitize_document_text`, truncates to `OPENAI_MAX_TOKENS - 1000` (approx via char count). Parses by wrapping raw response into `{'summary': <text>, 'raw_response': <text>, 'structured': True}` without schema validation.
- `claims/services/rating_analysis_service.py:RatingDecisionAnalyzer.analyze(document_text, decision_date=None)`  
  - Extraction phase: sanitized text → `EXTRACTION_PROMPT` → `_call_openai(temperature=0.1)` expects pure JSON; parsed via `_parse_json_response`.  
  - Analysis phase: extracted JSON + optional condition-specific guidance → `ANALYSIS_PROMPT` → `_call_openai(temperature=0.3)` expects pure JSON; parsed similarly.  
  - Returns `RatingAnalysisResult` with tokens/cost; tasks persist fields into `agents.models.RatingAnalysis`.  
  - Simple path `SimpleRatingAnalyzer.analyze` returns markdown string + tokens using `ACTIONABLE_ANALYSIS_PROMPT`.

Storage boundaries
------------------
- Documents stored via `Document.file` (under `documents/user_<id>/…`). OCR text + AI outputs persisted in DB (`Document.ocr_text`, `ai_summary`, analysis models). Audit events recorded in `core.models.AuditLog` for access. Data retention jobs purge soft-deleted documents and old analyses per `core.models.DataRetentionPolicy`.
