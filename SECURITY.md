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
- Use 1Password CLI (op) for production credentials
- Use environment variables (`.env`) for development/testing only
- Add `.env` files to `.gitignore`

### Credential Management with 1Password CLI

**Production (Recommended)**: This project uses 1Password CLI (`op`) for secure credential management with automatic fallback to `.env` files for development.

#### Setup 1Password CLI

1. **Install 1Password CLI**:
   ```bash
   # macOS
   brew install --cask 1password-cli
   
   # Linux
   # Download from: https://1password.com/downloads/command-line/
   
   # Windows
   # Download from: https://1password.com/downloads/command-line/
   ```

2. **Sign in to 1Password**:
   ```bash
   op signin
   ```

3. **Store credentials in 1Password**:
   - Create a vault named "AI" in 1Password
   - Add items for each service (Supabase, Missive, Twilio, etc.)
   - Store credentials as fields within these items
   - Supported field names: `password`, `secret`, `token`, `api_key`, `key`

#### How It Works

The project automatically:
1. **First**: Tries to load credentials from 1Password CLI
2. **Fallback**: Falls back to `.env` file if 1Password is not available
3. **Error**: Raises clear error if credential not found in either location

Example from code:
```python
from utils.secrets_loader import load_secret

# Loads from 1Password "AI" vault, falls back to .env
SUPABASE_KEY = load_secret(
    'SUPABASE_KEY',
    vault='AI',
    item_names=['Supabase', 'Premium Gastro'],
    field_names=['SUPABASE_KEY', 'api_key', 'service_key', 'password']
)
```

### Development with .env Files

For development/testing when 1Password CLI is not installed:

```python
# Create .env file (never commit this!)
# The secrets loader will automatically fall back to .env

# .env file contents:
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_key
MISSIVE_API_TOKEN=your_missive_token
```

**Note**: The loader logs where each credential was loaded from:
- `INFO: Loaded secret from 1Password: vault='AI', item='Supabase', field='api_key'`
- `INFO: Loaded SUPABASE_KEY from .env file`

### Required Credentials

Create credentials in 1Password "AI" vault or `.env` file (see `env.example`):

**Supabase**:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - API key (service role or anon key)

**Missive**:
- `MISSIVE_API_TOKEN` - Missive API authentication token
- `MISSIVE_ORG_ID` - Your Missive organization ID

**Twilio**:
- `TWILIO_SID` - Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Twilio authentication token

**AI Services**:
- `GEMINI_API_KEY` - Google Gemini API key
- `HUGGING_FACE_TOKEN` - Hugging Face access token

**Other Services**:
- `LINDY_API_KEY` - Lindy AI API key
- `WHATSAPP_PHONE` - WhatsApp Business phone number

## Security Improvements

### Addressed in This Version

✅ **GHSA-658q-wh8w-4cqm** - Migrated from `.env`-only to 1Password CLI with `.env` fallback:
- Production systems use 1Password for credential storage
- Development systems can use `.env` files
- Clear audit trail via logging
- Graceful degradation when 1Password unavailable
- Comprehensive error messages

### Benefits of 1Password CLI Integration

1. **Centralized Secret Management**: All secrets in one secure vault
2. **No Secrets in Code**: Credentials never touch version control
3. **Audit Trail**: Know where each credential was loaded from
4. **Team Sharing**: Share credentials securely via 1Password
5. **Rotation**: Easy credential rotation without code changes
6. **Development Flexibility**: `.env` fallback for local testing

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
- Regularly rotate credentials in 1Password
- Monitor 1Password CLI logs for unauthorized access attempts
