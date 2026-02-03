# 🗂️ Git Repository Inventory - Digital Hygiene Audit

**Generated:** 2026-02-03  
**Total Repositories Found:** 57 local Git repos on your Mac

---

## 🚨 CRITICAL DUPLICATES DETECTED

### Premium Gastro AI Assistant (4 COPIES!)
1. ✅ **ACTIVE:** `/Users/premiumgastro/premium-gastro-ai-assistant` (current working directory)
   - Remote: https://github.com/darkangelpraha/premium-gastro-ai-assistant.git
   - Branch: `claude/ai-assistant-interface-design-WYXJz` (84 ahead, 38 behind)
   
2. 🔍 **SECURITY FORK:** `/Users/premiumgastro/premium-gastro-ai-assistant-ghsa-658q-wh8w-4cqm`
   - Likely: GitHub Security Advisory fork - KEEP for security fixes
   
3. ⚠️ **DUPLICATE:** `/Users/premiumgastro/Projects/premium-gastro-ai-assistant`
   - Status: UNKNOWN - needs investigation
   
4. ⚠️ **DUPLICATE:** `/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant`
   - Status: UNKNOWN - needs investigation

---

## 📊 REPOSITORY CATEGORIES

### Premium Gastro Suite (9 repos)
- `premium-gastro-ai-assistant` (x4 - see above)
- `premium-gastro-magic-stack`
- `premium-gastro-pim`
- `premium-gastro-automations`
- `premium-gastro-infrastructure`
- `premium-gastro-workspace`
- `premium-gastro-gdpr-tracking`
- `premium-gastro-upload`

### Pan-Talir Projects (2 repos)
- `pan-talir-missive-sidebar`
- `pan-talir-missive`

### MCP Servers (12 repos)
- `mcp-remote-macos-use_claude`
- `steel-puppeteer-mcp`
- `gistpad-mcp`
- `github-mcp-server`
- `mcp-api-gateway`
- `google-ads-mcp-server`
- `hyperbrowser-mcp`
- `mem0-mcp`
- `docker-mcp`
- `mcp-gateway`
- `discord-webhook-mcp`
- `canva-mcp-server`
- `mcp-memory-service` (x2 - DUPLICATE!)

### Business Tools (3 repos)
- `google-ecosystem-audit-framework`
- `business-excellence-framework`
- `todoist`

### Development Tools (5 repos)
- `vscode-go`
- `python-sdk`
- `vscode-twitter`
- `Tests`
- `splinter`

### Integrations (4 repos)
- `google-sheets-mcp`
- `supabase`
- `Gmail-MCP-Server`
- `firecrawl-selfhost`

### N8N Ecosystem (2 repos)
- `n8n`
- `n8n-nodes-skyvern`

### AI Agents (4 repos)
- `perplexity-tool`
- `Agent-Zero`
- `mem0`
- `xai-grok-mcp-server`

### Legacy/Archive (2 repos)
- `Legacy_Registry`
- `vscode_database_backup_20250709_222712`

### Miscellaneous (14 repos)
- `openwork`
- `icon-shelf`
- `AppleScript`
- `lucy_system`
- `phosphor-icons`
- `.codex/vendor_imports/skills`
- `BlueJet/git`
- `PG_Screensaver_Development` (NO REMOTE - orphaned?)
- `claude-nas-rag` (connected to GitHub)
- `legendary-guide` (connected to GitHub)
- `LandmarksBuildingAnAppWithLiquidGlass` (NO REMOTE - orphaned?)

---

## 🎯 SALVAGE & CLEANUP STRATEGY

### Phase 1: Investigation (DO NOT DELETE YET)
**Action:** Inspect duplicates to find valuable uncommitted work

```bash
# Compare duplicate repos
cd /Users/premiumgastro/Projects/premium-gastro-ai-assistant
git status
git log --oneline -10
git diff origin/main

cd /Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant
git status
git log --oneline -10
```

### Phase 2: Salvage Uncommitted Work
**Before deletion:** Check each duplicate for:
- [ ] Uncommitted changes (`git status`)
- [ ] Unpushed commits (`git log origin/main..HEAD`)
- [ ] Stashed changes (`git stash list`)
- [ ] Local branches not on remote (`git branch -vv`)
- [ ] Untracked files that matter

### Phase 3: Consolidation Plan (PENDING YOUR APPROVAL)

#### Keep One Canonical Location Per Project
**Recommendation:** Organize by purpose:

```
~/Projects/
  Premium-Gastro/          # All production PG projects
  MCP/                     # All MCP servers
  Business/                # Business frameworks
  Development/             # Dev tools
  Integrations/            # Third-party integrations
  AI_Agents/               # AI agent experiments
  Archive/                 # Old/inactive projects
```

#### Proposed Deletions (AFTER SALVAGE)
- [ ] `/Users/premiumgastro/Projects/premium-gastro-ai-assistant` (if duplicate)
- [ ] `/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant` (if duplicate)
- [ ] `/Users/premiumgastro/Downloads/LandmarksBuildingAnAppWithLiquidGlass` (if no value)
- [ ] `/Users/premiumgastro/Documents/PG_Screensaver_Development` (if orphaned)
- [ ] One of two `mcp-memory-service` copies

### Phase 4: Establish Single Source of Truth
**Canonical repo locations:**
- **Active development:** `/Users/premiumgastro/premium-gastro-ai-assistant`
- **Organized projects:** `~/Projects/[Category]/[repo-name]`
- **Experiments:** `~/Projects/Archive/[repo-name]`

---

## 🔍 NEXT INVESTIGATION STEPS

### 1. Duplicate Analysis
```bash
# For each duplicate pair, run:
diff -r --brief \
  /Users/premiumgastro/premium-gastro-ai-assistant \
  /Users/premiumgastro/Projects/premium-gastro-ai-assistant
```

### 2. Orphaned Repo Check
```bash
# Find repos without remotes
for repo in [list]; do
  cd "$repo"
  if ! git remote -v | grep -q "origin"; then
    echo "ORPHANED: $repo"
  fi
done
```

### 3. Disk Space Recovery
```bash
# Calculate total space used by duplicates
du -sh /Users/premiumgastro/**/premium-gastro-ai-assistant
```

---

## ⚠️ AWAITING YOUR EXPLICIT APPROVAL

**No files will be deleted or moved without your direct confirmation.**

### What I need from you:

1. **Which duplicate repos should I investigate first?**
   - `premium-gastro-ai-assistant` copies?
   - `mcp-memory-service` copies?
   - Orphaned repos in Downloads/Documents?

2. **Your preferred organization structure?**
   - Keep current scattered locations?
   - Consolidate into `~/Projects/[Category]/`?
   - Different approach?

3. **What counts as "valuable" for salvage?**
   - Any uncommitted changes?
   - Unpushed commits from last X days?
   - Specific files/branches?

4. **GitHub Desktop disconnection troubleshooting?**
   - Do you still use GitHub Desktop?
   - Should we reconnect repos or migrate to CLI-only?

---

## 📈 ESTIMATED SAVINGS

**Potential disk space recovery:** TBD (need du -sh analysis)  
**Reduced mental overhead:** 4 duplicate repos → 1 canonical  
**Improved workflow:** Clear organization vs scattered clones

---

**Status:** 🟡 Audit Complete - Awaiting Instructions  
**Safety:** ✅ No changes made - everything preserved
