# 🤖 Premium Gastro AI Assistant

**The most advanced digital assistant ecosystem for business automation in 2025**

## 🚀 PG 2.0 AI-First Transformation (ACTIVE)

**Current Initiative**: PG 2.0 AI-First Transformation (Lucy / Pan Talir / Zeus)
- 📍 **GitHub Anchor**: [`PG_2.0_TRANSFORMATION_ANCHOR.md`](PG_2.0_TRANSFORMATION_ANCHOR.md)
- 📈 **Execution Log**: [`PG_2.0_EXECUTION_LOG.md`](PG_2.0_EXECUTION_LOG.md)
- 👥 **Role Boundaries**: [`PG_2.0_ROLE_BOUNDARIES.md`](PG_2.0_ROLE_BOUNDARIES.md)
- ⏱️ **Cadence**: Daily ships + Weekly customer/reliability improvements (non-negotiable)
- 🎯 **Timeline**: 14-day execution window (Feb 14-27, 2026)

See the transformation anchor document for full details on operational principles, role boundaries, and success criteria.

---

## 🎯 Overview

Complete AI-powered automation system that transforms Premium Gastro into a technology-driven business with 90% automated communications and administrative tasks.

## ✅ Current Status: Phase 1 DEPLOYED

### 📧 Email Intelligence System (LIVE)

- **VIP Contact Identification**: 3,598 contacts auto-identified from Supabase business data
- **Multi-language Urgency Detection**: Czech/English/German with 49 keywords
- **Intelligent Priority Scoring**: 1-10 scale based on business context
- **Cost Optimization**: 75% reduction in AI processing costs
- **Response Automation**: Context-aware response generation

## 🚀 Complete Roadmap (6 Phases)

### Phase 1: Email Intelligence ✅ COMPLETE

- Automated VIP detection from business data
- Multi-language urgency analysis
- SaneBox + Lindy integration
- Missive AI assistant integration

### Phase 2: Conversation Intelligence 🔄 NEXT

- **Phone Call Transcription**: Whisper API integration
- **Meeting Intelligence**: Otter.ai automatic summaries
- **Real-time Insights**: Sentiment analysis and action extraction

### Phase 3: Document Intelligence 📋 PLANNED

- **Handwritten Notes OCR**: Google Vision + Tesseract
- **Note Classification**: AI categorization and action extraction
- **Mobile Integration**: iPhone camera → searchable text

### Phase 4: Social Media Automation 📱 PLANNED

- **Multi-Platform Management**: Ayrshare API (12+ platforms)
- **Content Generation**: AI-powered posts and scheduling
- **Engagement Monitoring**: Automated responses and analytics

### Phase 5: Advanced Communications 💬 PLANNED

- **Enhanced Missive Integration**: Webhooks and AI panels
- **Beeper AI Enhancement**: Smart message prioritization
- **Unified Communication Hub**: Cross-platform conversation sync

### Phase 6: Multi-Agent AI System 🧠 ✅ COMPLETE

- **App Navigation Agent**: Error-free navigation with multi-agent coordination
- **Autonomous Business Agents**: Client relations, supplier management
- **Self-Improving System**: Learn from business patterns
- **Complete Automation**: Email → fulfillment workflows

## 🛠️ Technology Stack

### Core Platform

- **Database**: Supabase (40,803+ business records)
- **Automation**: N8n (recommended for complex workflows)
- **AI Processing**: OpenAI GPT models + Whisper
- **Email**: Missive-first orchestration (personal inbox plus `info@`, `accounting@`, `marketing@`)

### APIs & Integrations

- **Transcription**: OpenAI Whisper, Otter.ai, Plivo ASR
- **OCR**: Google Cloud Vision API + Tesseract
- **Social Media**: Ayrshare unified API
- **Communications**: Missive webhooks, Beeper integration
- **Telephony & Voice**: Twilio (SMS/WhatsApp/voice) + Cal.com + ElevenLabs (11.ai) for branded calls

### Integration Rationale (What & Why)

