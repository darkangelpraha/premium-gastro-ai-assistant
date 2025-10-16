# Phase 6 Automation Workflows

**Created:** 2025-10-16
**Purpose:** Notion ↔ Asana bidirectional sync workflows

## Contents

This directory contains n8n workflow definitions ready for import:

1. **workflow_1_supplier_to_asana.json**
   - Notion Supplier created → Auto-create Asana task
   - Polls Notion Suppliers DB every 5 minutes
   - Creates task in DODAVATELÉ (1207809086806827)

2. **workflow_2_asana_to_notion.json**
   - Asana task completed → Update Notion Supplier status
   - Polls Asana DODAVATELÉ for completions
   - Updates Notion Suppliers DB

3. **workflow_3_tech_cost_monitor.json**
   - Monthly tech stack cost monitoring
   - Runs 1st of month at 9:00 AM
   - Alerts if total cost > threshold

4. **workflow_4_tech_evaluation.json**
   - New tech tool → Auto-create evaluation task
   - Polls Notion Tech Stack DB every 15 minutes
   - Creates task in tech_strack (1211547448108353)

## Naming Convention

All workflows use this format:
```
[PHASE 6 SYNC] {Description} [INACTIVE]
```

## Safety Features

- ✅ All workflows start INACTIVE
- ✅ Clearly labeled with [PHASE 6 SYNC] prefix
- ✅ Tagged: phase6, notion-asana-sync, INACTIVE
- ✅ Never delete data (only create/update)
- ✅ Polling-based (no webhook setup needed)
- ✅ Error handling with retries

## Import to n8n

**Option 1:** Via n8n UI
1. Open n8n: http://localhost:5678
2. Click "+" → "Import from File"
3. Select workflow JSON
4. Review and save (stays INACTIVE)

**Option 2:** Via API (automated)
```bash
N8N_API_KEY=$(op read "op://AI/n8n local API key/password")
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @workflow_1_supplier_to_asana.json
```

## Before Activation

Review checklist in: `/Users/premiumgastro/PHASE_6_WORKFLOWS_STATUS.md`

