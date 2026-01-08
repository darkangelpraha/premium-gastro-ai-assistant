# Copilot Instructions for Premium Gastro AI Assistant

## Repository Overview
**Premium Gastro AI Assistant** - AI-powered business automation system for food service. Multi-phase automation ecosystem: email intelligence, communication processing, document OCR, social media automation, workflow orchestration.

**Stack:** Python 3.12.3, Supabase, N8n, Docker, Missive API, Twilio, OpenAI | **Size:** ~30 files, 6 Python scripts, 17+ markdown docs

## Project Structure
**Root:** 6 Python scripts (email/VIP/Twilio/Missive/mobile automation) + extensive markdown documentation + `docker-compose.yml` + `env.example`
**Subdirs:** `tests/` (pytest), `phase6_workflows/` (n8n JSONs), `mcp-gateway/` (API docs)

**Key Scripts:**
- `SUPABASE_VIP_ANALYZER.py` - Analyzes 40K+ records for VIP contacts
- `INTELLIGENT_EMAIL_PROCESSOR.py` - Email classification, priority scoring
- `MISSIVE_AI_ASSISTANT.py`, `TWILIO_WHATSAPP_LINDY_SETUP.py`, `MOBILE_APP_PROTOTYPE.py`

**Config:** `docker-compose.yml` (7 services: hub-ui, comm-processor, n8n, postgres, redis, backup, health-monitor) | `env.example` (20+ required vars) | `.gitignore`

## Build, Test, and Run

**Prerequisites:** Python 3.12.3, pip, Docker 28.0.4, pytest

### CRITICAL: Environment Variables Required
ALL scripts need env vars. Scripts fail gracefully with descriptive errors if missing.

Setup: `cp env.example .env` → Edit with real credentials (SUPABASE_URL, SUPABASE_KEY, MISSIVE_*, TWILIO_*, etc.)

### Testing (ALWAYS run before changes)
```bash
pip install pytest requests  # If needed
python3 -m pytest tests/ -v  # 3 tests, ~0.08s, 100% pass expected
```

### Running Python Scripts
```bash
# Requires env vars set
python3 SUPABASE_VIP_ANALYZER.py  # Needs SUPABASE_URL, SUPABASE_KEY
python3 INTELLIGENT_EMAIL_PROCESSOR.py  # Warns if no VIP data, continues with test data
```

### Docker (Use `docker compose` NOT `docker-compose`)
```bash
docker compose config --quiet  # Validates (warns about missing env vars - expected)
docker compose up -d  # Requires .env file populated
```

**Note:** docker-compose.yml references directories (hub-ui/, comm-processor/, etc.) without Dockerfiles - this is deployment config for external infrastructure.

## Validation & CI/CD
**No GitHub Actions exist.** No automated CI/CD pipeline.

**Manual validation:** `python3 -m pytest tests/ -v` | `python3 -m py_compile *.py` | `docker compose config --quiet`

## Code Conventions

**Python Style:** dataclasses, type hints (Dict/List/Optional), logging module, `os.getenv()` with validation, descriptive ValueErrors

**Security (CRITICAL):** NEVER commit credentials. Use environment variables exclusively. `.env` in `.gitignore`. Scripts validate env vars:
```python
if not self.supabase_url or 'your-project' in self.supabase_url:
    raise ValueError("SUPABASE_URL environment variable is required...")
```

**API Patterns:** Supabase (apikey + Bearer), Missive (Bearer), Twilio (Basic auth base64), N8n (polling not webhooks, all start INACTIVE)

**Architecture:** Supabase VIP data → Email Processor → Missive | Notion/Asana sync via n8n (Phase 6) | Multi-service Docker stack

## Common Issues & Solutions

**Environment Variable Missing**
→ Create `.env` from `env.example`, set real values

**Test Import Error** (`ModuleNotFoundError: TWILIO_WHATSAPP_LINDY_SETUP`)
→ Run pytest from repo root: `cd /home/runner/work/.../premium-gastro-ai-assistant && python3 -m pytest tests/`

**Docker Compose Not Found**
→ Use `docker compose` (space) not `docker-compose` (hyphen)

**Missing VIP Analysis File**
→ Expected behavior. Email processor logs warning, continues with test data. Generate: `python3 SUPABASE_VIP_ANALYZER.py`

**N8n Workflow Activation**
→ All Phase 6 workflows INACTIVE by default. Configure credentials first (see `phase6_workflows/IMPORT_INSTRUCTIONS.md`). n8n: http://localhost:5678 or http://127.0.0.1:5678 (Safari compat)

## Making Changes

**Before:** Run tests (`pytest tests/ -v`), check imports, review `env.example`
**During:** Preserve env var validation, follow existing patterns
**After:** Run `pytest tests/ -v`, verify scripts run with env vars

**Add tests:** Follow `tests/test_twilio_redaction.py` pattern

**Update docs:** Sync with Phase docs, `README.md`, `SECURITY.md` if relevant

## Quick Commands
```bash
python3 -m pytest tests/ -v                    # Test
python3 -m py_compile *.py                     # Syntax check
docker compose config --quiet                  # Docker validate
docker compose ps                              # Services status
```

## Critical Notes

1. **Trust these instructions** - Comprehensive and tested. Search only if incomplete/incorrect.
2. **Env vars mandatory** - Scripts validate and fail with helpful errors if missing.
3. **Minimal tests** - 3 unit tests for redaction only. Add tests for new functionality.
4. **No automated CI** - Manual testing required. Always run pytest before committing.
5. **Docker config incomplete** - References external services. Intentional deployment config.
6. **Security paramount** - Never commit credentials. Environment variables only.
7. **N8n workflows** - See `phase6_workflows/` for definitions and import steps.
8. **Documentation-heavy** - 17+ markdown files with business context. Reference when changing logic.
