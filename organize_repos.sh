#!/bin/bash
# 🗂️ Premium Gastro Repository Organization Script
# Safely organizes 57 Git repositories into a professional structure
# Date: 2026-02-03

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗂️  Premium Gastro Repository Organization${NC}"
echo "=========================================="
echo ""

# Confirmation
read -p "This will reorganize your repositories. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Backup current state
echo ""
echo -e "${YELLOW}📋 Creating backup list...${NC}"
BACKUP_FILE=~/repo_backup_$(date +%Y%m%d_%H%M%S).txt
find ~/Projects ~/premium-gastro-ai-assistant ~/Documents/PG_Screensaver_Development -type d -name ".git" 2>/dev/null | sed 's|/.git||' > "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup saved to $BACKUP_FILE${NC}"
echo "   (Contains list of all current repo locations)"

# Create organized structure
echo ""
echo -e "${YELLOW}📁 Creating organized directory structure...${NC}"
cd ~/Projects
mkdir -p 00-Premium-Gastro 01-Pan-Talir 02-MCP-Servers 03-Business-Tools 04-Integrations 05-AI-Experiments 06-Development-Tools 07-Scripts 08-Design-Assets 99-Legacy 99-Forks

echo -e "${GREEN}✅ Created organized folders:${NC}"
echo "   ~/Projects/00-Premium-Gastro/     - Premium Gastro production projects"
echo "   ~/Projects/01-Pan-Talir/          - Client work"
echo "   ~/Projects/02-MCP-Servers/        - Model Context Protocol servers"
echo "   ~/Projects/03-Business-Tools/     - Business frameworks"
echo "   ~/Projects/04-Integrations/       - Third-party integrations"
echo "   ~/Projects/05-AI-Experiments/     - AI research projects"
echo "   ~/Projects/06-Development-Tools/  - Dev utilities"
echo "   ~/Projects/07-Scripts/            - Automation scripts"
echo "   ~/Projects/08-Design-Assets/      - Graphics and icons"
echo "   ~/Projects/99-Legacy/             - Archived projects"
echo "   ~/Projects/99-Forks/              - External forks"

# Move main AI assistant (from home directory)
echo ""
echo -e "${YELLOW}🚚 Moving premium-gastro-ai-assistant (main)...${NC}"
if [ -d ~/premium-gastro-ai-assistant ]; then
    if [ ! -d ~/Projects/00-Premium-Gastro/premium-gastro-ai-assistant ]; then
        mv ~/premium-gastro-ai-assistant ~/Projects/00-Premium-Gastro/
        echo -e "${GREEN}✅ Moved to ~/Projects/00-Premium-Gastro/premium-gastro-ai-assistant${NC}"
        
        # Create symlink for compatibility
        ln -s ~/Projects/00-Premium-Gastro/premium-gastro-ai-assistant ~/premium-gastro-ai-assistant
        echo -e "${BLUE}   Created symlink at ~/premium-gastro-ai-assistant → new location${NC}"
    else
        echo -e "${YELLOW}⚠️  Already exists in target location${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Not found in ~/premium-gastro-ai-assistant (may already be moved)${NC}"
fi

# Move screensaver (now on GitHub)
echo ""
echo -e "${YELLOW}🚚 Moving screensaver...${NC}"
if [ -d ~/Documents/PG_Screensaver_Development ]; then
    if [ ! -d ~/Projects/00-Premium-Gastro/premium-gastro-screensaver ]; then
        mv ~/Documents/PG_Screensaver_Development ~/Projects/00-Premium-Gastro/premium-gastro-screensaver
        echo -e "${GREEN}✅ Moved to ~/Projects/00-Premium-Gastro/premium-gastro-screensaver${NC}"
    else
        echo -e "${YELLOW}⚠️  Already exists in target location${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Not found (may already be moved)${NC}"
fi

# Move existing Premium-Gastro repos
echo ""
echo -e "${YELLOW}🚚 Consolidating Premium-Gastro repos...${NC}"
if [ -d ~/Projects/Premium-Gastro ]; then
    moved_count=0
    for repo in ~/Projects/Premium-Gastro/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/00-Premium-Gastro/"$basename" ]; then
                mv "$repo" ~/Projects/00-Premium-Gastro/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/Premium-Gastro 2>/dev/null && echo -e "${GREEN}   ✓ Removed old Premium-Gastro folder${NC}" || echo -e "${YELLOW}   ⚠️  Could not remove old folder (may contain files)${NC}"
    echo -e "${GREEN}✅ Consolidated $moved_count Premium-Gastro repos${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/Premium-Gastro not found (may already be organized)${NC}"
fi

# Move MCP servers
echo ""
echo -e "${YELLOW}🚚 Organizing MCP servers...${NC}"
if [ -d ~/Projects/MCP ]; then
    moved_count=0
    for repo in ~/Projects/MCP/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/02-MCP-Servers/"$basename" ]; then
                mv "$repo" ~/Projects/02-MCP-Servers/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/MCP 2>/dev/null && echo -e "${GREEN}   ✓ Removed old MCP folder${NC}" || echo -e "${YELLOW}   ⚠️  Could not remove old folder (may contain files)${NC}"
    echo -e "${GREEN}✅ Organized $moved_count MCP servers${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/MCP not found (may already be organized)${NC}"
fi

