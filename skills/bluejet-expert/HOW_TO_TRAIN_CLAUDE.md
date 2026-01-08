# How to Train Claude to Master Bluejet

This guide shows you exactly how to teach Claude about your Bluejet app so it becomes your personal expert guide.

---

## 🎯 Overview

You have 3 options, from easiest to most comprehensive:

1. **Quick Start** (30 minutes) - Basic navigation help
2. **Standard Training** (2-4 hours) - Most common tasks covered
3. **Expert Training** (1 week, 30 min/day) - Complete mastery

**Recommended**: Start with Quick Start, then expand over time as you use Bluejet.

---

## 🚀 Option 1: Quick Start (30 Minutes)

### What You'll Do:
Fill in the bare minimum in `SKILL.md` to get immediate help.

### Steps:

1. **Open** `skills/bluejet-expert/SKILL.md` in a text editor

2. **Fill in these sections** (search for "[FILL IN"):
   - What Bluejet does for your business
   - Your top 3 most common tasks
   - Main menu structure (just the top level)
   - Support contact info

3. **Take 3 screenshots**:
   - Main dashboard/home screen
   - Your most-used feature screen
   - The menu/navigation bar

4. **Test it immediately**:
   - Go to Claude.ai
   - Paste your filled-in SKILL.md content
   - Say: "I'm trying to [do X] in Bluejet, here's a screenshot"
   - Upload a screenshot
   - See if Claude can help

### Time Investment: 30 minutes
### Result: Basic navigation help

---

## 📚 Option 2: Standard Training (2-4 Hours)

### What You'll Do:
Comprehensive documentation of your Bluejet workflows.

### Steps:

#### Session 1: Structure (30 min)
1. Open Bluejet in one window, SKILL.md in another
2. Document the complete menu structure:
   ```
   Main Menu Item 1
      └─ Submenu A
      └─ Submenu B
   Main Menu Item 2
      └─ Submenu C
      └─ Submenu D
   ```
3. Take screenshot of each main section

#### Session 2: Your Workflows (60-90 min)
For each of your common tasks:
1. **Do the task** while documenting each step
2. **Take screenshots** at key steps
3. **Note any tricks** or gotchas
4. **Document in SKILL.md** under "Common Tasks"

**Example workflow documentation:**
```markdown
### Task: Create New Order in Bluejet

**Frequency**: Daily
**Time Required**: 5 minutes

**Step-by-Step:**
1. Click "Orders" in left sidebar (blue icon)
2. Click "+ New Order" button (top right, green)
3. Fill in required fields:
   - Customer Name: [Type or select from dropdown]
   - Order Date: [Auto-fills to today, or click to change]
   - Products: [Click "Add Product" and search]
4. Add products:
   - Search by SKU or name
   - Select from results
   - Enter quantity
5. Review totals (bottom right panel)
6. Click "Save Order" (green button, bottom right)

**Success Check**:
- Order number appears (e.g., "ORD-2026-0123")
- Green success message at top
- Order appears in "Recent Orders" list

**Common Issues**:
- If customer not found: Click "Add New Customer" first
- If product out of stock: Red warning appears - consider alternative
- If total looks wrong: Check quantities and unit prices

**Pro Tips**:
💡 Use keyboard: Tab to move between fields, Enter to save
💡 Duplicate existing order: Find similar order, click "Duplicate"
💡 Bookmark frequent customers: Click star icon next to name
```

#### Session 3: Troubleshooting (30 min)
1. List the 5 most frustrating/confusing things about Bluejet
2. Document what usually goes wrong
3. Add solutions you've discovered
4. Add workarounds for known issues

#### Session 4: Test & Refine (30 min)
1. Load your updated skill in Claude
2. Test with real scenarios
3. Note what's missing or unclear
4. Update the skill document

### Time Investment: 2-4 hours (can spread over several days)
### Result: Comprehensive guide for daily tasks

---

## 🏆 Option 3: Expert Training (1 Week)

### What You'll Do:
Build a complete Bluejet knowledge base over time.

### Week Schedule:

**Day 1 (30 min)**: Complete Option 2 basics
**Day 2 (30 min)**: Document all menu items and their purposes
**Day 3 (30 min)**: Document 5 more workflows
**Day 4 (30 min)**: Create visual guide with annotated screenshots
**Day 5 (30 min)**: Document advanced features and power user tips
**Day 6 (30 min)**: Test everything, fill gaps
**Day 7 (30 min)**: Create quick reference cheat sheet

