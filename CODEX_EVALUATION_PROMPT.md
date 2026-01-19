# Benefits Navigator - Developer Evaluation Prompt

## Context

You are evaluating **Benefits Navigator**, a Django web application that helps veterans navigate VA disability benefits claims. The app provides AI-powered document analysis, case management for Veterans Service Organizations (VSOs), and secure handling of sensitive personal information.

## Evaluation Objectives

Please perform a comprehensive developer evaluation of this codebase, focusing on:

### 1. Architecture & Code Quality

- **Project Structure**: Evaluate the Django app organization (accounts, agents, appeals, claims, core, documentation, examprep, vso)
- **Design Patterns**: Assess use of Django best practices, separation of concerns, DRY principles
- **Code Readability**: Review naming conventions, documentation, and code organization
- **Maintainability**: Identify areas that may be difficult to maintain or extend

### 2. Security Assessment

- **PII Handling**: Review the encryption implementation in `core/encryption.py` for VA file numbers, dates of birth, and other sensitive data
- **Authentication & Authorization**: Evaluate the role-based permission system in `vso/permissions.py`
- **CSRF/XSS Protection**: Check for proper Django security middleware usage
- **SQL Injection**: Verify ORM usage and any raw SQL queries (check migrations)
- **Secret Management**: Review how API keys and secrets are handled
- **File Upload Security**: Assess document upload validation in claims app

### 3. AI Integration

- **OpenAI API Usage**: Review `claims/services/rating_analysis_service.py` for prompt engineering quality
- **Privacy Disclosure**: Evaluate the AI consent system in `accounts/views.py` and `templates/accounts/privacy_settings.html`
- **Confidence Scoring**: Assess the AI confidence scoring implementation in `agents/models.py`
- **Error Handling**: Check how AI failures are handled gracefully

### 4. Database Design

- **Model Relationships**: Review models in accounts, claims, vso, and agents apps
- **Migration Strategy**: Check migration files for data integrity considerations
- **Query Performance**: Look for N+1 queries, missing indexes, or inefficient queries
- **Data Encryption**: Verify encrypted field implementations work correctly

### 5. User Experience & Accessibility

- **Template Quality**: Review templates for accessibility (ARIA labels, semantic HTML)
- **Error Messages**: Check user-facing error handling
- **VSO Consultation Prompts**: Evaluate `templates/components/vso_consultation_prompt.html` for helpfulness

### 6. Testing & Quality Assurance

- **Test Coverage**: Identify what tests exist and what's missing
- **Test Quality**: Assess test patterns and mocking strategies
- **CI/CD Readiness**: Check for deployment configuration (app.yaml, Dockerfile)

### 7. Performance Considerations

- **Async Tasks**: Review Celery task implementations
- **Caching Strategy**: Check for Redis usage and caching patterns
- **Static Asset Handling**: Review static file configuration

## Key Files to Review

```
# Core Security
core/encryption.py                    # PII encryption (Fernet/AES-256)
vso/permissions.py                    # Role-based access control

# AI Integration
claims/services/rating_analysis_service.py  # OpenAI analysis service
agents/models.py                            # Analysis result storage

# User-Facing
templates/accounts/privacy_settings.html    # AI consent UI
templates/claims/rating_analyzer_result.html # Analysis display
templates/components/vso_consultation_prompt.html # VSO prompts

# Models
accounts/models.py                    # User, Profile, Organization
vso/models.py                         # Case, SharedDocument
claims/models.py                      # Document storage

# Configuration
benefits_navigator/settings.py        # Django settings
app.yaml                              # Google Cloud deployment
```

## Specific Questions to Answer

1. **Is the PII encryption implementation secure?** Review the Fernet key derivation from SECRET_KEY and the EncryptedCharField/EncryptedDateField implementations.

2. **Are there any OWASP Top 10 vulnerabilities?** Specifically check for injection, broken auth, sensitive data exposure, and security misconfigurations.

3. **Is the role-based permission system robust?** Can users bypass VSO staff checks? Are there authorization gaps?

4. **Is the AI prompt injection-resistant?** Review how user document text is passed to OpenAI.

5. **Are database migrations reversible and safe?** Check the data migration for encrypting existing PII.

6. **Is the consent system GDPR-compliant?** Review how AI processing consent is tracked and enforced.

7. **What's missing for production readiness?** Identify gaps in logging, monitoring, rate limiting, etc.

## Output Format

Please provide your evaluation as:

```markdown
## Executive Summary
[2-3 paragraph overview of findings]

## Critical Issues (Must Fix)
- Issue 1: [Description, location, recommended fix]
- Issue 2: ...

## High Priority Improvements
- Improvement 1: [Description, benefit, effort estimate]
- ...

## Code Quality Observations
- Positive: [What's done well]
- Negative: [What needs improvement]

## Security Audit Results
- [Detailed security findings with severity ratings]

## Recommendations
1. [Prioritized list of recommended changes]

## Questions for the Development Team
- [Questions that need clarification]
```

## Additional Context

- The app targets veterans navigating VA disability claims
- VSO = Veterans Service Organization (provides free claims assistance)
- The app analyzes VA rating decisions and denial letters using AI
- Multi-tenant architecture: veterans can be associated with VSO organizations
- PII includes VA file numbers (similar to SSN), dates of birth, medical information

## Run the Evaluation

To explore the codebase:

```bash
# Check project structure
find . -type f -name "*.py" | head -50

# Review models
cat accounts/models.py
cat vso/models.py
cat claims/models.py

# Review security
cat core/encryption.py
cat vso/permissions.py

# Review AI integration
cat claims/services/rating_analysis_service.py

# Check for tests
find . -name "test*.py" -o -name "*_test.py"

# Review migrations
ls -la */migrations/*.py

# Check settings
cat benefits_navigator/settings.py
```

Begin your evaluation now.
