# Phase 6 Workflows - Import Instructions

**Created:** 2025-10-16
**Status:** ✅ All 4 workflows ready for import

---

## 📂 WORKFLOW FILES READY

All workflow JSON files are in: `/Users/premiumgastro/phase6_workflows/`

1. `workflow_1_supplier_to_asana.json` - Notion Supplier → Asana Task
2. `workflow_2_asana_to_notion.json` - Asana Complete → Notion Update
3. `workflow_3_tech_cost_monitor.json` - Monthly Cost Monitoring
4. `workflow_4_tech_evaluation.json` - Tech Tool Evaluation Tasks

---

## 🚀 IMPORT METHOD (Choose One)

### Method 1: n8n Web UI (RECOMMENDED)

**Why:** Easiest, allows immediate credential configuration

**Steps:**
1. Open n8n: http://localhost:5678
2. Click "Add Workflow" button (top right)
3. Click menu (⋮) → "Import from File"
4. Select workflow JSON file
5. Review workflow (will be INACTIVE)
6. Click "Save" (stays INACTIVE until you activate)
7. Configure credentials (see section below)
8. Repeat for all 4 workflows

### Method 2: n8n CLI Import

**Why:** Faster for importing all 4 at once

**Steps:**
```bash
cd /Users/premiumgastro/phase6_workflows

# Import each workflow
for workflow in workflow_*.json; do
  echo "Importing $workflow..."
  N8N_API_KEY=$(op read "op://AI/n8n local API key/password")

  curl -X POST http://localhost:5678/api/v1/workflows/import \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: multipart/form-data" \
    -F "file=@$workflow"
done
```

**Note:** After CLI import, you MUST configure credentials via UI

---

## 🔐 CREDENTIAL CONFIGURATION (Required After Import)

Each workflow uses HTTP Request nodes that need credentials configured.

### Step 1: Create Notion API Credential

1. In n8n, go to "Credentials" menu
2. Click "Add Credential"
3. Select "Header Auth"
4. Configure:
   - **Name:** `Notion API - Premium Gastro`
   - **Name:** `Authorization`
   - **Value:** `Bearer {NOTION_TOKEN}`

**Get Notion Token:**
```bash
op read "op://AI/Alice Notion API/credential"
```

5. Also add another header:
   - **Name:** `Notion-Version`
   - **Value:** `2022-06-28`

6. Test and Save

### Step 2: Create Asana API Credential

1. In n8n, go to "Credentials" menu
2. Click "Add Credential"
3. Select "Header Auth"
4. Configure:
   - **Name:** `Asana API - Premium Gastro`
   - **Name:** `Authorization`
   - **Value:** `Bearer {ASANA_TOKEN}`

**Get Asana Token:**
```bash
op read "op://AI/Claude Asana Token/credential"
```

5. Test and Save

### Step 3: Assign Credentials to Workflows

For **each workflow** after import:

1. Open workflow in n8n
2. Find HTTP Request nodes (marked with ⚠️ warning)
3. Click on each HTTP Request node
4. Select appropriate credential:
   - Notion API calls → Select "Notion API - Premium Gastro"
   - Asana API calls → Select "Asana API - Premium Gastro"
5. Save workflow

**Workflows that need Notion credentials:**
- Workflow 1: "Query Notion Suppliers" node
- Workflow 2: "Find Supplier in Notion", "Update Notion Status" nodes
- Workflow 3: "Query Active Tools" node
- Workflow 4: "Query Tools Under Evaluation" node

**Workflows that need Asana credentials:**
- Workflow 1: "Create Asana Task" node
- Workflow 2: "Query Completed Tasks" node
- Workflow 3: "Create Alert Task" node
- Workflow 4: "Create Evaluation Task" node

---

## ✅ VERIFICATION CHECKLIST

After import and credential configuration:

### For Each Workflow:
- [ ] Workflow imported successfully
- [ ] Workflow name shows `[PHASE 6 SYNC]` prefix
- [ ] Workflow shows `[INACTIVE]` in name
- [ ] No ⚠️ warnings on HTTP Request nodes
- [ ] All credentials configured
- [ ] Workflow saved
- [ ] Workflow remains INACTIVE

### Overall:
- [ ] Total workflows in n8n = 6 (2 existing + 4 new)
- [ ] Active workflows = 2 (only your existing ones)
- [ ] New workflows tagged with "phase6"
- [ ] New workflows clearly labeled

