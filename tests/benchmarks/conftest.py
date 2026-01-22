"""
Benchmark test fixtures and configuration.

Provides mocked services to ensure benchmarks are deterministic and don't
hit external services (OpenAI, etc.).
"""

import json
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

User = get_user_model()


# =============================================================================
# Benchmark Results Storage
# =============================================================================

BENCHMARK_RESULTS = {}


def record_benchmark(name: str, duration: float):
    """Record a benchmark result."""
    BENCHMARK_RESULTS[name] = {
        'name': name,
        'time': duration,
        'mean': duration,
    }


@pytest.fixture(scope="session", autouse=True)
def save_benchmark_results(request):
    """Save benchmark results to JSON after all tests complete."""
    yield

    # Save results after session
    results_file = Path("benchmark-results.json")
    results = {
        'tests': BENCHMARK_RESULTS,
        'timestamp': time.time(),
    }
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def benchmark_user(db):
    """Create a user for benchmark tests."""
    user, _ = User.objects.get_or_create(
        email='benchmark@test.com',
        defaults={
            'first_name': 'Benchmark',
            'last_name': 'User',
        }
    )
    user.set_password('BenchmarkPassword123!')
    user.save()

    # Grant AI consent
    if hasattr(user, 'profile'):
        user.profile.ai_processing_consent = True
        user.profile.save()

    return user


@pytest.fixture
def authenticated_client(db, benchmark_user):
    """Create an authenticated client for benchmark tests."""
    client = Client()
    client.login(email='benchmark@test.com', password='BenchmarkPassword123!')
    return client


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls to prevent network requests."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        'summary': 'Test analysis summary',
        'key_findings': ['Finding 1', 'Finding 2'],
    })
    mock_response.usage.total_tokens = 100

    with patch('openai.OpenAI') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.fixture
def mock_celery():
    """Mock Celery to prevent async task execution."""
    with patch('claims.tasks.process_document_task.delay') as mock_task:
        mock_task.return_value = MagicMock(id='test-task-id')
        yield mock_task


@pytest.fixture
def sample_pdf_file():
    """Create a minimal PDF file for upload tests."""
    # Minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
170
%%EOF"""

    return SimpleUploadedFile(
        name="benchmark_test.pdf",
        content=pdf_content,
        content_type="application/pdf"
    )
