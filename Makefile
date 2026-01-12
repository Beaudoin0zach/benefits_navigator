# VA Benefits Navigator - Makefile
# =================================
# Quick commands for development and testing

.PHONY: help test test-unit test-e2e test-bdd test-agents test-coverage test-quick install server

help:
	@echo "VA Benefits Navigator - Available Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-e2e      - Run E2E browser tests"
	@echo "  make test-bdd      - Run BDD scenario tests"
	@echo "  make test-agents   - Run AI testing agents"
	@echo "  make test-coverage - Run tests with coverage"
	@echo "  make test-quick    - Run quick smoke tests"
	@echo ""
	@echo "Development:"
	@echo "  make install       - Install dependencies"
	@echo "  make server        - Run development server"
	@echo "  make shell         - Django shell"
	@echo "  make migrate       - Run migrations"
	@echo ""

# Testing commands
test:
	./scripts/run_tests.sh all

test-unit:
	pytest core accounts claims examprep appeals agents documentation -v --tb=short

test-e2e:
	./scripts/run_tests.sh e2e

test-bdd:
	pytest tests/bdd -v --tb=short

test-agents:
	./scripts/run_tests.sh agents

test-coverage:
	pytest --cov=core --cov=accounts --cov=claims --cov=examprep --cov=appeals --cov=agents --cov=documentation --cov-report=html --cov-report=term-missing

test-quick:
	pytest -x -q core/tests.py::TestHomeView core/tests.py::TestDashboardView --tb=line

# Development commands
install:
	pip install -r requirements.txt
	playwright install chromium

server:
	python manage.py runserver

shell:
	python manage.py shell

migrate:
	python manage.py migrate

# Pre-release validation
pre-release: test-quick test-unit test-bdd
	@echo "Pre-release tests passed!"
