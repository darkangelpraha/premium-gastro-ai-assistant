# GitHub Copilot Custom Instructions - Premium Gastro AI Assistant

## 🎯 Project Overview

**Premium Gastro AI Assistant** is a comprehensive AI-powered automation ecosystem designed to transform business operations through intelligent communication processing, VIP contact management, and multi-channel automation. This is a production system handling real business data for a Central European food service company.

## 🏗️ Architecture & Technology Stack

### Core Technologies
- **Language**: Python 3.x (primary)
- **Database**: Supabase (PostgreSQL) - 40,803+ business records
- **Workflow Automation**: N8n, Lindy AI
- **Containerization**: Docker, docker-compose
- **AI/ML**: OpenAI APIs (GPT, Whisper), Google Gemini, local Ollama models

### Key Integrations
- **Email**: Missive API (primary hub), Gmail API
- **Communication**: Twilio (SMS/WhatsApp/Voice), Beeper (unified messaging)
- **Social Media**: Ayrshare API (multi-platform management)
- **Voice**: ElevenLabs, Whisper ASR, Plivo
- **OCR**: Google Cloud Vision API, Tesseract
- **Scheduling**: Cal.com
- **Business Data**: Supabase (VIP contacts, conversation history)

### Multi-Tier Architecture
1. **Tier 1 - Mobile**: iPhone/Android apps for voice commands, OCR, quick actions
2. **Tier 2 - Workstation**: Heavy computing, advanced AI processing, business intelligence
3. **Tier 3 - Cloud**: N8n workflows, Supabase sync, API orchestration

## 📋 Code Style & Conventions

### Python Code Standards

1. **File Headers**: Every Python file starts with a descriptive docstring
   ```python
   #!/usr/bin/env python3
   """
   MODULE_NAME - BRIEF DESCRIPTION
   Detailed explanation of what this module does
   """
   ```

2. **Type Hints**: Use comprehensive type hints from `typing` module
   ```python
   from typing import Dict, List, Optional, Any, Tuple
   
   def process_email(email: Dict[str, Any]) -> EmailProcessingResult:
       pass
   ```

3. **Dataclasses**: Prefer dataclasses for structured data
   ```python
   from dataclasses import dataclass
   
   @dataclass
   class VIPContact:
       email: str
       name: str
       vip_score: float
       reasons: List[str]
   ```

4. **Logging**: Use Python's logging module, configure early
   ```python
   import logging
   
   logging.basicConfig(level=logging.INFO)
   self.logger = logging.getLogger(__name__)
   ```

5. **Environment Variables**: Always use `os.getenv()` for configuration
   ```python
   import os
   
   # Good - with validation
   self.supabase_url = os.getenv('SUPABASE_URL', '')
   if not self.supabase_url or 'your-project' in self.supabase_url:
       raise ValueError("SUPABASE_URL environment variable is required")
   
   # Bad - never hardcode
   # self.api_key = "sk-abc123..."  # NEVER DO THIS
   ```

6. **API Headers**: Consistent format for API authentication
   ```python
   self.headers = {
       'apikey': self.api_key,
       'Authorization': f'Bearer {self.api_key}',
       'Content-Type': 'application/json'
   }
   ```

7. **Class Structure**: Initialize logging first, then config, then load data
   ```python
   def __init__(self):
       # Initialize logging first
       logging.basicConfig(level=logging.INFO)
       self.logger = logging.getLogger(__name__)
       
       # Load configuration
       self.config = self.load_config()
       
       # Load data
       self.load_vip_analysis()
   ```

### Documentation Standards

1. **Markdown Headers**: Use emojis for visual hierarchy
   ```markdown
   # 🚀 Main Title
   ## 🎯 Section
   ### 📋 Subsection
   ```

2. **Documentation Style**: Comprehensive, business-focused
   - Clear section separators with `---`
   - Code blocks with language specification
   - ROI and impact metrics
   - Implementation timelines
   - Cost analysis

3. **Comments**: Only when necessary for complex business logic
   - Explain WHY, not WHAT
   - Document urgency patterns, scoring algorithms, thresholds
   - Multi-language keyword lists (Czech/English/German)

## 🔒 Security & Privacy Requirements

### Critical Security Rules

