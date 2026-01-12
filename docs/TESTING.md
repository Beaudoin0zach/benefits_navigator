# VA Benefits Navigator - Testing Guide

This document describes the comprehensive testing strategy for the VA Benefits Navigator application.

## Overview

The application uses a multi-layered testing approach:

| Layer | Tool | Purpose |
|-------|------|---------|
| Unit Tests | pytest + Django TestCase | Test individual functions and models |
| Integration Tests | pytest-django | Test component interactions |
| E2E Tests | Playwright | Test complete user flows in browser |
| BDD Tests | pytest-bdd | Human-readable scenario tests |
| AI Agents | Custom Playwright agents | Autonomous exploratory testing |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run all tests
./scripts/run_tests.sh all

# Run specific test types
./scripts/run_tests.sh unit       # Unit tests only
./scripts/run_tests.sh e2e        # Browser tests
./scripts/run_tests.sh bdd        # BDD scenarios
./scripts/run_tests.sh agents     # AI testing agents
./scripts/run_tests.sh coverage   # With coverage report
./scripts/run_tests.sh quick      # Quick smoke tests
```

## Test Types

### 1. Unit Tests

Located in each app's `tests.py` file.

```bash
# Run all unit tests
pytest core accounts claims examprep appeals

# Run specific app tests
pytest examprep/tests.py

# Run specific test class
pytest core/tests.py::TestDashboardView

# Run with verbose output
pytest -v claims/tests.py
```

### 2. End-to-End (E2E) Tests

Browser-based tests in `tests/e2e/`.

```bash
# Run E2E tests (requires server running)
python manage.py runserver &
pytest tests/e2e/

# Run in headed mode (see browser)
E2E_HEADLESS=false pytest tests/e2e/

# Run specific E2E test file
pytest tests/e2e/test_authentication.py
```

**Test Files:**
- `test_authentication.py` - Login, logout, registration
- `test_rating_calculator.py` - Rating calculator workflow
- `test_document_upload.py` - Document management
- `test_appeals.py` - Appeals workflow
- `test_examprep.py` - Exam preparation features
- `test_journey.py` - Journey tracking
- `test_accessibility.py` - WCAG compliance

### 3. BDD Tests

Human-readable scenario tests in `tests/bdd/`.

```bash
# Run BDD tests
pytest tests/bdd/

# Run specific feature
pytest tests/bdd/test_authentication.py
```

**Feature Files** (in `tests/bdd/features/`):
- `authentication.feature`
- `rating_calculator.feature`
- `exam_prep.feature`
- `appeals.feature`
- `documents.feature`
- `journey.feature`

Example feature:
```gherkin
Feature: VA Disability Rating Calculator
  As a veteran
  I want to calculate my combined disability rating
  So that I can understand my potential compensation

  Scenario: Rating calculator is publicly accessible
    Given I am an anonymous user
    When I visit "/examprep/rating-calculator/"
    Then I should see a 200 status
    And I should see "Rating Calculator" on the page
```

### 4. AI Testing Agents

Autonomous agents in `tests/agents/`.

```bash
# Run all agents
python -m tests.agents.run_all_agents

# Run specific agent
python -m tests.agents.explorer_agent --auth
python -m tests.agents.user_journey_agent
python -m tests.agents.chaos_agent

# Run in headed mode
python -m tests.agents.run_all_agents --headed
```

**Available Agents:**

| Agent | Purpose |
|-------|---------|
| `ExplorerAgent` | Crawls app looking for errors |
| `DeepExplorerAgent` | Explores + interacts with forms |
| `UserJourneyAgent` | Tests complete user workflows |
| `ChaosAgent` | Security testing, fuzzing, edge cases |

Reports are saved to `tests/agents/reports/`.

## Test Fixtures

Common fixtures are defined in `conftest.py`:

```python
# User fixtures
@pytest.fixture
def user(db):              # Standard test user
def premium_user(db):      # User with premium subscription
def admin_user(db):        # Superuser
def other_user(db):        # For permission testing

# Client fixtures
@pytest.fixture
def authenticated_client(client, user):  # Logged in client
def premium_client(client, premium_user): # Premium user client

# Model fixtures
@pytest.fixture
def document(db, user):     # Test document
def exam_checklist(db):     # Exam checklist
def appeal(db, user):       # Test appeal
def glossary_term(db):      # Glossary term

# Mock fixtures
@pytest.fixture
def mock_openai():          # Mock OpenAI API
def mock_celery():          # Mock Celery tasks
def mock_ocr():             # Mock OCR service
```

## Coverage

```bash
# Generate coverage report
pytest --cov=core --cov=accounts --cov=claims --cov=examprep \
       --cov=appeals --cov=agents --cov=documentation \
       --cov-report=html

# View report
open htmlcov/index.html
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    pip install -r requirements.txt
    playwright install chromium
    pytest --tb=short -q

# With coverage
- name: Run Tests with Coverage
  run: |
    pytest --cov --cov-report=xml
```

## Test Configuration

Configuration in `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = benefits_navigator.settings
python_files = tests.py test_*.py
addopts = --strict-markers -v --tb=short
markers =
    slow: marks tests as slow
    e2e: end-to-end browser tests
    bdd: BDD scenario tests
```

## Writing New Tests

### Unit Test Example

```python
# In app/tests.py
import pytest
from django.test import Client

class TestMyFeature:
    def test_something_works(self, authenticated_client):
        response = authenticated_client.get('/my-feature/')
        assert response.status_code == 200
        assert 'expected text' in response.content.decode()
```

### E2E Test Example

```python
# In tests/e2e/test_my_feature.py
from playwright.sync_api import Page, expect

class TestMyFeature:
    def test_user_can_do_thing(self, authenticated_page: Page):
        page = authenticated_page
        page.goto('/my-feature/')
        page.click('button:has-text("Do Thing")')
        expect(page.locator('.success')).to_be_visible()
```

### BDD Test Example

```gherkin
# In tests/bdd/features/my_feature.feature
Feature: My Feature
  Scenario: User does something
    Given I am logged in
    When I visit "/my-feature/"
    Then I should see "Welcome" on the page
```

## Pre-Release Checklist

Before releasing to test users, run:

```bash
# 1. Full test suite
./scripts/run_tests.sh all

# 2. E2E tests
./scripts/run_tests.sh e2e

# 3. AI agents (finds edge cases)
./scripts/run_tests.sh agents

# 4. Coverage report (aim for >80%)
./scripts/run_tests.sh coverage

# 5. Quick smoke test
./scripts/run_tests.sh quick
```

## Troubleshooting

### E2E Tests Failing

1. Ensure Django server is running: `python manage.py runserver`
2. Check test user exists: `python manage.py shell -c "from accounts.models import User; print(User.objects.filter(email='e2e_test@example.com').exists())"`
3. Run in headed mode to see what's happening: `E2E_HEADLESS=false pytest tests/e2e/`

### BDD Tests Failing

1. Check step definitions in `tests/bdd/conftest.py`
2. Ensure database fixtures are created

### Agent Tests Timing Out

1. Increase timeout: Edit `max_pages` in agent constructor
2. Check server is responding: `curl http://localhost:8000`
