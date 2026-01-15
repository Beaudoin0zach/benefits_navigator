# Security Policy

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in VA Benefits Navigator, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please email security concerns to: **security@benefitsnavigator.com**

Or use GitHub's private vulnerability reporting feature if enabled.

### What to Include

When reporting a vulnerability, please include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Suggested fix** (if you have one)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Target**: Within 30 days for critical issues

### Scope

This security policy applies to:

- The VA Benefits Navigator web application
- All code in this repository
- Associated deployment configurations

### Out of Scope

- Third-party services (OpenAI, Stripe, AWS)
- User-provided content or documents
- Issues in dependencies (report to upstream maintainers)

## Security Best Practices

### For Deployers

1. **Never commit secrets** - Use environment variables for all sensitive data
2. **Use HTTPS** - Always deploy with TLS/SSL in production
3. **Keep dependencies updated** - Regularly run `pip-audit` or similar tools
4. **Set strong SECRET_KEY** - Generate a unique, random key for production
5. **Configure ALLOWED_HOSTS** - Restrict to your actual domain(s)
6. **Enable CSP headers** - Already configured, verify in production

### For Contributors

1. **No hardcoded credentials** - Always use environment variables
2. **Validate all input** - Especially file uploads and user-provided data
3. **Use parameterized queries** - Django ORM handles this, avoid raw SQL
4. **Follow OWASP guidelines** - Be aware of common vulnerabilities

## Data Handling

### What We Store

- User account information (email, hashed passwords)
- Uploaded documents (encrypted at rest in production)
- Analysis results and saved calculations

### What We Don't Store

- Payment card numbers (handled by Stripe)
- OpenAI API keys (provided by deployer via environment variable, never stored in database)

### Data Retention

- User data is retained until account deletion is requested
- Uploaded documents can be deleted by users at any time
- Soft-deleted data is permanently purged after 30 days

## Disclaimer

This application is intended for **educational and informational purposes only**. It is not intended to store or process Protected Health Information (PHI) under HIPAA. Users should not upload documents containing sensitive medical information to public or shared deployments.

For production deployments handling sensitive veteran data, additional security measures and compliance requirements may apply.