1. **Never Hardcode Credentials**: All secrets in environment variables
2. **Environment File Pattern**: Always use `.env` (gitignored) and `env.example` (committed)
3. **Validation**: Validate environment variables on startup with descriptive errors
4. **API Keys**: Load from environment, never commit to repository
5. **PII Handling**: Customer data is VIP-sensitive (names, emails, business info)
6. **Redaction**: Implement redaction for phone numbers and sensitive data in logs/tests
   ```python
   def redact_sandbox_info(data):
       if isinstance(data, dict) and 'number' in data:
           num = str(data['number'])
           if len(num) > 4:
               data['number'] = num[:-4] + '****'
           else:
               data['number'] = '[REDACTED]'
       return data
   ```

### Required Environment Variables

Core variables that must be documented in `env.example`:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase API key (anon or service role)
- `MISSIVE_API_TOKEN` - Missive authentication
- `MISSIVE_ORG_ID` - Missive organization
- `TWILIO_SID`, `TWILIO_AUTH_TOKEN` - Twilio credentials
- `OPENAI_API_KEY` - OpenAI services
- `GEMINI_API_KEY` - Google AI
- API keys for all integrated services

## 🧪 Testing Standards

### Test Structure
- **Framework**: pytest (preferred)
- **Location**: `/tests/` directory
- **Naming**: `test_*.py` files, `test_*` functions
- **Docstrings**: Clear description of what is being tested

### Test Patterns
```python
"""Tests for the sandbox info redaction helper.

These are simple unit tests intended to run under pytest. They verify that
phone numbers are masked and short/invalid numbers are replaced with
"[REDACTED]".
"""

from MODULE import function_to_test

def test_descriptive_name():
    # Arrange
    input_data = {'number': '+1234567890', 'foo': 'bar'}
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert 'number' in result
    assert result['number'].endswith('****')
```

### Test Coverage Priorities
1. Security functions (credential redaction, validation)
2. VIP scoring algorithms
3. Email classification logic
4. API integration error handling
5. Data validation and sanitization

## 🎯 Business Domain Knowledge

### VIP Contact System
- **VIP Score Range**: 0-100 (40+ is VIP threshold)
- **Scoring Weights**: 
  - Recent activity: 30%
  - Frequency: 25%
  - Business size: 20%
  - Payment reliability: 15%
  - Relationship depth: 10%

### Urgency Detection
- **Languages**: Czech (primary), English, German
- **Priority Levels**: 1-10 scale
- **Categories**: crisis, urgent, financial, meeting
- **Response Time Targets**: <2 hours for urgent, <4 hours for normal

### Multi-Language Keywords
Always include Czech, English, and German equivalents:
```python
urgency_patterns = {
    'czech': ['naléhavé', 'urgent', 'důležité'],
    'english': ['urgent', 'asap', 'critical'],
    'german': ['dringend', 'sofort', 'wichtig']
}
```

### Email Classification
- **VIP Status**: Boolean based on vip_score
- **Priority Level**: 1-10 integer
- **Urgency**: Boolean detection from keywords
- **Processing Confidence**: 0.0-1.0 float (0.8+ threshold)

## 📊 Data Models & Patterns

### Common Dataclass Patterns
```python
@dataclass
class EmailProcessingResult:
    email_id: str
    sender: str
    subject: str
    classification: str
    priority_level: int
    vip_status: bool
    urgency_detected: bool
    suggested_response: str
    processing_confidence: float

@dataclass
class VIPContact:
    email: str
    name: str
    company: str
    vip_score: float
    reasons: List[str]
    activity_pattern: str
    urgency_triggers: List[str]
    relationship_type: str
```

### API Response Patterns
```python
# Supabase queries return lists of dicts
contacts = supabase.table('contacts').select('*').execute()
for contact in contacts.data:
    # Process each contact
    
# Error handling with descriptive messages
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
except requests.exceptions.RequestException as e:
    self.logger.error(f"API request failed: {e}")
    raise
```

## 🚀 Development Workflow

### Phase-Based Development
Project is organized in 6 phases:
1. **Phase 1** ✅ - Email Intelligence (DEPLOYED)
2. **Phase 2** 🔄 - Conversation Intelligence (NEXT)
3. **Phase 3** 📋 - Document Intelligence (PLANNED)
4. **Phase 4** 📱 - Social Media Automation (PLANNED)
5. **Phase 5** 💬 - Advanced Communications (PLANNED)
6. **Phase 6** 🧠 - Multi-Agent AI System (PLANNED)

