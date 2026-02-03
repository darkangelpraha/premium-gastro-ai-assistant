# 🎯 Repository Cleanup & Consolidation Action Plan

**Status:** EXECUTING  
**Date:** 2026-02-03  
**Estimated Time:** 2-3 hours  
**Estimated Space Recovery:** ~1.8 GB

---

## 📊 ANALYSIS SUMMARY

### Current Repository (#1 - ACTIVE)
- **Location:** `/Users/premiumgastro/premium-gastro-ai-assistant`
- **Size:** 1.5GB
- **Commits:** 184 total
- **Branch:** `claude/ai-assistant-interface-design-WYXJz` 
- **Status:** ⚠️ 84 unpushed commits, 2 untracked files
- **Remote:** Connected to GitHub
- **Action:** KEEP - Primary working directory

### Duplicate #2 (Security Fork - KEEP)
- **Location:** `/Users/premiumgastro/premium-gastro-ai-assistant-ghsa-658q-wh8w-4cqm`
- **Size:** 42MB
- **Commits:** Similar to main
- **Branch:** `advisory-fix-1`
- **Status:** ✅ Clean, all pushed
- **Remote:** GitHub Security Advisory fork
- **Action:** KEEP - Active security work

### Duplicate #3 (STALE - DELETE AFTER SALVAGE)
- **Location:** `/Users/premiumgastro/Projects/premium-gastro-ai-assistant`
- **Size:** 1.0MB
- **Commits:** 43 (OLD - missing 141 commits!)
- **Branch:** `claude/review-skills-repo-1f8In`
- **Status:** ⚠️ Deleted files + "_IX.md" junk files
- **Remote:** Connected but outdated
- **Action:** SALVAGE "_IX.md" files → DELETE

### Duplicate #4 (VERY STALE - DELETE AFTER SALVAGE)
- **Location:** `/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant`
- **Size:** 596KB
- **Commits:** 26 (VERY OLD - missing 158 commits!)
- **Branch:** `main`
- **Status:** ⚠️ Deleted files + "_IX.md" junk files
- **Remote:** Connected but very outdated
- **Action:** SALVAGE "_IX.md" files → DELETE

### Orphaned Repo #1 (DECISION NEEDED)
- **Location:** `/Users/premiumgastro/Documents/PG_Screensaver_Development`
- **Size:** 302MB
- **Commits:** Unknown count
- **Status:** ✅ Clean, NO REMOTE
- **Last Activity:** 4 months ago
- **Action:** CREATE GITHUB REPO + PUSH or ARCHIVE

### Orphaned Repo #2 (LIKELY DELETE)
- **Location:** `/Users/premiumgastro/Downloads/LandmarksBuildingAnAppWithLiquidGlass`
- **Size:** 322MB
- **Commits:** Unknown count
- **Status:** ✅ Clean, NO REMOTE
- **Last Activity:** 7 months ago (Apple sample code)
- **Action:** DELETE (can re-download from Apple)

---

## 🚀 EXECUTION PLAN

### Phase 1: Current Repo Cleanup ✅ IN PROGRESS
**Goal:** Clean up primary working directory

#### Step 1.1: Commit investigation files
```bash
cd /Users/premiumgastro/premium-gastro-ai-assistant
git add REPOSITORY_INVENTORY.md investigate_duplicates.sh CLEANUP_ACTION_PLAN.md
git commit -m "docs: Add repository cleanup and investigation tools"
```

#### Step 1.2: Resolve branch divergence
**Decision needed:** Merge or rebase the 84 unpushed commits?
- Option A: `git pull --rebase origin claude/ai-assistant-interface-design-WYXJz`
- Option B: `git pull --no-rebase origin claude/ai-assistant-interface-design-WYXJz`
- Option C: Force push (risky): `git push --force-with-lease`

#### Step 1.3: Push to GitHub
```bash
git push origin claude/ai-assistant-interface-design-WYXJz
```

---

### Phase 2: Pull Request Management 🔄 NEXT
**Goal:** Close/merge 7 open PRs

#### PR Triage Strategy
- **MERGE:** PRs #27, #24, #22 (approved security/doc fixes)
- **CLOSE:** PR #26 (blocked - missing context)
- **REVIEW:** PRs #25, #23, #19 (decide keep/close)

---

### Phase 3: Salvage Duplicate Repos 💾 PENDING
**Goal:** Extract valuable "_IX.md" files before deletion

#### Step 3.1: Check what "_IX.md" files are
```bash
cd /Users/premiumgastro/Projects/premium-gastro-ai-assistant
head -20 PREMIUM_GASTRO_ASSISTANT_MASTERPLAN_IX.md
# If valuable → copy to main repo
# If junk → ignore
```

