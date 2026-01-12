# Contributing to VA Benefits Navigator

Thank you for your interest in contributing to VA Benefits Navigator! This project helps veterans navigate VA disability claims, and every contribution makes a difference.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Beaudoin0zach/benefits_navigator.git
   cd benefits_navigator
   ```

2. **Copy environment template**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker compose up -d
   ```

4. **Run migrations**
   ```bash
   docker compose exec web python manage.py migrate
   ```

5. **Load fixtures**
   ```bash
   docker compose exec web python manage.py loaddata examprep/fixtures/*.json
   ```

6. **Create a superuser**
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## How to Contribute

### Reporting Bugs

- Check existing issues first to avoid duplicates
- Use the bug report template if available
- Include steps to reproduce, expected vs actual behavior
- Include browser/OS information for frontend issues

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the use case and why it helps veterans
- Be open to discussion about implementation approaches

### Contributing Code

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

### Content Contributions

We welcome contributions to:

- **Exam Guides**: C&P exam preparation content
- **Glossary Terms**: VA terminology explanations
- **Secondary Conditions**: Documented condition relationships
- **Appeals Guidance**: Step-by-step appeal instructions

Content should be:
- Accurate and based on official VA sources
- Written in plain, accessible language
- Helpful without providing legal/medical advice

## Pull Request Process

1. **Update documentation** if you change functionality
2. **Add tests** for new features
3. **Follow style guidelines** (see below)
4. **Keep PRs focused** - one feature/fix per PR
5. **Write clear commit messages**

### PR Title Format

```
type: brief description

Examples:
feat: Add TBI exam guide
fix: Correct bilateral factor calculation
docs: Update installation instructions
test: Add rating calculator tests
```

### PR Description

Include:
- What changes were made
- Why the changes were needed
- How to test the changes
- Screenshots for UI changes

## Style Guidelines

### Python

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and small

### Django

- Follow Django conventions for models, views, templates
- Use class-based views where appropriate
- Keep business logic out of views (use services/utilities)

### Templates

- Maintain WCAG AA accessibility
- Use semantic HTML
- Follow existing Tailwind CSS patterns

### JavaScript

- Prefer vanilla JS or HTMX over heavy frameworks
- Keep it simple and accessible

## Testing

### Running Tests

```bash
# All tests
docker compose exec web pytest

# Specific app
docker compose exec web pytest examprep/

# With coverage
docker compose exec web pytest --cov=. --cov-report=html
```

### Writing Tests

- Test file naming: `test_*.py`
- Use pytest fixtures
- Test both success and failure cases
- Mock external services (OpenAI, Stripe)

## Documentation

### Code Documentation

- Add docstrings to public functions/methods
- Comment complex logic
- Update README for new features

### User Documentation

- Write for veterans who may not be tech-savvy
- Use plain language (no jargon)
- Include examples where helpful

## Questions?

- Open an issue for general questions
- Check existing documentation first
- Be patient - maintainers are volunteers

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions

Thank you for helping veterans navigate their benefits!
