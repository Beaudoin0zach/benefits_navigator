Next Steps (staged)
===================

1) Enforce AI consent everywhere  
   - Add consent check and UI gating to `agents.views.*` submit handlers; block OpenAI calls when consent absent; log consent events.

2) Harden OpenAI wrapper and validation  
   - Centralize sanitization + timeouts/retries in `BaseAgent._call_openai` and reuse in `AIService`; add JSON schema validation for each analysis before save; surface structured errors to status endpoints.

3) Tighten data exposure controls  
   - Gate/trim `document_analysis` GraphQL response (mask VA file numbers/SSN patterns, length cap); default `include_ai_analysis` to opt-in for document sharing; add AuditLog entries for AI runs and VSO shares.

4) Improve org scoping for VSO users  
   - Require explicit organization selection (slug in URL or session) and verify per-request in `vso.views`; adjust templates/links accordingly; add tests for multi-org users.

5) Shore up background job reliability and observability  
   - Add timeouts to OCR/OpenAI calls, clearer task error states, and monitoring for dependency failures (python-magic, PyMuPDF). Ensure retention tasks are scheduled and visible.

6) Expand automated tests for core flows  
   - Add mocks for OpenAI and write tests for claims upload → task dispatch, denial/rating analyzers, VSO invitations/access control, and GraphQL/HTMX endpoints. Include CI job to run them.
