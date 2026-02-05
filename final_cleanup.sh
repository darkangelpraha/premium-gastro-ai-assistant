#!/bin/bash

# Final Professional Cleanup - Premium Gastro AI Assistant
# Moves remaining content and deletes old folder structure

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== FINAL PROFESSIONAL CLEANUP ===${NC}"
echo "This will move remaining files and delete old empty folders"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

cd ~/Projects

# Move remaining content from old folders
echo -e "${YELLOW}Moving remaining content...${NC}"

# AI_Agents - has PDFs
if [ -d "AI_Agents" ]; then
    echo "Moving AI_Agents contents..."
    find AI_Agents -type f -not -name ".DS_Store" -exec mv {} 05-AI-Experiments/ \;
fi

# Archive - has backup file
if [ -d "Archive" ]; then
    echo "Moving Archive contents..."
    mkdir -p 99-Legacy/archive-backups
    find Archive -type f -not -name ".DS_Store" -exec mv {} 99-Legacy/archive-backups/ \;
fi

# Archives - has backups folder
if [ -d "Archives" ]; then
    echo "Moving Archives contents..."
    [ -d "Archives/backups" ] && mv Archives/backups 99-Legacy/
    find Archives -type f -not -name ".DS_Store" -exec mv {} 99-Legacy/ \;
fi

# Business - has database
if [ -d "Business" ]; then
    echo "Moving Business contents..."
    find Business -type f -not -name ".DS_Store" -exec mv {} 03-Business-Tools/ \;
fi

# Data - has Manifests
if [ -d "Data" ]; then
    echo "Moving Data contents..."
    [ -d "Data/Manifests" ] && mv Data/Manifests 03-Business-Tools/
fi

# Dev_Tools - has CLI_Tools and other files
if [ -d "Dev_Tools" ]; then
    echo "Moving Dev_Tools contents..."
    find Dev_Tools -mindepth 1 -maxdepth 1 -not -name ".DS_Store" -exec mv {} 06-Development-Tools/ \;
fi

# Development - has bin folder
if [ -d "Development" ]; then
    echo "Moving Development contents..."
    [ -d "Development/bin" ] && mv Development/bin 06-Development-Tools/
    find Development -type f -not -name ".DS_Store" -exec mv {} 06-Development-Tools/ \;
fi

# Docker_Configs - has configs
if [ -d "Docker_Configs" ]; then
    echo "Moving Docker_Configs contents..."
    find Docker_Configs -mindepth 1 -maxdepth 1 -not -name ".DS_Store" -exec mv {} 03-Business-Tools/Docker_Configs/ \;
fi

# Documentation - has many PDFs
if [ -d "Documentation" ]; then
    echo "Moving Documentation contents..."
    mkdir -p 03-Business-Tools/Documentation
    find Documentation -type f -not -name ".DS_Store" -exec mv {} 03-Business-Tools/Documentation/ \;
fi

# Integrations - has database
if [ -d "Integrations" ]; then
    echo "Moving Integrations contents..."
    find Integrations -type f -not -name ".DS_Store" -exec mv {} 04-Integrations/ \;
fi

# Logs - has various logs
if [ -d "Logs" ]; then
    echo "Moving Logs contents..."
    mkdir -p 99-Legacy/logs
    find Logs -type f -exec mv {} 99-Legacy/logs/ \;
fi

# MCP - has error logs
if [ -d "MCP" ]; then
    echo "Moving MCP contents..."
    find MCP -type f -not -name ".DS_Store" -exec mv {} 02-MCP-Servers/ \;
fi

# Mem0 - has Python cache and files
if [ -d "Mem0" ]; then
    echo "Moving Mem0 contents..."
    mkdir -p 05-AI-Experiments/mem0
    find Mem0 -mindepth 1 -maxdepth 1 -not -name ".DS_Store" -exec mv {} 05-AI-Experiments/mem0/ \;
fi

# N8N - has n8n subfolder
if [ -d "N8N" ]; then
    echo "Moving N8N contents..."
    [ -d "N8N/n8n" ] && mv N8N/n8n 03-Business-Tools/N8N
    find N8N -type f -not -name ".DS_Store" -exec mv {} 03-Business-Tools/N8N/ \; 2>/dev/null || true
fi