### Advanced Components:

#### Visual Documentation
1. Take screenshots of every main screen
2. Annotate them (use Preview, Paint, or Skitch):
   - Draw arrows to important buttons
   - Add text labels for sections
   - Highlight key elements
3. Save as: `bluejet-screenshot-[screen-name].png`
4. Reference in SKILL.md: "See screenshot: bluejet-dashboard.png"

#### Screen Recording
1. Use built-in screen recorder (Mac: Cmd+Shift+5, Windows: Win+G)
2. Record yourself doing complex workflows
3. Narrate as you go: "Now I'm clicking... I'm looking for..."
4. Share video with Claude for analysis
5. Claude can extract step-by-step instructions

#### Error Documentation
Keep a "Bluejet Issues Log":
```markdown
## Issue Log

### 2026-01-08: Error when saving order
- **What I did**: Tried to save order with 3 products
- **Error message**: "Validation failed: Invalid product code"
- **Cause**: Old product SKU no longer in system
- **Solution**: Updated product SKU from new catalog
- **Lesson**: Always verify product codes in Bluejet match current catalog
```

### Time Investment: 3.5 hours over 1 week
### Result: Expert-level knowledge base

---

## 📸 Screenshot Guide

### How to Take Effective Screenshots

**Mac**:
- Cmd+Shift+4 (select area)
- Cmd+Shift+3 (full screen)

**Windows**:
- Win+Shift+S (Snipping Tool)
- PrtScn (full screen)

**What to Capture**:
1. **Navigation/Menu Structure**
   - Full menu expanded
   - Top navigation bar
   - Sidebar (if applicable)

2. **Each Common Task Screen**
   - Before starting task
   - Mid-process (forms filled)
   - Success confirmation

3. **Important Buttons/Icons**
   - Zoom in on key UI elements
   - Capture tooltips (hover text)

4. **Error Messages**
   - Full error text
   - Context (what you were doing)

### How to Share Screenshots with Claude

**Method 1: Direct Upload** (Claude.ai)
- Drag and drop image into chat
- Claude can analyze and reference it

**Method 2: Describe Location**
- "Top right corner, blue button"
- "Left sidebar, under 'Orders' section"
- "Bottom panel, next to 'Save' button"

**Method 3: Annotate First**
- Add arrows and labels
- Number the steps
- Highlight important areas

---

## 🔄 Iterative Learning Process

### The Best Way to Train Claude on Bluejet:

**Learn as you go:**

1. **Today**: Fill in basic structure (30 min)
2. **Each time you use Bluejet**:
   - Notice what you had to figure out
   - Document it in SKILL.md (2 min)
   - Update the skill in Claude
3. **Weekly**: Review and organize (15 min)
4. **Monthly**: Clean up and optimize (30 min)

**Example Daily Update:**
```
Today I learned how to export invoices:
- Go to Reports → Invoices
- Select date range
- Click "Export" (top right)
- Choose format (PDF or Excel)
- File downloads automatically

Added to SKILL.md in 2 minutes!
```

### After 1 Month:
- Complete documentation of YOUR Bluejet usage
- Custom-tailored to YOUR workflows
- Constantly improving with real experience

---

## 💬 Interactive Training with Claude

### Advanced Technique: Use Claude to Help Document

**Start a Claude session:**
```
I'm going to teach you about Bluejet. I'll share screenshots and
describe what I'm doing. Help me create step-by-step documentation.

Here's what I'm doing: [describe task]
[Upload screenshot]

Can you help me write clear instructions for this?
```

**Claude will:**
1. Analyze your screenshot
2. Ask clarifying questions
3. Draft step-by-step instructions
4. Suggest what else to document
5. Help you format it properly

**You copy-paste Claude's output into SKILL.md!**

This makes documentation 10x faster!

---

## 📋 Quick Training Checklist

Use this to track your progress:

### Basic Training ✓
- [ ] Filled in "About Bluejet" section
- [ ] Documented top 3 tasks
- [ ] Took 3 key screenshots
- [ ] Tested with Claude once
- [ ] Got helpful response

