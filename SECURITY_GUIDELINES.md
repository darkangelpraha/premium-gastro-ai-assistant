# Security Guidelines for Premium Gastro AI Assistant

## ⚠️ ZERO TOLERANCE POLICY

**ABSOLUTE RULE: NO CREDENTIALS IN FILES - EVER!**

**STRICTLY PROHIBITED:**
- ❌ **ZERO placeholders** in .env files - ALL values MUST reference 1Password
- ❌ **ZERO credentials** stored in any file (.env, config, scripts, etc.)
- ❌ Commit credentials to Git
- ❌ Share API keys in chat/email/Slack
- ❌ Hard-code secrets in source code
- ❌ Store credentials in code comments
- ❌ Push `.env` file to GitHub (even with placeholders)
- ❌ Screenshot or log sensitive data
- ❌ Share credentials with Claude in prompts
- ❌ Include real keys in documentation

**ONLY ACCEPTABLE METHOD:**
✅ Fetch credentials from 1Password CLI (`op`) on-demand
✅ Use 1Password item IDs in code (IDs are safe, not secrets)
✅ Clear credentials from memory immediately after use

---

## ✅ Secure Credential Management

### 1. Use 1Password CLI EXCLUSIVELY

**Store in 1Password:**
- API keys (Claude, OpenAI, Bluejet, etc.)
- Database credentials (Supabase)
- Email/messaging service tokens
- Webhook secrets
- OAuth tokens
- Any sensitive configuration

**1Password Structure:**
```
Premium Gastro Vault/
├── AI Services/
│   ├── Claude API Key
│   ├── OpenAI API Key
│   └── Anthropic Account
├── Bluejet/
│   ├── Bluejet API Key
│   ├── Bluejet API Secret
│   └── Bluejet Workspace ID
├── Database/
│   ├── Supabase URL
│   ├── Supabase Key
│   └── Supabase Service Role Key
└── Communication/
    ├── Missive API Token
    ├── Twilio Auth Token
    └── Slack Webhook URL
```

### 2. Environment Variables (.env)

**File**: `/home/user/premium-gastro-ai-assistant/.env`

**Never committed to Git** (in `.gitignore` ✅)

**How to set up:**

1. **Copy from 1Password** (manually, one by one)
2. **Paste into `.env` file**
3. **Never share or commit**

**Example structure** (with FAKE placeholder values):
```bash
# AI Services
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Bluejet
BLUEJET_API_KEY=bj_live_XXXXXXXXXXXXXXXXXXXXXX
BLUEJET_API_SECRET=bj_sec_XXXXXXXXXXXXXXXXXXXXXXXX
BLUEJET_API_BASE_URL=https://api.bluejet.com/v1
BLUEJET_WORKSPACE_ID=ws_XXXXXXXXXXXX

# Database
SUPABASE_URL=https://XXXXXXXXXXXXX.supabase.co
SUPABASE_KEY=eyJXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SUPABASE_SERVICE_ROLE_KEY=eyJXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Email / Communication
MISSIVE_API_TOKEN=mst_XXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_ACCOUNT_SID=ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# N8n
N8N_ENCRYPTION_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Never add real values to examples or documentation!
```

### 3. Loading Environment Variables Securely

**In Python:**
```python
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access secrets
api_key = os.getenv('ANTHROPIC_API_KEY')

# Never print or log the actual key
if not api_key:
    raise ValueError("API key not found in environment")

# Never do this:
# print(f"API Key: {api_key}")  # ❌ NEVER!

# Instead:
print("✅ API key loaded successfully")
```

**In Node.js:**
```javascript
require('dotenv').config();

const apiKey = process.env.ANTHROPIC_API_KEY;

if (!apiKey) {
  throw new Error('API key not found');
}

// Never log the actual key
console.log('✅ API key loaded');
```

---

## 🚫 What NOT to Share with Claude

### Never Include in Claude Prompts:

❌ **API Keys:**
```
Bad: "Use this API key: sk-ant-abc123..."
Good: "Use the API key from environment variables"
```