#### Step 3.2: Salvage if needed
```bash
# Only if "_IX.md" files contain unique content
cp *_IX.md /Users/premiumgastro/premium-gastro-ai-assistant/archive/
```

---

### Phase 4: Delete Duplicate Repos 🗑️ PENDING APPROVAL
**Goal:** Remove confirmed duplicates

```bash
# Duplicate #3 (after salvage)
rm -rf /Users/premiumgastro/Projects/premium-gastro-ai-assistant

# Duplicate #4 (after salvage)
rm -rf /Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant

# Space recovered: ~1.6MB
```

---

### Phase 5: Handle Orphaned Repos 📦 PENDING DECISION

#### Option A: Publish PG_Screensaver_Development
```bash
cd /Users/premiumgastro/Documents/PG_Screensaver_Development
gh repo create premium-gastro-screensaver --private --source=. --remote=origin
git push -u origin main
# Move to: ~/Projects/Premium-Gastro/premium-gastro-screensaver
```

#### Option B: Archive PG_Screensaver_Development
```bash
mkdir -p ~/Projects/Archive
mv /Users/premiumgastro/Documents/PG_Screensaver_Development \
   ~/Projects/Archive/
```

#### Option C: Delete LandmarksBuildingAnAppWithLiquidGlass
```bash
rm -rf /Users/premiumgastro/Downloads/LandmarksBuildingAnAppWithLiquidGlass
# Space recovered: 322MB
```

---

### Phase 6: Establish Repository Organization 📁 PENDING
**Goal:** Create consistent structure

#### Proposed Structure
```
~/Projects/
├── Premium-Gastro/
│   ├── premium-gastro-ai-assistant (canonical location)
│   ├── premium-gastro-magic-stack
│   ├── premium-gastro-infrastructure
│   └── premium-gastro-screensaver (if published)
├── MCP/ (12 servers)
├── Business/ (3 frameworks)
├── Integrations/ (4 services)
├── Development/ (5 dev tools)
└── Archive/ (inactive projects)
```

#### Migration (if approved)
```bash
# Move active development repo to canonical location
# NOT recommended mid-project - wait for stable point
```

---

### Phase 7: Branch Cleanup 🌿 PENDING
**Goal:** Remove stale/merged branches

```bash
# List all remote branches
gh api repos/darkangelpraha/premium-gastro-ai-assistant/branches --paginate

# Delete merged branches
git branch --merged main | grep -v "main" | xargs git branch -d

# Clean up remote tracking
git remote prune origin
```

---

### Phase 8: GitHub Actions & CI/CD ⚙️ PENDING
**Goal:** Add missing workflows

#### Create: `.github/workflows/pytest.yml`
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

#### Create: `.github/PULL_REQUEST_TEMPLATE.md`
#### Create: `.github/CODEOWNERS`

---

## 📈 EXPECTED OUTCOMES

### Space Recovery
- Duplicate repos: ~1.6MB
- Orphaned Apple sample: 322MB
- **Total: ~324MB**

### Repository Health
- ✅ Single source of truth established
- ✅ All PRs resolved
- ✅ Stale branches removed
- ✅ CI/CD tests enabled
- ✅ Clear organization structure

### Development Velocity
- ⚡ No more confusion about which repo to use
- ⚡ Faster PR turnaround with tests
- ⚡ Clear contribution workflow

---

## ⚠️ PENDING APPROVALS

### Immediate Actions (Ready to execute)
- [x] Commit investigation files to main repo
- [ ] Push 84 commits to GitHub (rebase strategy?)
- [ ] Merge approved PRs (#27, #24, #22)
- [ ] Close blocked PR (#26)

### Salvage Operations (Need inspection)
- [ ] Check "_IX.md" files for value
- [ ] Extract if valuable, ignore if junk

### Deletions (Need explicit approval)
- [ ] Delete `/Users/premiumgastro/Projects/premium-gastro-ai-assistant`
- [ ] Delete `/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant`
- [ ] Delete `/Users/premiumgastro/Downloads/LandmarksBuildingAnAppWithLiquidGlass`

### Orphaned Repo Decisions
- [ ] PG_Screensaver_Development: Publish to GitHub? Archive? Delete?

---

**Next Command Awaiting Your Approval:**
```bash
# Commit current work
git add REPOSITORY_INVENTORY.md investigate_duplicates.sh CLEANUP_ACTION_PLAN.md
git commit -m "docs: Add repository cleanup and investigation tools"

# Then resolve branch divergence (your choice):
# A) git pull --rebase origin claude/ai-assistant-interface-design-WYXJz
# B) git push --force-with-lease origin claude/ai-assistant-interface-design-WYXJz
```

**Status:** 🟡 Awaiting approval to proceed with Phase 1