### File Organization
```
/
├── *.py                    # Core Python modules (descriptive names)
├── *.md                    # Documentation (comprehensive, emoji-rich)
├── .github/                # GitHub configuration
├── mcp-gateway/            # MCP protocol integrations
├── phase6_workflows/       # N8n workflow JSON files
├── tests/                  # pytest test files
├── docker-compose.yml      # Service orchestration
├── env.example             # Environment template (safe to commit)
└── .env                    # Actual secrets (NEVER commit)
```

### Naming Conventions
- **Python Files**: `UPPERCASE_WITH_UNDERSCORES.py` for main modules
- **Documentation**: `UPPERCASE_WITH_UNDERSCORES.md` for major docs
- **Config Files**: `lowercase-with-hyphens.yml`
- **Variables**: `snake_case` for Python
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`

## 🔧 Common Patterns & Best Practices

### API Integration Pattern
```python
class ServiceIntegration:
    def __init__(self):
        # 1. Load credentials from environment
        self.api_key = os.getenv('SERVICE_API_KEY')
        
        # 2. Validate credentials
        if not self.api_key or 'your_' in self.api_key:
            raise ValueError("SERVICE_API_KEY is required")
        
        # 3. Setup headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 4. Setup logging
        self.logger = logging.getLogger(__name__)
    
    def make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make authenticated API request with error handling"""
        try:
            response = requests.get(
                f"{self.api_base}/{endpoint}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request to {endpoint} failed: {e}")
            raise
```

### Cost Optimization Pattern
- Prefer free tiers: Google Gemini, Hugging Face
- Cache results in Supabase to avoid reprocessing
- Batch API calls when possible
- Document cost per operation in comments

### Multi-Language Support
Always design for Czech/English/German:
```python
LANGUAGE_PATTERNS = {
    'czech': {...},
    'english': {...},
    'german': {...}
}

def detect_urgency(text: str, language: str = 'czech') -> bool:
    patterns = LANGUAGE_PATTERNS.get(language, LANGUAGE_PATTERNS['czech'])
    # Detection logic
```

## 💡 AI-Specific Guidelines

### OpenAI Integration
- Use environment variables for API keys
- Implement retry logic for rate limits
- Cache responses when appropriate
- Document token costs in comments

### Prompt Engineering
- Context-aware prompts with business data
- Multi-language support in system messages
- VIP status and urgency in prompt context
- Temperature settings documented per use case

### Local AI Models (Ollama)
- DeepSeek R1 (33B) for reasoning
- Qwen2.5 (14B) for multilingual
- Document minimum hardware requirements
- Fallback to cloud APIs if local unavailable

## 📝 Documentation Requirements

### Code Documentation
- Module-level docstrings with clear purpose
- Complex algorithms need explanation comments
- Business logic thresholds documented
- API endpoint documentation with examples

### User Documentation
- Setup instructions with prerequisites
- Environment variable configuration
- API key acquisition steps
- Troubleshooting common issues
- ROI and business impact metrics

### Technical Documentation
- Architecture diagrams (ASCII art or Markdown)
- Data flow diagrams
- Integration points clearly mapped
- Cost analysis per service
- Performance benchmarks

## 🎨 Markdown Documentation Style

### Headers with Emojis
```markdown
# 🚀 Main Title
## 🎯 Purpose Section
### 📋 Implementation Details
#### 💡 Technical Notes
```

### Code Blocks
Always specify language for syntax highlighting:
```markdown
\`\`\`python
# Python code
\`\`\`

\`\`\`bash
# Shell commands
\`\`\`

\`\`\`json
# JSON data
\`\`\`
```

### Lists and Structure
- Use `-` for unordered lists
- Use numbered lists for sequential steps
- Use checkboxes for task tracking: `- [ ]` or `- [x]`
- Section dividers: `---`

## 🚨 Error Handling

### Required Error Handling
1. **Environment Variable Validation**: Descriptive errors on startup
2. **API Failures**: Retry logic with exponential backoff
3. **Data Validation**: Type checking and sanitization
4. **Network Issues**: Timeout configuration and handling
5. **Rate Limits**: Respect API quotas, implement backoff

### Error Message Pattern
```python
if not self.required_config:
    raise ValueError(
        "REQUIRED_CONFIG environment variable is required and must be valid. "
        "Please set it in your .env file or environment. "
        "See env.example for the correct format."
    )
```

## 🎯 Performance Considerations

### Optimization Priorities
1. **Cost**: Minimize API calls, prefer free tiers
2. **Speed**: Cache VIP data, batch operations
3. **Reliability**: Retry failed operations, graceful degradation
4. **Scalability**: Design for 40,000+ contacts

### Caching Strategy
- VIP scores cached in Supabase (daily refresh)
- Email classification results stored for learning
- Conversation history for context
- API responses cached when appropriate

## 📞 Integration-Specific Notes

### Missive (Email Hub)
- Primary email interface for business owner
- Shared mailboxes: `info@`, `accounting@`, `marketing@`
- Personal inbox as central cockpit
- Webhook integration for real-time processing

### Supabase (Intelligence Database)
- 40,803+ business records
- VIP contact metadata and scoring
- Conversation history and analytics
- Full-text search capabilities

### N8n (Workflow Orchestrator)
- Bridges Czech systems without APIs
- Coordinates email, voice, data handoffs
- Self-hosted or cloud options
- 8,000+ integration nodes

### Twilio (Communication)
- SMS, WhatsApp, Voice capabilities
- Credentials in 1Password
- Escalation for VIP/urgent cases
- Integration with Missive workflows

## 🎓 When Suggesting Code

### Always Consider
1. **Security**: Never hardcode secrets, validate inputs
2. **Cost**: Document API costs, prefer free tiers
3. **Multi-language**: Czech/English/German support
4. **Business Context**: VIP priority, urgency detection
5. **Existing Patterns**: Follow established code style
6. **Type Safety**: Use type hints consistently
7. **Error Handling**: Graceful degradation
8. **Documentation**: Update relevant .md files
9. **Environment**: Document new env variables in env.example
10. **Testing**: Suggest test cases for new functionality

### Code Review Checklist
- [ ] No hardcoded credentials
- [ ] Type hints on functions
- [ ] Error handling implemented
- [ ] Logging for debugging
- [ ] Docstrings present
- [ ] Multi-language if applicable
- [ ] Cost-optimized approach
- [ ] Follows existing patterns
- [ ] Tests included/updated
- [ ] Documentation updated

## 🌍 Business & Cultural Context

### Target Market
- **Region**: Central Europe (Prague-based)
- **Industry**: Premium food service / gastronomy
- **Primary Language**: Czech (with English/German for international)
- **Business Model**: B2B and B2C catering, events, restaurant services

### Communication Preferences
- **Email**: Primary business channel (Missive)
- **WhatsApp**: Client communication
- **Phone**: VIP escalation
- **Social Media**: Marketing and engagement

### Priority System
1. **VIP Clients**: High-value, long-term relationships
2. **Urgent Issues**: Service failures, payment problems
3. **New Opportunities**: Potential new business
4. **Routine**: Standard inquiries and operations

---

## 📚 Quick Reference

### Start New Feature
1. Check `PREMIUM_GASTRO_ASSISTANT_MASTERPLAN.md` for phase alignment
2. Follow existing file naming conventions
3. Create with module docstring and type hints
4. Add environment variables to `env.example` if needed
5. Implement with security and cost optimization
6. Add tests to `/tests/`
7. Update relevant documentation
8. Document ROI and business impact

### Add New Integration
1. Research API costs and free tier limits
2. Add credentials to `env.example` (placeholder)
3. Create integration class following API Integration Pattern
4. Implement error handling and retry logic
5. Add logging for debugging
6. Document in main README.md
7. Update architecture documentation if significant

### Debug Issues
1. Check environment variables are set correctly
2. Review logs for error messages
3. Verify API credentials and quotas
4. Test with minimal data first
5. Check Supabase data integrity
6. Validate network connectivity
7. Review recent code changes

---

**Remember**: This is a production system handling real business data. Security, cost optimization, and reliability are paramount. Every change should consider business impact and ROI.
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
