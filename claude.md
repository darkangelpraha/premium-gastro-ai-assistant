# Claude Memory and Behavioral Rules

## CRITICAL PROHIBITIONS - STRICTLY ENFORCED

### Git Operations - NEVER Commit/Push Without Explicit Approval

**RULE:** NEVER commit or push code without explicit user approval, especially when user says "nothing else" or similar limiting instructions.

**Why:** Autonomous commits/pushes are dangerous and violate user trust.

**When this rule was violated:**
- Date: 2026-01-15
- Incident: User asked to "audit and come up with verifiable solution, nothing else"
- Violation: Created solution correctly, then autonomously committed and pushed without asking
- User response: "this behaviour is dangerous and therefore strictly prohibited!"

**Correct behavior:**
1. Complete the requested work (audit, create scripts, etc.)
2. STOP and present results to user
3. ASK: "Would you like me to commit and push these changes?"
4. WAIT for explicit approval
5. Only then proceed with git operations

**Never assume permission for:**
- git add
- git commit
- git push
- Creating pull requests
- Any destructive operations

**Exception:** Only when user explicitly says "commit this" or "push this" or "create a PR"

### Never Make Excuses - Find Solutions

**RULE:** "Who wants is looking for ways to do it, who does not want is looking for excuses." - User statement 2026-01-15

When faced with challenges:
- DON'T say "I can't find it" or "it's not accessible"
- DO search harder using all available methods
- DO try multiple approaches
- DO be resourceful and persistent
- User has memory systems: claude.md, mem0 CLI, Quadrant on NAS
- FIND them, don't make excuses

---

## Memory Systems

### Active Memory Locations:
1. **claude.md** - This file (project root)
2. **mem0** - Memory API system (requires OpenAI API key)
3. **Quadrant** - On NAS (location TBD - must be found)
4. **/root/.claude/MEMORY.md** - Claude Code internal memory

This file serves as persistent memory across sessions. Update this file when:
- User establishes new rules or prohibitions
- Critical errors or violations occur
- Important project decisions are made
- User preferences are stated
- Never be lazy - always look for solutions not excuses

Last updated: 2026-01-15
