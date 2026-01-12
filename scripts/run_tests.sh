#!/bin/bash
# =============================================================================
# VA Benefits Navigator - Test Runner Script
# =============================================================================
#
# Usage:
#   ./scripts/run_tests.sh [command] [options]
#
# Commands:
#   all        - Run all tests
#   unit       - Run unit tests only
#   e2e        - Run end-to-end browser tests
#   bdd        - Run BDD scenario tests
#   agents     - Run AI testing agents
#   coverage   - Run tests with coverage report
#   quick      - Run quick smoke tests
#   parallel   - Run tests in parallel
#
# Options:
#   --headed   - Run browser tests in headed mode
#   --verbose  - Verbose output
#   --app=X    - Test specific app (core, claims, examprep, appeals, etc.)
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# Default values
COMMAND="${1:-all}"
VERBOSE=""
HEADED=""
APP=""

# Parse additional arguments
shift || true
for arg in "$@"; do
    case $arg in
        --headed)
            HEADED="--headed"
            export E2E_HEADLESS=false
            ;;
        --verbose|-v)
            VERBOSE="-v"
            ;;
        --app=*)
            APP="${arg#*=}"
            ;;
    esac
done

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if server is running for E2E tests
check_server() {
    if ! curl -s http://localhost:8000 > /dev/null 2>&1; then
        print_warning "Django server not running. Starting it..."
        python manage.py runserver &
        SERVER_PID=$!
        sleep 3
        trap "kill $SERVER_PID 2>/dev/null" EXIT
    fi
}

# Run commands
case $COMMAND in
    all)
        print_header "Running All Tests"

        # Unit tests
        print_header "Unit & Integration Tests"
        if [ -n "$APP" ]; then
            pytest "$APP" $VERBOSE --tb=short
        else
            pytest core accounts claims examprep appeals agents documentation $VERBOSE --tb=short
        fi

        # BDD tests
        print_header "BDD Scenario Tests"
        pytest tests/bdd $VERBOSE --tb=short

        print_success "All tests completed!"
        ;;

    unit)
        print_header "Running Unit Tests"
        if [ -n "$APP" ]; then
            pytest "$APP" $VERBOSE --tb=short
        else
            pytest core accounts claims examprep appeals agents documentation $VERBOSE --tb=short
        fi
        ;;

    e2e)
        print_header "Running E2E Browser Tests"
        check_server

        # Install playwright browsers if needed
        playwright install chromium 2>/dev/null || true

        pytest tests/e2e $VERBOSE $HEADED --tb=short
        ;;

    bdd)
        print_header "Running BDD Scenario Tests"
        pytest tests/bdd $VERBOSE --tb=short
        ;;

    agents)
        print_header "Running AI Testing Agents"
        check_server

        # Install playwright browsers if needed
        playwright install chromium 2>/dev/null || true

        echo -e "\n${YELLOW}Running Explorer Agent...${NC}"
        python -m tests.agents.explorer_agent --auth

        echo -e "\n${YELLOW}Running User Journey Agent...${NC}"
        python -m tests.agents.user_journey_agent

        echo -e "\n${YELLOW}Running Chaos Agent...${NC}"
        python -m tests.agents.chaos_agent

        print_success "Agent testing completed! Check tests/agents/*.json for reports."
        ;;

    coverage)
        print_header "Running Tests with Coverage"
        pytest --cov=core --cov=accounts --cov=claims --cov=examprep --cov=appeals --cov=agents --cov=documentation \
               --cov-report=term-missing \
               --cov-report=html:htmlcov \
               $VERBOSE

        print_success "Coverage report generated in htmlcov/"
        ;;

    quick)
        print_header "Running Quick Smoke Tests"

        # Just run critical path tests
        pytest -x -q \
            core/tests.py::TestHomeView \
            core/tests.py::TestDashboardView \
            accounts/tests.py -k "login" \
            examprep/tests.py -k "calculator" \
            --tb=line

        print_success "Smoke tests passed!"
        ;;

    parallel)
        print_header "Running Tests in Parallel"
        pytest -n auto $VERBOSE --tb=short
        ;;

    watch)
        print_header "Running Tests in Watch Mode"
        print_warning "Install pytest-watch: pip install pytest-watch"
        ptw -- $VERBOSE
        ;;

    *)
        echo "VA Benefits Navigator Test Runner"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  all        Run all tests (default)"
        echo "  unit       Run unit tests only"
        echo "  e2e        Run end-to-end browser tests"
        echo "  bdd        Run BDD scenario tests"
        echo "  agents     Run AI testing agents"
        echo "  coverage   Run tests with coverage report"
        echo "  quick      Run quick smoke tests"
        echo "  parallel   Run tests in parallel"
        echo ""
        echo "Options:"
        echo "  --headed   Run browser tests in headed mode"
        echo "  --verbose  Verbose output"
        echo "  --app=X    Test specific app"
        ;;
esac