# Pan-Talir - has server file
if [ -d "Pan-Talir" ]; then
    echo "Moving Pan-Talir contents..."
    find Pan-Talir -type f -not -name ".DS_Store" -exec mv {} 01-Pan-Talir/ \;
fi

# Personal - has Media folder
if [ -d "Personal" ]; then
    echo "Moving Personal contents..."
    mkdir -p 99-Legacy/personal
    [ -d "Personal/Media" ] && mv Personal/Media 99-Legacy/personal/
fi

# Premium-Gastro - has various Python scripts
if [ -d "Premium-Gastro" ]; then
    echo "Moving Premium-Gastro contents..."
    find Premium-Gastro -type f -not -name ".DS_Store" -exec mv {} 00-Premium-Gastro/ \;
fi

# Scripts - has many scripts
if [ -d "Scripts" ]; then
    echo "Moving Scripts contents..."
    mkdir -p 07-Scripts
    find Scripts -type f -not -name ".DS_Store" -exec mv {} 07-Scripts/ \;
fi

# Scripts2 - has ai subfolder
if [ -d "Scripts2" ]; then
    echo "Moving Scripts2 contents..."
    find Scripts2 -mindepth 1 -maxdepth 1 -not -name ".DS_Store" -exec mv {} 07-Scripts/ \;
fi

# RECOVERY_ATTEMPT - has audit.txt
if [ -d "RECOVERY_ATTEMPT" ]; then
    echo "Moving RECOVERY_ATTEMPT contents..."
    mkdir -p 99-Legacy/recovery
    find RECOVERY_ATTEMPT -type f -exec mv {} 99-Legacy/recovery/ \;
fi

# Unsorted - has certificates and other files
if [ -d "Unsorted" ]; then
    echo "Moving Unsorted contents..."
    mkdir -p 99-Legacy/unsorted
    find Unsorted -mindepth 1 -maxdepth 1 -not -name ".DS_Store" -exec mv {} 99-Legacy/unsorted/ \;
fi

# Web_Assets - has CSS/HTML
if [ -d "Web_Assets" ]; then
    echo "Moving Web_Assets contents..."
    mkdir -p 08-Design-Assets/web
    find Web_Assets -type f -not -name ".DS_Store" -exec mv {} 08-Design-Assets/web/ \;
fi

# Delete empty old folders
echo -e "${YELLOW}Deleting empty old folders...${NC}"
for dir in AI_Agents Archive Archives Business Data Dev_Tools Development Docker_Configs Documentation \
           Go_Projects Integrations Logs MCP Mem0 N8N Node_Projects Pan-Talir Personal Premium-Gastro \
           Python_Projects Scripts Scripts2 RECOVERY_ATTEMPT Unsorted Web_Assets; do
    if [ -d "$dir" ]; then
        # Remove .DS_Store files first
        find "$dir" -name ".DS_Store" -delete 2>/dev/null || true
        # Try to remove directory (will only work if empty)
        if [ -z "$(ls -A $dir)" ]; then
            rmdir "$dir" && echo -e "${GREEN}✓ Deleted empty: $dir${NC}"
        else
            echo -e "${RED}⚠ Not empty, kept: $dir${NC}"
            echo "  Contents:"
            ls -la "$dir" | head -5
        fi
    fi
done

# Clean up .DS_Store files throughout
echo -e "${YELLOW}Cleaning .DS_Store files...${NC}"
find ~/Projects -name ".DS_Store" -delete 2>/dev/null || true

# Clean up home directory clutter
echo -e "${YELLOW}Cleaning home directory...${NC}"
cd ~

# Move standalone files to appropriate locations
[ -f "repo_backup_20260203_182804.txt" ] && mv repo_backup_20260203_182804.txt ~/Projects/99-Legacy/
[ -f "premium-gastro-ai-assistant" ] && echo "Symlink exists (kept)"

echo -e "${GREEN}=== CLEANUP COMPLETE ===${NC}"
echo ""
echo "Summary:"
echo "  - Moved remaining files from old folders"
echo "  - Deleted empty old folder structure"
echo "  - Cleaned .DS_Store files"
echo "  - Moved backup file to 99-Legacy"
echo ""
echo "Run: ls -la ~/Projects/ to see clean structure"