# Move Pan-Talir projects
echo ""
echo -e "${YELLOW}🚚 Organizing Pan-Talir projects...${NC}"
if [ -d ~/Projects/Pan-Talir ]; then
    moved_count=0
    for repo in ~/Projects/Pan-Talir/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/01-Pan-Talir/"$basename" ]; then
                mv "$repo" ~/Projects/01-Pan-Talir/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/Pan-Talir 2>/dev/null && echo -e "${GREEN}   ✓ Removed old Pan-Talir folder${NC}" || true
    echo -e "${GREEN}✅ Organized $moved_count Pan-Talir projects${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/Pan-Talir not found${NC}"
fi

# Move Business tools
echo ""
echo -e "${YELLOW}🚚 Organizing Business tools...${NC}"
if [ -d ~/Projects/Business ]; then
    moved_count=0
    for repo in ~/Projects/Business/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/03-Business-Tools/"$basename" ]; then
                mv "$repo" ~/Projects/03-Business-Tools/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/Business 2>/dev/null && echo -e "${GREEN}   ✓ Removed old Business folder${NC}" || true
    echo -e "${GREEN}✅ Organized $moved_count business tools${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/Business not found${NC}"
fi

# Move Integrations
echo ""
echo -e "${YELLOW}🚚 Organizing Integrations...${NC}"
if [ -d ~/Projects/Integrations ]; then
    moved_count=0
    for repo in ~/Projects/Integrations/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/04-Integrations/"$basename" ]; then
                mv "$repo" ~/Projects/04-Integrations/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/Integrations 2>/dev/null && echo -e "${GREEN}   ✓ Removed old Integrations folder${NC}" || true
    echo -e "${GREEN}✅ Organized $moved_count integrations${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/Integrations not found${NC}"
fi

# Move AI experiments
echo ""
echo -e "${YELLOW}🚚 Organizing AI experiments...${NC}"
if [ -d ~/Projects/AI_Agents ]; then
    moved_count=0
    for repo in ~/Projects/AI_Agents/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/05-AI-Experiments/"$basename" ]; then
                mv "$repo" ~/Projects/05-AI-Experiments/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/AI_Agents 2>/dev/null && echo -e "${GREEN}   ✓ Removed old AI_Agents folder${NC}" || true
    echo -e "${GREEN}✅ Organized $moved_count AI experiments${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/AI_Agents not found${NC}"
fi

# Move Legacy/Archive
echo ""
echo -e "${YELLOW}🚚 Moving legacy projects...${NC}"
if [ -d ~/Projects/Archive ]; then
    moved_count=0
    for repo in ~/Projects/Archive/*; do
        if [ -d "$repo" ]; then
            basename=$(basename "$repo")
            if [ ! -d ~/Projects/99-Legacy/"$basename" ]; then
                mv "$repo" ~/Projects/99-Legacy/
                echo -e "${GREEN}   ✓ Moved $basename${NC}"
                ((moved_count++))
            fi
        fi
    done
    rmdir ~/Projects/Archive 2>/dev/null && echo -e "${GREEN}   ✓ Removed old Archive folder${NC}" || true
    echo -e "${GREEN}✅ Moved $moved_count legacy projects${NC}"
else
    echo -e "${YELLOW}⚠️  ~/Projects/Archive not found${NC}"
fi

# Set GitHub Desktop default
echo ""
echo -e "${YELLOW}⚙️  Configuring GitHub Desktop...${NC}"
defaults write com.github.GitHubClient "repositoriesFolder" ~/Projects
echo -e "${GREEN}✅ GitHub Desktop default folder set to ~/Projects${NC}"

# Verify main repo still works
echo ""
echo -e "${YELLOW}🔍 Verifying Git functionality...${NC}"
cd ~/Projects/00-Premium-Gastro/premium-gastro-ai-assistant 2>/dev/null && {
    git remote -v >/dev/null 2>&1 && echo -e "${GREEN}✅ Git remote connection verified${NC}" || echo -e "${RED}⚠️  Git remote check failed${NC}"
    git status >/dev/null 2>&1 && echo -e "${GREEN}✅ Git status working${NC}" || echo -e "${RED}⚠️  Git status failed${NC}"
} || echo -e "${YELLOW}⚠️  Could not verify (repo may not be in expected location)${NC}"

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Organization Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📊 New Structure:${NC}"
echo "   ~/Projects/00-Premium-Gastro/     - All Premium Gastro projects"
echo "   ~/Projects/01-Pan-Talir/          - Client projects"
echo "   ~/Projects/02-MCP-Servers/        - All MCP servers"
echo "   ~/Projects/03-Business-Tools/     - Business frameworks"
echo "   ~/Projects/04-Integrations/       - Third-party integrations"
echo "   ~/Projects/05-AI-Experiments/     - AI research"
echo "   ~/Projects/99-Legacy/             - Archived projects"
echo ""
echo -e "${YELLOW}🔄 Next Steps:${NC}"
echo "   1. Open GitHub Desktop"
echo "   2. File → Add Local Repository"
echo "   3. Add: ~/Projects/00-Premium-Gastro/premium-gastro-ai-assistant"
echo "   4. Repeat for other active repos"
echo ""
echo -e "${YELLOW}💡 Recommended Shell Aliases (add to ~/.zshrc):${NC}"
echo "   alias pgai='cd ~/Projects/00-Premium-Gastro/premium-gastro-ai-assistant'"
echo "   alias pgscreen='cd ~/Projects/00-Premium-Gastro/premium-gastro-screensaver'"
echo "   alias mcp='cd ~/Projects/02-MCP-Servers'"
echo "   alias projects='cd ~/Projects'"
echo ""
echo -e "${YELLOW}📝 Backup File:${NC}"
echo "   $BACKUP_FILE"
echo "   (List of original repo locations - keep for reference)"
echo ""