- **Missive hub** – Petr handles all mail, so Missive remains the central cockpit. Shared mailboxes feed into the personal inbox while future rules/SLA tags can be layered once workflows are defined.
- **N8n orchestrator** – Bridges Czech systems without official APIs (BlueJet, Shoptet Premium, Pohoda, banking feeds) and coordinates handoffs between email, voice, and data stores.
- **Supabase intelligence** – Stores VIP/contact metadata that the email processor uses to rank responses; also becomes the analytics backbone for later phases.
- **Twilio escalation** – Account exists (verification pending) and credentials live in 1Password (`Twilio`). Once activated, Missive/n8n can trigger SMS, WhatsApp, or voice alerts for VIP or urgent cases.
- **Cal.com + 11.ai voice** – Already connected: when a thread needs a call, the system can send a Cal.com link that plays the Premium Gastro voice, giving customers a consistent experience.
- **Gmail/Gemini watchlist** – Documented for future comparison; once Google exposes reliable backend hooks we can decide whether to augment or replace pieces of the Missive stack.

## 📊 ROI & Impact

### Time Savings

- **Current**: 75% reduction in email processing time
- **Target**: 90% automation across all communications
- **Value**: 4+ hours saved daily = €4,400 monthly value

### Cost Efficiency

- **Email Processing**: $600 → $150/month (75% reduction)
- **Complete System**: ~$417/month total
- **ROI**: 1,008% monthly return on investment

## 📁 Project Structure

```
/
├── PG_2.0_TRANSFORMATION_ANCHOR.md         # PG 2.0 transformation master doc
├── PG_2.0_EXECUTION_LOG.md                 # Daily/weekly execution tracking
├── PG_2.0_ROLE_BOUNDARIES.md               # Lucy/Pan Talir/Zeus interfaces
├── PREMIUM_GASTRO_ASSISTANT_MASTERPLAN.md  # Complete roadmap
├── EMAIL_AUTOMATION_DEPLOYED.md            # Phase 1 documentation
├── SUPABASE_VIP_ANALYZER.py               # VIP contact detection
├── INTELLIGENT_EMAIL_PROCESSOR.py         # Email classification system
├── MISSIVE_AI_ASSISTANT.py                # Missive integration
├── MOBILE_APP_PROTOTYPE.py                # Mobile assistant prototype
├── APP_NAVIGATION_AGENT.py                # Error-free navigation bot
├── APP_NAVIGATION_AGENT_GUIDE.md          # Navigation agent documentation
├── NAVIGATION_AGENT_QUICKSTART.md         # Quick start guide
├── NAVIGATION_AGENT_EXAMPLES.py           # Example workflows
├── tests/test_app_navigation_agent.py     # Navigation agent tests
└── phase6_workflows/                       # N8n workflow definitions
```

## 🚦 Quick Start

### Prerequisites

1. **Python 3.12+** installed
2. **1Password CLI** (recommended for production) OR `.env` file (development)

### Credential Setup

This project supports two methods for managing credentials:

#### Option 1: 1Password CLI (Recommended for Production)

```bash
# Install 1Password CLI
brew install --cask 1password-cli  # macOS
# Or download from: https://1password.com/downloads/command-line/

# Sign in
op signin

# Create "AI" vault in 1Password and add credentials
# The application will automatically load from 1Password
```

**Benefits:**
- ✅ Centralized secret management
- ✅ No secrets in code or `.env` files
- ✅ Easy credential rotation
- ✅ Team credential sharing
- ✅ Audit trail via logging

#### Option 2: .env File (Development/Testing)

```bash
# Copy example and fill in your values
cp env.example .env

# Edit .env with your credentials
# The application automatically falls back to .env if 1Password not available
```

**Important:** The `.env` file is gitignored and should NEVER be committed.

### Install Dependencies

```bash
# Install all dependencies from requirements.txt (recommended)
pip install -r requirements.txt

# Or install core dependencies individually:
pip install python-dotenv requests pytest pytest-asyncio aiohttp
```

### App Navigation Agent (NEW - Phase 6)

```bash
# Demo the navigation bot
python3 APP_NAVIGATION_AGENT.py

# Run example workflows
python3 NAVIGATION_AGENT_EXAMPLES.py

# Run tests
python3 -m pytest tests/test_app_navigation_agent.py -v
```

**Features:**
- ✅ Error-free navigation between app modules
- ✅ Multi-agent coordination for complex workflows
- ✅ Automatic error recovery
- ✅ 23 comprehensive tests, all passing

