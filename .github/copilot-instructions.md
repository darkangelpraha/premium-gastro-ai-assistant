# Copilot Instructions for Premium Gastro AI Assistant

## Repository Overview

**Premium Gastro AI Assistant** is a comprehensive AI-powered business automation system for Premium Gastro, a food service business. The repository contains Python scripts, documentation, and configuration for a multi-phase automation ecosystem that handles email intelligence, communication processing, document OCR, social media automation, and workflow orchestration.

**Repository Size:** Small (~30 files in root, 6 Python scripts, 17+ markdown documents)
**Primary Language:** Python 3.12.3
**Key Technologies:** Supabase, N8n, Docker, Missive API, Twilio, OpenAI
**Target Runtime:** Python 3.12+ with standard libraries (requests module)

## Project Structure

### Root Directory Files
- **Python Scripts (6):** Core automation scripts for email processing, VIP analysis, Twilio/WhatsApp setup, Missive integration, and mobile app prototype
- **Documentation (17+ MD files):** Phase completion reports, masterplan, security policy, setup guides
- **Configuration:** `docker-compose.yml`, `env.example`, `.gitignore`
- **Subdirectories:**
  - `tests/` - Pytest unit tests
  - `phase6_workflows/` - N8n workflow JSON files and import instructions
  - `mcp-gateway/` - MCP Gateway API setup documentation

### Key Python Scripts
1. **SUPABASE_VIP_ANALYZER.py** - Analyzes 40,803+ Supabase records to identify VIP contacts and urgency patterns
2. **INTELLIGENT_EMAIL_PROCESSOR.py** - Email classification, priority scoring, automated response generation
3. **MISSIVE_AI_ASSISTANT.py** - Context-aware email intelligence via Missive API
4. **TWILIO_WHATSAPP_LINDY_SETUP.py** - WhatsApp Business automation setup; includes `redact_sandbox_info()` function
5. **MOBILE_APP_PROTOTYPE.py** - Mobile app integration prototype
6. **env.example** - Complete environment variable template with security notes

### Critical Configuration Files
- **docker-compose.yml** - Multi-service stack: hub-ui, comm-processor, n8n, postgres, redis, backup-service, health-monitor
- **env.example** - Requires 20+ environment variables (Supabase, Twilio, APIs, etc.)
- **.gitignore** - Excludes .env, credentials.json, __pycache__, venv/, build artifacts

## Build, Test, and Run Instructions

### Prerequisites
- **Python:** 3.12.3 (verified working version)
- **pip:** Available in system
- **Docker:** Version 28.0.4 (use `docker compose`, NOT `docker-compose`)
- **pytest:** Required for testing (install if missing)

### Environment Setup

**CRITICAL:** All scripts require environment variables. Scripts will fail with helpful error messages if variables are not set.

1. **Create .env file from template:**
   ```bash
   cp env.example .env
   # Edit .env and fill in actual API keys and credentials
   ```

2. **Required environment variables for Python scripts:**
   - `SUPABASE_URL` - Must be valid URL (scripts validate this)
   - `SUPABASE_KEY` - Must be valid API key (minimum 20 characters)
   - `MISSIVE_API_TOKEN`, `MISSIVE_ORG_ID` - For Missive integration
   - `TWILIO_SID`, `TWILIO_AUTH_TOKEN` - For Twilio integration
   - See `env.example` for complete list

### Testing

**ALWAYS run tests before making changes to understand baseline behavior.**

```bash
# Install pytest if not present
pip install pytest

# Run all tests (currently 3 tests in test_twilio_redaction.py)
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_twilio_redaction.py -v
```

**Expected output:** 3 tests pass in ~0.08 seconds
- `test_redact_full_number` - Redacts last 4 digits of phone numbers
- `test_redact_short_number` - Replaces short numbers with [REDACTED]
- `test_passthrough_non_dict` - Passes through non-dict inputs

**Test Framework:** pytest 9.0.2
**Test Location:** `tests/` directory
**Import Pattern:** Tests import from root-level Python modules (e.g., `from TWILIO_WHATSAPP_LINDY_SETUP import redact_sandbox_info`)

### Running Python Scripts

**All scripts run standalone but require environment variables:**

```bash
# VIP Analyzer (requires SUPABASE_URL and SUPABASE_KEY)
python3 SUPABASE_VIP_ANALYZER.py

# Email Processor (expects VIP analysis data, has test mode)
python3 INTELLIGENT_EMAIL_PROCESSOR.py

# Missive Assistant (requires MISSIVE_API_TOKEN, SUPABASE_KEY)
python3 MISSIVE_AI_ASSISTANT.py
```

**Known Behavior:**
- Scripts fail gracefully with descriptive error messages if environment variables are missing
- `INTELLIGENT_EMAIL_PROCESSOR.py` logs warning if VIP analysis file not found at `/tmp/vip_analysis_complete.json` but continues with test data
- Scripts use Python's `logging` module with INFO level by default

### Python Dependencies

**Standard library used extensively:** No requirements.txt file exists.

**Required pip packages:**
- `requests` (version 2.31.0 verified working) - Used by all Python scripts
- `pytest` (version 9.0.2) - For testing

**Installation (if needed):**
```bash
pip install requests pytest
```

### Docker Setup

**Command:** Use `docker compose` (newer syntax), NOT `docker-compose`

