# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it by:

1. **Email**: Contact the maintainer privately (do NOT create a public issue)
2. **GitHub Security Advisory**: Use GitHub's private vulnerability reporting feature

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Best Practices

This project handles sensitive data. Contributors should:

### Never Hardcode Credentials

- **Never** commit API keys, passwords, or secrets to the repository
- Use environment variables for all sensitive configuration
- Add `.env` files to `.gitignore`

### Environment Variables

All sensitive configuration should be loaded from environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Good: Load from environment
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Bad: Hardcoded (NEVER do this)
# SUPABASE_SERVICE_KEY = 'eyJhbGci...'
```

### Required Environment Variables

Create a `.env` file with these variables (see `.env.example`):

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key
```

## Known Security Issues

For current security advisories, see:
https://github.com/darkangelpraha/premium-gastro-ai-assistant/security/advisories

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Security Updates

- Enable Dependabot alerts in repository settings
- Review and merge security patches promptly
- Follow GitHub's security best practices
