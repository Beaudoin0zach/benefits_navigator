#!/usr/bin/env python3
"""
Security Invariants Checker

Static analysis script that verifies security invariants are maintained.
Run by CI on every PR and push to main.

Usage:
    python scripts/check_security_invariants.py
    python scripts/check_security_invariants.py --verbose

Exit codes:
    0 - All checks passed
    1 - One or more violations found
"""

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Violation:
    """A security invariant violation."""
    check: str
    file: str
    line: int
    message: str
    severity: str = "error"  # error, warning

    def __str__(self):
        return f"[{self.severity.upper()}] {self.file}:{self.line} - {self.check}: {self.message}"


class SecurityChecker:
    """Runs security invariant checks against the codebase."""

    def __init__(self, root_dir: Path, verbose: bool = False):
        self.root_dir = root_dir
        self.verbose = verbose
        self.violations: List[Violation] = []

    def log(self, message: str):
        """Print message if verbose mode enabled."""
        if self.verbose:
            print(f"  {message}")

    def add_violation(self, check: str, file: str, line: int, message: str, severity: str = "error"):
        """Record a violation."""
        self.violations.append(Violation(check, file, line, message, severity))

    def run_all_checks(self) -> bool:
        """Run all security checks. Returns True if all pass."""
        print("Running security invariant checks...")
        print()

        self.check_prohibited_phi_fields()
        self.check_sentry_pii_config()
        self.check_logging_pitfalls()
        self.check_phi_in_logging()

        print()
        if self.violations:
            print(f"FAILED: {len(self.violations)} violation(s) found")
            print()
            for v in self.violations:
                print(f"  {v}")
            return False
        else:
            print("PASSED: All security invariants verified")
            return True

    # =========================================================================
    # Check 1: Prohibited PHI Fields
    # =========================================================================

    def check_prohibited_phi_fields(self):
        """Ensure prohibited PHI fields don't exist in model definitions."""
        print("[1/4] Checking for prohibited PHI fields in models...")

        # Patterns that indicate field definitions (not comments or strings)
        prohibited_patterns = [
            # Django model field definitions
            (r'^\s*ocr_text\s*=\s*models\.', 'ocr_text field definition'),
            (r'^\s*raw_text\s*=\s*models\.', 'raw_text field definition'),
            # Also check for TextField/CharField with these names
            (r'models\.\w+Field\([^)]*["\']ocr_text["\']', 'ocr_text field'),
            (r'models\.\w+Field\([^)]*["\']raw_text["\']', 'raw_text field'),
        ]

        # Files to check
        model_files = [
            self.root_dir / "claims" / "models.py",
            self.root_dir / "agents" / "models.py",
        ]

        for model_file in model_files:
            if not model_file.exists():
                continue

            self.log(f"Scanning {model_file.relative_to(self.root_dir)}")

            with open(model_file, 'r') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue

                for pattern, desc in prohibited_patterns:
                    if re.search(pattern, line):
                        self.add_violation(
                            "PHI_FIELD",
                            str(model_file.relative_to(self.root_dir)),
                            line_num,
                            f"Prohibited PHI field detected: {desc}. "
                            f"Raw OCR/document text must not be stored in DB."
                        )

    # =========================================================================
    # Check 2: Sentry PII Configuration
    # =========================================================================

    def check_sentry_pii_config(self):
        """Ensure Sentry is not configured to send default PII."""
        print("[2/4] Checking Sentry PII configuration...")

        settings_file = self.root_dir / "benefits_navigator" / "settings.py"
        if not settings_file.exists():
            self.log("Settings file not found, skipping")
            return

        self.log(f"Scanning {settings_file.relative_to(self.root_dir)}")

        with open(settings_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')

        # Check for send_default_pii=True
        for line_num, line in enumerate(lines, 1):
            if 'send_default_pii' in line and 'True' in line:
                # Make sure it's not a comment or in a False context
                stripped = line.strip()
                if not stripped.startswith('#') and 'send_default_pii=True' in line.replace(' ', ''):
                    self.add_violation(
                        "SENTRY_PII",
                        str(settings_file.relative_to(self.root_dir)),
                        line_num,
                        "Sentry configured with send_default_pii=True. "
                        "This must be False to prevent PII leakage."
                    )

    # =========================================================================
    # Check 3: Logging Pitfalls
    # =========================================================================

    def check_logging_pitfalls(self):
        """Check for common logging patterns that might leak sensitive data."""
        print("[3/4] Checking for logging pitfalls...")

        # Patterns that might log request bodies or sensitive data
        pitfall_patterns = [
            (r'log.*\(.*request\.body', 'Logging request.body may contain PII'),
            (r'log.*\(.*request\.POST', 'Logging request.POST may contain PII'),
            (r'log.*\(.*request\.data', 'Logging request.data may contain PII'),
            (r'print\s*\(.*request\.body', 'Printing request.body may contain PII'),
            (r'print\s*\(.*request\.POST', 'Printing request.POST may contain PII'),
        ]

        python_files = list(self.root_dir.glob("**/*.py"))
        # Exclude migrations, tests, venv, and this script
        python_files = [
            f for f in python_files
            if 'migration' not in str(f)
            and 'venv' not in str(f)
            and '__pycache__' not in str(f)
            and 'check_security_invariants' not in str(f)
        ]

        for py_file in python_files:
            self.log(f"Scanning {py_file.relative_to(self.root_dir)}")

            try:
                with open(py_file, 'r') as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue

                for pattern, message in pitfall_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.add_violation(
                            "LOGGING_PITFALL",
                            str(py_file.relative_to(self.root_dir)),
                            line_num,
                            message,
                            severity="warning"
                        )

    # =========================================================================
    # Check 4: PHI in Logging Statements
    # =========================================================================

    def check_phi_in_logging(self):
        """Check for logging statements that might include PHI fields."""
        print("[4/4] Checking for PHI in logging statements...")

        # Field names that should never appear in logging
        phi_fields = [
            'ocr_text',
            'raw_text',
            'document_text',
            'ssn',
            'social_security',
            'file_number',
            'va_file_number',
        ]

        # Build pattern
        phi_pattern = '|'.join(phi_fields)
        logging_with_phi = re.compile(
            rf'(logger?\.|logging\.)\w+\s*\([^)]*({phi_pattern})',
            re.IGNORECASE
        )

        python_files = list(self.root_dir.glob("**/*.py"))
        python_files = [
            f for f in python_files
            if 'migration' not in str(f)
            and 'venv' not in str(f)
            and '__pycache__' not in str(f)
            and 'check_security' not in str(f)  # Exclude this script
        ]

        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue

                if logging_with_phi.search(line):
                    self.add_violation(
                        "PHI_LOGGING",
                        str(py_file.relative_to(self.root_dir)),
                        line_num,
                        "Logging statement may include PHI field. "
                        "Remove sensitive data from log output."
                    )


def main():
    parser = argparse.ArgumentParser(description="Check security invariants")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    parser.add_argument('--root', type=str, default='.', help="Project root directory")
    args = parser.parse_args()

    root_dir = Path(args.root).resolve()

    # Verify we're in the right directory
    if not (root_dir / "manage.py").exists():
        print(f"Error: {root_dir} does not appear to be a Django project")
        sys.exit(1)

    checker = SecurityChecker(root_dir, verbose=args.verbose)
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