```bash
# Validate configuration (will warn about missing env vars - this is expected)
docker compose config --quiet

# Build services (requires .env file with all variables set)
docker compose build

# Start services (requires .env file)
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

**Docker Compose Services (7 total):**
1. `hub-ui` - Communication Hub UI on port 3000
2. `comm-processor` - Unified communication processor
3. `n8n` - Workflow engine on port 5678
4. `postgres` - Database on port 5432
5. `redis` - Cache on port 6379
6. `backup-service` - Automated backups
7. `health-monitor` - Service monitoring

**IMPORTANT:** Docker services reference subdirectories that don't exist in this repo (hub-ui/, comm-processor/, backup-service/, health-monitor/). These are defined in docker-compose.yml but the Dockerfiles are not present. This appears to be infrastructure configuration for a larger deployment.

## Validation and CI/CD

**No GitHub Actions workflows exist.** There is no automated CI/CD pipeline.

**Manual validation steps:**
1. Run pytest: `python3 -m pytest tests/ -v`
2. Syntax check Python files: `python3 -m py_compile <filename>.py`
3. Docker config validation: `docker compose config --quiet`

## Code Conventions and Architecture

### Python Code Style
- Scripts use `#!/usr/bin/env python3` shebang
- Heavy use of dataclasses for structured data (@dataclass decorator)
- Logging via Python's logging module (INFO level)
- Environment variables loaded via `os.getenv()` with validation
- Type hints in function signatures (typing module: Dict, List, Optional, Any)
- Error handling with descriptive ValueError messages for missing config

### Security Practices
**CRITICAL - NEVER commit credentials:**
- All sensitive data MUST be in environment variables
- `.env` file is in `.gitignore`
- See `SECURITY.md` for detailed security policy
- Example validation from `SUPABASE_VIP_ANALYZER.py`:
  ```python
  if not self.supabase_url or 'your-project' in self.supabase_url:
      raise ValueError("SUPABASE_URL environment variable is required...")
  ```

### API Integration Patterns
- **Supabase:** Headers include `apikey` and `Authorization: Bearer {key}`
- **Missive:** Authorization via `Bearer {token}`
- **Twilio:** Basic auth with base64 encoded SID:AUTH_TOKEN
- **N8n Workflows:** Use polling (not webhooks) for safety; all start INACTIVE

### Data Flow Architecture
1. **Email Intelligence:** Supabase VIP data → Email Processor → Missive integration
2. **Workflow Automation:** Notion/Asana sync via n8n (Phase 6)
3. **Communication Hub:** Multiple services orchestrated via Docker Compose

## Common Pitfalls and Known Issues

### Environment Variable Issues
**SYMPTOM:** Script fails with "variable is required" error
**SOLUTION:** Create `.env` file from `env.example` and set real values

### Test Import Errors
**SYMPTOM:** `ModuleNotFoundError: No module named 'TWILIO_WHATSAPP_LINDY_SETUP'`
**CAUSE:** Tests run from wrong directory
**SOLUTION:** Always run pytest from repository root: `cd /home/runner/work/premium-gastro-ai-assistant/premium-gastro-ai-assistant && python3 -m pytest tests/`

### Docker Compose Version
**SYMPTOM:** `docker-compose: command not found`
**SOLUTION:** Use `docker compose` (space, not hyphen) - newer Docker CLI syntax

### Missing VIP Analysis File
**SYMPTOM:** Email processor logs "Failed to load VIP analysis"
**BEHAVIOR:** This is expected - script continues with test data
**SOLUTION:** Run `SUPABASE_VIP_ANALYZER.py` first to generate `/tmp/vip_analysis_complete.json`

### n8n Workflow Activation
**CRITICAL:** All Phase 6 workflows are INACTIVE by default for safety
**BEFORE ACTIVATION:** Configure credentials via n8n UI (see `phase6_workflows/IMPORT_INSTRUCTIONS.md`)
**ACCESS:** n8n runs on http://localhost:5678 (or http://127.0.0.1:5678 for Safari compatibility)

## Making Code Changes

### Before Changing Python Scripts
1. **Understand the environment:** Scripts heavily use environment variables - check `env.example`
2. **Run existing tests:** `python3 -m pytest tests/ -v` to establish baseline
3. **Check imports:** Scripts use standard library + requests module
4. **Preserve security patterns:** Keep environment variable validation logic

### Testing Changes
1. **Add tests for new functions:** Follow pattern in `tests/test_twilio_redaction.py`
2. **Run tests after changes:** `python3 -m pytest tests/ -v`
3. **Verify scripts run:** Test with appropriate environment variables set

### Documentation Changes
- Update relevant Phase documentation if changing automation logic
- Update `README.md` if changing project structure or adding major features
- Update `SECURITY.md` if changing credential handling

## Quick Reference Commands

```bash
# Test suite
python3 -m pytest tests/ -v

# Syntax validation
python3 -m py_compile *.py

# Run with environment (example)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-key-here"
python3 SUPABASE_VIP_ANALYZER.py

# Docker validation
docker compose config --quiet

# Check Docker services
docker compose ps
```

## Important Notes for Coding Agents

1. **Trust these instructions** - They are comprehensive and tested. Only search for additional information if instructions are incomplete or found to be in error.

2. **Environment variables are mandatory** - All Python scripts validate required variables and fail with helpful errors if not set. Don't try to run scripts without proper .env setup.

3. **Tests are minimal** - Only 3 unit tests exist for the redaction function. Add tests for new functionality following the existing pytest pattern.

4. **No automated CI** - Manual testing is required. Always run pytest before committing changes.

5. **Docker infrastructure is incomplete** - docker-compose.yml references services that don't have Dockerfiles in repo. This is intentional - it's deployment configuration for external infrastructure.

6. **Security is paramount** - Never commit API keys, tokens, or credentials. Use environment variables exclusively.

7. **N8n workflows are documented externally** - See `phase6_workflows/` for complete workflow definitions and import instructions.

8. **The codebase is documentation-heavy** - 17+ markdown files contain critical context about the multi-phase automation project. Reference them when making changes to understand business logic.