---

## 🧪 TESTING (After Import & Credential Setup)

### Test Workflow 1 (Supplier → Asana)

1. In Notion, create test supplier:
   - Name: "Test Supplier - PHASE 6"
   - Onboarding Stage: "In Progress"
2. In n8n, open Workflow 1
3. Click "Execute Workflow" (manual test)
4. Check execution log - should create Asana task
5. Verify in Asana DODAVATELÉ project
6. If successful, activate workflow (toggle to ACTIVE)

### Test Workflow 2 (Asana → Notion)

1. In Asana, complete the test task created above
2. In n8n, execute Workflow 2 manually
3. Check execution log - should update Notion
4. Verify in Notion - Onboarding Stage should be "Completed"
5. If successful, activate workflow

### Test Workflow 3 (Tech Cost Monitor)

1. In n8n, execute Workflow 3 manually (don't wait for monthly schedule)
2. Check execution log - should calculate total costs
3. If over $500, check Asana tech_strack for alert task
4. If successful, activate workflow (will run monthly)

### Test Workflow 4 (Tech Evaluation)

1. In Notion Tech Stack, create test tool:
   - Name: "Test Tool - PHASE 6"
   - Status: "Under Evaluation"
2. In n8n, execute Workflow 4 manually
3. Check execution log - should create Asana task
4. Verify in Asana tech_strack project
5. If successful, activate workflow

---

## ⚠️ IMPORTANT SAFETY NOTES

### Before Activating:
- ✅ Test each workflow manually first
- ✅ Verify no duplicate tasks created
- ✅ Check execution logs for errors
- ✅ Ensure credentials work correctly

### What INACTIVE means:
- Workflows won't run on schedule
- Can still test manually via "Execute Workflow"
- No automatic polling or sync
- Safe to import and configure

### What ACTIVE means:
- Workflow will run on schedule (every 5/15 min or monthly)
- Will automatically poll Notion/Asana
- Will create tasks automatically
- **Only activate after successful testing**

---

## 🔄 ROLLBACK (If Needed)

If you need to remove workflows:

1. In n8n, open workflow
2. Click menu (⋮) → "Delete"
3. Confirm deletion
4. Workflow and all executions removed

**Existing workflows:** Your 2 existing workflows are NOT affected - they remain untouched.

**Asana tasks created:** If workflows created unwanted tasks, manually delete them in Asana.

---

## 📊 EXPECTED RESULTS AFTER IMPORT

### In n8n UI:
- Total workflows: 6
- Active: 2 (existing)
- Inactive: 4 (new Phase 6)
- Workflows list shows:
  - `[PHASE 6 SYNC] Notion Supplier → Asana Task [INACTIVE]`
  - `[PHASE 6 SYNC] Asana Complete → Notion Update [INACTIVE]`
  - `[PHASE 6 SYNC] Monthly Tech Stack Cost Alert [INACTIVE]`
  - `[PHASE 6 SYNC] Tech Tool Evaluation Task [INACTIVE]`

### Tags visible:
- `phase6`
- `notion-asana-sync`
- `INACTIVE`

---

## 📞 TROUBLESHOOTING

### Issue: Import fails
**Solution:** Make sure JSON file is valid, try Method 1 (UI import)

### Issue: ⚠️ warnings on HTTP nodes
**Solution:** Configure credentials (see Credential Configuration section)

### Issue: Credential test fails
**Solution:** Check token in 1Password, ensure it's valid

### Issue: Workflow creates duplicate tasks
**Solution:** Deactivate immediately, check "last_check" logic in code nodes

### Issue: Workflow doesn't create any tasks
**Solution:** Check n8n execution log for errors, verify database IDs are correct

---

## 📋 NEXT STEPS

1. ✅ Import all 4 workflows (via UI or CLI)
2. ✅ Configure Notion + Asana credentials
3. ✅ Assign credentials to HTTP Request nodes
4. ✅ Save all workflows (keep INACTIVE)
5. ✅ Test each workflow manually
6. ✅ Verify results in Notion and Asana
7. ✅ Activate workflows one by one
8. ✅ Monitor execution logs for 24-48 hours

---

**Ready to Import!** All workflow files are prepared and documented.

**Questions?** Check `/Users/premiumgastro/PHASE_6_BUILD_SUMMARY.md` for architecture details.