❌ **Database Credentials:**
```
Bad: "Connect to postgres://user:password@host..."
Good: "Connect using credentials from .env"
```

❌ **Customer Personal Data:**
```
Bad: "Customer credit card: 4532-1234-5678-9012"
Good: "Customer payment processed successfully"
```

❌ **Passwords or Tokens:**
```
Bad: "Login with password: MySecretPass123"
Good: "Login using authenticated session"
```

### Safe to Share with Claude:

✅ Non-sensitive configuration (e.g., "timeout: 30 seconds")
✅ Public documentation URLs
✅ Error messages (that don't contain secrets)
✅ Anonymized data (e.g., "Customer A ordered 3 items")
✅ Code structure and logic
✅ Public API endpoints

---

## 🔐 Git Security

### .gitignore Configuration

**Must be in `.gitignore`:**
```
# Environment variables
.env
.env.local
.env.*.local

# Credentials
credentials.json
secrets.yaml
config/secrets.json

# API keys
*_api_key.txt
*_secret.txt

# Database
*.db-journal
*.sqlite

# Logs (may contain sensitive data)
*.log
logs/

# Backups
backup/*.sql
backup/*.dump

# IDE
.vscode/settings.json (if contains secrets)
.idea/workspace.xml

# OS
.DS_Store
Thumbs.db
```

### Before Every Commit:

**Run this checklist:**
```bash
# 1. Check what you're committing
git status

# 2. Review changes
git diff

# 3. Search for potential secrets
grep -r "api_key\|secret\|password\|token" .

# 4. Check .env is NOT staged
git status | grep ".env"

# If .env appears, STOP and unstage it:
# git reset .env

# 5. Only then commit
git commit -m "Your message"
```

### If You Accidentally Commit Secrets:

**⚠️ IMMEDIATE ACTION REQUIRED:**

1. **Rotate the compromised secret immediately**
   - Generate new API key/password
   - Update in 1Password
   - Update in `.env`

2. **Remove from Git history**
   ```bash
   # Remove file from history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (only if repository is private)
   git push origin --force --all
   ```

3. **Notify team** (if applicable)

4. **Monitor for unauthorized usage**

---

## 🛡️ API Key Security

### Best Practices:

1. **Use Read-Only Keys When Possible**
   - For analytics/monitoring: read-only
   - For automation: minimum required permissions

2. **Rotate Regularly**
   - Every 90 days minimum
   - Immediately if suspected compromise
   - After team member departure

3. **Use Different Keys for Dev/Prod**
   - Development: `ANTHROPIC_API_KEY_DEV`
   - Production: `ANTHROPIC_API_KEY_PROD`
   - Never mix them

4. **Monitor Usage**
   - Check API usage dashboards
   - Set up alerts for unusual activity
   - Review logs monthly

5. **Limit Scope**
   - Use workspace/project-specific keys
   - Set rate limits
   - Restrict IP addresses (if possible)

### API Key Format Recognition

**Learn to recognize API key formats** (never commit these):

```
Anthropic Claude:   sk-ant-api03-...
OpenAI:            sk-proj-...
Supabase:          eyJ... (JWT format)
Stripe:            sk_live_... or sk_test_...
AWS:               AKIA...
GitHub:            ghp_... or github_pat_...
```

If you see these patterns in code, **STOP and move to .env!**

---

## 📝 Secure Logging

### Never Log:

❌ Full API responses (may contain sensitive data)
❌ Database query results with customer data
❌ Authentication tokens
❌ Email content (may contain sensitive info)
❌ Full error messages from external APIs

### Safe Logging:

```python
# Bad:
logging.info(f"API Response: {response}")  # May contain secrets

# Good:
logging.info(f"API Response Status: {response.status_code}")
logging.debug(f"API Response Keys: {response.keys()}")  # Structure only

# Bad:
print(f"Customer data: {customer}")  # Full object

# Good:
print(f"Processing customer ID: {customer.id}")  # ID only

# Bad:
logging.error(f"Auth failed: {api_key}")  # Logs the key!

# Good:
logging.error("Auth failed: Invalid API key")  # No key exposed
```

### Log Redaction:

```python
def redact_sensitive_data(text: str) -> str:
    """Remove sensitive data from logs"""
    import re

    # Redact API keys
    text = re.sub(r'(sk-[a-zA-Z0-9-]{20,})', '***REDACTED_API_KEY***', text)

    # Redact email addresses
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                  '***EMAIL***', text)

    # Redact phone numbers
    text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                  '***PHONE***', text)

    # Redact credit cards
    text = re.sub(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}',
                  '***CARD***', text)

    return text

# Usage:
safe_log = redact_sensitive_data(potentially_sensitive_text)
logging.info(safe_log)
```

---

## 🔍 Code Review Security Checklist

Before deploying code, check:

- [ ] No hardcoded credentials
- [ ] All secrets in .env
- [ ] .env not committed
- [ ] Sensitive data redacted in logs
- [ ] No API keys in comments
- [ ] No TODO with credentials
- [ ] Database queries use parameterized statements (SQL injection prevention)
- [ ] User input validated and sanitized
- [ ] Error messages don't expose system details
- [ ] HTTPS used for all API calls
- [ ] Authentication tokens properly secured

---

## 🚨 Incident Response

### If Credentials Are Compromised:

**Immediate (within 5 minutes):**
1. ⚠️ **Revoke/rotate the credential** immediately
2. 🔍 Check for unauthorized usage
3. 📝 Document what was exposed and when

**Within 1 Hour:**
1. 🔐 Update all systems with new credentials
2. 🚫 Remove from Git history if committed
3. 📧 Notify team/stakeholders
4. 📊 Review access logs

**Within 24 Hours:**
1. 🔎 Complete security audit
2. 📈 Monitor for suspicious activity
3. 📋 Update security procedures
4. 🎓 Team training if needed

**Follow-up:**
1. 📝 Post-mortem analysis
2. 🛠️ Implement preventive measures
3. ✅ Update this document with lessons learned

---

## 📚 Security Resources

### Tools:

**1. git-secrets** (Prevents committing secrets)
```bash
# Install
brew install git-secrets

# Set up for repository
git secrets --install
git secrets --register-aws
```

**2. truffleHog** (Find secrets in Git history)
```bash
pip install truffleHog
truffleHog --regex --entropy=True .
```

**3. 1Password CLI**
```bash
# Install
brew install --cask 1password-cli

# Use in scripts (prompts for auth)
op item get "Claude API Key" --fields password
```

### Training:

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- API Security: https://apisecurity.io/
- 12-Factor App: https://12factor.net/ (see Config section)

---

## ✅ Security Checklist for New Team Members

When onboarding:

- [ ] 1Password access granted
- [ ] Explained .env usage
- [ ] Reviewed this security document
- [ ] Git security training completed
- [ ] .gitignore configured correctly
- [ ] Know what NOT to commit
- [ ] Know incident response procedure
- [ ] Have contact for security questions

---

## 📞 Security Contacts

**For Security Incidents:**
- Technical Lead: [Your name/contact]
- Backup: [Backup person]

**Vendor Security:**
- Anthropic Security: security@anthropic.com
- OpenAI: security@openai.com
- Supabase: security@supabase.io

**Emergency:**
- Rotate all credentials: [Link to procedure]
- Lock down systems: [Link to runbook]

---

## 🎯 Remember

### The Golden Rules:

1. **If in doubt, DON'T commit it**
2. **Credentials belong in .env and 1Password ONLY**
3. **Never share secrets in chat/email**
4. **Rotate regularly**
5. **Monitor for unusual activity**

### A Simple Test:

**Before committing, ask yourself:**
> "If this code was public on GitHub, would I be okay with that?"

If the answer is **NO** → Remove secrets first!

---

**Security is everyone's responsibility. When in doubt, ask! 🔒**

---

**Last Updated**: 2026-01-08
**Version**: 1.0
**Next Review**: 2026-04-08 (quarterly)