See [NAVIGATION_AGENT_QUICKSTART.md](NAVIGATION_AGENT_QUICKSTART.md) for integration guide.

### Email System (Already Deployed)

```bash
# Test VIP analysis
python3 SUPABASE_VIP_ANALYZER.py

# Test email processing
python3 INTELLIGENT_EMAIL_PROCESSOR.py
```

### Next Phase: Conversation Intelligence

1. **Whisper API Setup**: Phone call transcription
2. **Otter.ai Integration**: Meeting intelligence
3. **Supabase Sync**: Conversation storage and analysis

## 🎯 Success Metrics

- ✅ **Email Automation**: 95% achieved
- 🔄 **Meeting Follow-up**: 90% target
- 📋 **Document Processing**: 85% target
- 📱 **Social Media**: 100% automation target
- ⚡ **Response Time**: <2 hours across all channels

## 🔮 Vision

**Transform Premium Gastro into the most technologically advanced food service business in Central Europe, where AI handles 90% of routine communications, allowing focus on core business growth and client relationships.**

Every phone call transcribed. Every note digitized. Every email intelligently processed. Every social media post optimized. Every client interaction enhanced by AI.

## 📧 Contact

Built for Premium Gastro by AI automation specialists.

**Ready for immediate implementation. The future of business automation starts now.**

---

## 📝 Development Log

- **2025-10-09**: Phase 1 Email Intelligence System deployed
- **2025-10-09**: Complete masterplan and roadmap created
- **2025-10-09**: Research completed for all 6 phases
- **2025-10-09**: GitHub repository established

---

## ✅ Indexing Methodology (Do / Don't + Lessons Learned)

**Purpose:** Build a reliable semantic indexing pipeline (filesystem → embeddings → vector DB) with auditability and zero silent failures.

### ✅ Do (Correct Method)
- **Validate embeddings first**: run a 1‑request embedding call and verify a numeric vector is returned.
- **Auto‑detect vector size** from the embedding model and **create the collection with that exact size**.
- **Use valid IDs**: UUID or 64‑bit integer. Deterministic UUID (e.g., UUID from md5 of path) is safe for re‑runs.
- **Use the correct Qdrant upsert contract**:  
  `PUT /collections/{name}/points?wait=true` with:
  ```json
  {
    "points": [
      {"id": "<uuid>", "vector": [..], "payload": {"path": "...", "name": "...", "size": 123, "mtime": 1700000000}}
    ]
  }
  ```
- **Keep batches small and auditable** (e.g., 16–64 points per batch).
- **Write an audit log** per batch (`batch_id`, `count`, `first_path`, `last_path`, `status`, `timestamp`).
- **Log start + totals** (`total_files`, provider, collection) and final summary.
- **Use a reliable background runner** (LaunchAgent/systemd) for long runs.
- **Index non‑text safely**: use filename/metadata only; cap bytes for large text files.

### ❌ Don’t (Common Failure Modes)
- **Don’t** `POST /points` with record format if the server expects batch format — it will reject silently or with confusing errors.
- **Don’t** use arbitrary string IDs (Qdrant requires UUID or uint64).
- **Don’t** hard‑code versioned schema paths (breaks after extension updates).
- **Don’t** rely on fragile background methods (`nohup`) where the OS kills jobs.
- **Don’t** embed binary blobs or huge files without size caps.

### ✅ Minimal Payload Standard
- `path` (string), `name` (string), `size` (int), `mtime` (int), `source` (string)
- **Never** include secrets or raw file contents in logs.

### ✅ Verification Checklist
- `points_count` increases after a 1‑file smoke test.
- Audit log contains successful batches with increasing `batch_id`.
- Final count matches expectations (or is explainable by filtered/skipped files).

### ✅ Security & Privacy Hygiene
- Store tokens in OS keychain or env only.
- Keep logs metadata‑only.
- Never commit `.env` or secrets.

### Lessons Learned (Core)
- **APIs must be validated against the running version** (contract drift is real).
- **Correct upsert format + valid IDs** is the difference between “running” and “actually indexing.”
- **Background reliability is part of correctness.**

**Last updated:** 2026-02-07

**Canonical scripts:** `tools/indexing/`