### Standard Training ✓
- [ ] Complete menu structure documented
- [ ] 10 common tasks documented
- [ ] Troubleshooting section filled
- [ ] Screenshots for each task
- [ ] Tested with 5 real scenarios
- [ ] Updated based on feedback

### Expert Training ✓
- [ ] All sections completed
- [ ] Visual guides created
- [ ] Screen recordings made
- [ ] Advanced features documented
- [ ] Quick reference cheat sheet printed
- [ ] Team members can use it too

---

## 🎯 Quality Check

**Your skill is good when:**

✅ You can describe a task and Claude gives correct steps
✅ Screenshots are clear and labeled
✅ Common issues have solutions
✅ Someone else could learn Bluejet from your documentation
✅ You rarely need to look things up anymore

**Signs you need more work:**

❌ Claude gives generic advice not specific to Bluejet
❌ Steps are vague or incomplete
❌ Missing common tasks you do daily
❌ No troubleshooting help
❌ Screenshots missing or unclear

---

## 🚀 Advanced: API Integration (Optional)

**If Bluejet has an API**, you can integrate it with Claude:

1. **Get API documentation**
2. **Add to your SKILL.md**:
   ```markdown
   ## Bluejet API Integration

   Base URL: https://api.bluejet.com/v1
   Authentication: Bearer token

   Common Endpoints:
   - GET /orders - List orders
   - POST /orders - Create order
   - GET /customers - List customers
   ```

3. **Claude can help you**:
   - Write API calls
   - Automate tasks
   - Extract data
   - Build integrations

---

## 💡 Pro Tips

### Tip 1: Document Exceptions
Not just happy paths! Document:
- What happens when things go wrong
- Workarounds for known bugs
- Alternative methods
- Edge cases

### Tip 2: Use Real Examples
Instead of: "Enter customer name"
Better: "Enter customer name (e.g., 'Restaurant U Fleků' or 'Hotel Maximilian')"

### Tip 3: Update Immediately
When you discover something new in Bluejet:
- Add it to SKILL.md RIGHT AWAY
- Don't wait - you'll forget details
- Takes 2 minutes now vs 20 minutes later

### Tip 4: Test with Colleagues
- Have a team member try your documentation
- See where they get confused
- Update based on their questions

### Tip 5: Version Control
Since SKILL.md is in Git:
- Commit changes regularly
- Add meaningful commit messages
- Can roll back if needed
- Track evolution over time

---

## 📊 Expected Results

### After Basic Training (30 min):
- Claude can help with navigation
- Basic task guidance available
- Time saved: ~20% on Bluejet tasks

### After Standard Training (4 hours):
- Claude is your Bluejet expert
- Rarely need to fumble around
- Time saved: ~60% on Bluejet tasks

### After Expert Training (1 week):
- Complete mastery
- Can train others
- Build automations
- Time saved: ~80% on Bluejet tasks

**ROI**: Even 4 hours investment pays back in 1-2 weeks!

---

## 🎓 Remember

**The goal isn't perfection - it's progress!**

- Start small (30 min investment)
- Test immediately
- Improve over time
- Document as you learn

**Within a week**, you'll have a Bluejet expert assistant that knows YOUR specific setup and workflows.

---

## 🆘 Troubleshooting This Process

**"I don't have time for 4 hours of documentation"**
→ Do Quick Start (30 min), then 5 min/day as you use Bluejet

**"I'm not good at writing instructions"**
→ Use Claude to help! Share screenshots, Claude writes the steps

**"Bluejet changes frequently"**
→ Perfect! Update SKILL.md when you notice changes (2 min each)

**"I'm not technical"**
→ That's fine! This is just copy-pasting and filling in blanks

**"Can't take screenshots at work"**
→ Describe visually: "top right corner, blue button labeled 'Save'"

---

## ✅ Next Steps

**Right now** (5 minutes):
1. Open `skills/bluejet-expert/SKILL.md`
2. Fill in the "About Bluejet" section
3. List your top 3 tasks (just the names)

**Today** (30 minutes):
1. Complete Quick Start training
2. Test with Claude once

**This week** (when you use Bluejet):
1. Document each task as you do it
2. Take screenshots
3. Test with Claude
4. Celebrate your progress! 🎉

---

**You've got this!** In less time than you think, Claude will be your personal Bluejet expert. 🚀

---

**Questions?** Just ask Claude (me!) - I'm here to help you through this process!
