#!/bin/bash
# 🔍 Repository Duplicate Investigation Script
# Safely analyzes duplicate repos without making ANY changes
# Generated: 2026-02-03

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🔍 Premium Gastro Repository Duplicate Analysis"
echo "=================================================="
echo ""

# Function to analyze a repo
analyze_repo() {
    local repo_path="$1"
    local repo_name=$(basename "$repo_path")
    
    if [ ! -d "$repo_path/.git" ]; then
        echo -e "${RED}✗ NOT A GIT REPO: $repo_path${NC}"
        return
    fi
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📁 ANALYZING: $repo_path${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    cd "$repo_path" || return
    
    # Basic info
    echo -e "\n${YELLOW}📊 BASIC INFO:${NC}"
    echo "   Path: $repo_path"
    echo "   Size: $(du -sh . 2>/dev/null | awk '{print $1}')"
    
    # Remote status
    echo -e "\n${YELLOW}🌐 REMOTE CONFIGURATION:${NC}"
    if git remote -v | grep -q "origin"; then
        git remote -v | head -2
    else
        echo -e "   ${RED}⚠️  NO REMOTE CONFIGURED (ORPHANED)${NC}"
    fi
    
    # Current branch
    echo -e "\n${YELLOW}🌿 BRANCH STATUS:${NC}"
    current_branch=$(git branch --show-current 2>/dev/null || echo "detached HEAD")
    echo "   Current: $current_branch"
    echo "   All branches:"
    git branch -a | sed 's/^/     /'
    
    # Uncommitted changes
    echo -e "\n${YELLOW}📝 UNCOMMITTED CHANGES:${NC}"
    if git status --porcelain | grep -q .; then
        echo -e "   ${RED}⚠️  HAS UNCOMMITTED CHANGES:${NC}"
        git status --short | sed 's/^/     /'
    else
        echo -e "   ${GREEN}✓ Clean working tree${NC}"
    fi
    
    # Unpushed commits
    echo -e "\n${YELLOW}📤 UNPUSHED COMMITS:${NC}"
    if git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1; then
        unpushed=$(git log @{upstream}..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
        if [ "$unpushed" -gt 0 ]; then
            echo -e "   ${RED}⚠️  $unpushed UNPUSHED COMMITS:${NC}"
            git log @{upstream}..HEAD --oneline | head -5 | sed 's/^/     /'
        else
            echo -e "   ${GREEN}✓ All commits pushed${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠️  No upstream branch configured${NC}"
    fi
    
    # Stashed changes
    echo -e "\n${YELLOW}💾 STASHED CHANGES:${NC}"
    stash_count=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
    if [ "$stash_count" -gt 0 ]; then
        echo -e "   ${RED}⚠️  $stash_count STASHES FOUND:${NC}"
        git stash list | sed 's/^/     /'
    else
        echo -e "   ${GREEN}✓ No stashes${NC}"
    fi
    
    # Last commit
    echo -e "\n${YELLOW}🕐 LAST ACTIVITY:${NC}"
    echo "   Last commit: $(git log -1 --format='%ar (%h)' 2>/dev/null || echo 'unknown')"
    echo "   Last commit message: $(git log -1 --format='%s' 2>/dev/null || echo 'unknown')"
    
    # Unique files not in .gitignore
    echo -e "\n${YELLOW}📄 UNTRACKED FILES (not ignored):${NC}"
    untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
    if [ "$untracked" -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  $untracked untracked files:${NC}"
        git ls-files --others --exclude-standard | head -10 | sed 's/^/     /'
        [ "$untracked" -gt 10 ] && echo "     ... and $((untracked - 10)) more"
    else
        echo -e "   ${GREEN}✓ No untracked files${NC}"
    fi
    
    echo ""
}

# Function to compare two repos
compare_repos() {
    local repo1="$1"
    local repo2="$2"
    
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}⚖️  COMPARING TWO REPOSITORIES${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo "Repo 1: $repo1"
    echo "Repo 2: $repo2"
    
    # Compare commits
    echo -e "\n${YELLOW}📊 COMMIT COMPARISON:${NC}"
    cd "$repo1"
    commits1=$(git rev-list --all --count 2>/dev/null || echo "0")
    cd "$repo2"
    commits2=$(git rev-list --all --count 2>/dev/null || echo "0")
    echo "   $repo1: $commits1 commits"
    echo "   $repo2: $commits2 commits"
    
    # Compare size
    echo -e "\n${YELLOW}💾 SIZE COMPARISON:${NC}"
    size1=$(du -sh "$repo1" 2>/dev/null | awk '{print $1}')
    size2=$(du -sh "$repo2" 2>/dev/null | awk '{print $1}')
    echo "   $repo1: $size1"
    echo "   $repo2: $size2"
    
    echo ""
}

# Analyze premium-gastro-ai-assistant duplicates
echo -e "${GREEN}🎯 ANALYZING PREMIUM GASTRO AI ASSISTANT COPIES${NC}\n"

REPOS=(
    "/Users/premiumgastro/premium-gastro-ai-assistant"
    "/Users/premiumgastro/premium-gastro-ai-assistant-ghsa-658q-wh8w-4cqm"
    "/Users/premiumgastro/Projects/premium-gastro-ai-assistant"
    "/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant"
)

for repo in "${REPOS[@]}"; do
    if [ -d "$repo" ]; then
        analyze_repo "$repo"
    else
        echo -e "${RED}✗ DOES NOT EXIST: $repo${NC}\n"
    fi
done

# Compare main repo with duplicates
echo -e "\n${GREEN}🔄 COMPARATIVE ANALYSIS${NC}\n"

if [ -d "/Users/premiumgastro/Projects/premium-gastro-ai-assistant" ]; then
    compare_repos \
        "/Users/premiumgastro/premium-gastro-ai-assistant" \
        "/Users/premiumgastro/Projects/premium-gastro-ai-assistant"
fi

if [ -d "/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant" ]; then
    compare_repos \
        "/Users/premiumgastro/premium-gastro-ai-assistant" \
        "/Users/premiumgastro/Projects/Premium-Gastro/premium-gastro-ai-assistant"
fi

# Check orphaned repos
echo -e "\n${GREEN}🔍 ORPHANED REPOSITORIES (No Remote)${NC}\n"

ORPHAN_CANDIDATES=(
    "/Users/premiumgastro/Documents/PG_Screensaver_Development"
    "/Users/premiumgastro/Downloads/LandmarksBuildingAnAppWithLiquidGlass"
)

for repo in "${ORPHAN_CANDIDATES[@]}"; do
    if [ -d "$repo" ]; then
        analyze_repo "$repo"
    fi
done

# Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ INVESTIGATION COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo "📋 Review the output above to determine:"
echo "   1. Which repos have valuable uncommitted work"
echo "   2. Which repos can be safely removed"
echo "   3. Which repos should be consolidated"
echo ""
echo "⚠️  NO CHANGES WERE MADE - This was read-only analysis"
echo ""
