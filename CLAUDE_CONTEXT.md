# Claude Context Management

## Overview

This project uses `claude.md` to maintain context across Claude Code sessions.

## What is claude.md?

`claude.md` is a comprehensive context file that contains:
- Project overview and architecture
- Tech stack and dependencies
- Database schema
- Skills and assistants system
- Admin dashboard details
- Deployment methods
- Recent changes and current state
- Known issues and solutions
- Common tasks and workflows

## Why use it?

When you start a new Claude Code session:
1. Claude can read `claude.md` to understand the entire project instantly
2. No need to re-explain architecture, tech stack, or recent work
3. Claude can pick up exactly where you left off
4. Prevents repeating solved problems

## Workflow

### Before Starting a New Session

**You (Human)**:
- Update `claude.md` with any changes you made
- Document new features, fixes, or decisions
- Add to "Recent Changes" section

### Starting a New Session

**Claude**:
- Reads `claude.md` first thing
- Understands project state immediately
- Continues work seamlessly

### During Development

**Both**:
- Update `claude.md` as you go
- Document decisions, issues, solutions
- Keep "Current State" section up to date

### Before Committing

**Git Hook Reminder**:
- Pre-commit hook will remind you to update `claude.md`
- Shows checklist of things to verify
- Gives you 5 seconds to cancel if you forgot something

## File Status

**⚠️ IMPORTANT**: `claude.md` is in `.gitignore`

**Why?**
- Contains project-specific context
- May include internal notes
- Updates frequently during development
- Not meant for other developers (use README.md for that)

**What this means**:
- ✅ Update it freely without cluttering git history
- ✅ Keep it detailed and comprehensive
- ❌ Don't commit it to the repository
- ❌ Don't share sensitive info in it (though it's ignored)

## Pre-Commit Hook

Location: `.git/hooks/pre-commit`

**What it does**:
- Runs before every `git commit`
- Shows a checklist reminder
- Prompts you to update `claude.md`
- Gives you 5 seconds to cancel and make updates

**Example**:
```
🤖 PRE-COMMIT CHECKLIST
=======================

Have you updated claude.md with your latest changes?

[ ] Updated claude.md file
[ ] Tests pass (python scripts/run_tests.py)
[ ] No sensitive data in code
[ ] Documentation updated if needed

If you haven't updated claude.md, press Ctrl+C to cancel this commit.
Otherwise, press Enter to continue...

Press Enter to continue (5 seconds)...
```

## How to Use

### Starting a New Claude Session

```markdown
**Your prompt**:
"I'm continuing work on the VAPI skills system. Please read claude.md first."

**Claude**:
- Reads claude.md
- Understands entire project
- Ready to help immediately
```

### Updating claude.md

**During your session**:
1. Make changes to code
2. Update relevant sections in `claude.md`
3. Add notes to "Recent Changes" section
4. Update "Current State" if needed

**Before committing**:
1. Review your changes
2. Open `claude.md`
3. Update all relevant sections
4. Ensure "Recent Changes" is accurate
5. Update "Last Updated" timestamp
6. Save and close
7. Now you can commit

### What to Update in claude.md

**Always update**:
- "Last Updated" timestamp
- "Recent Changes" section
- "Current State" if features changed

**Update when relevant**:
- Architecture diagrams if structure changed
- Database schema if tables/columns changed
- Skills list if you added/removed skills
- Deployment steps if process changed
- Known issues if you found/fixed bugs
- Common tasks if you added new workflows

**Example update**:
```markdown
## 🔥 Recent Changes (Last Session - 2025-11-13)
1. Added voice notes reporting interface
2. Fixed pagination bug in user list
3. Updated Railway deployment to use newer Python version
4. Added new "export" skill for CSV generation
```

## Best Practices

### ✅ Do

- Update `claude.md` at the end of each work session
- Be detailed - more context is better
- Include file paths and line numbers for references
- Document WHY decisions were made, not just WHAT changed
- Update "Known Issues" when you encounter bugs
- Add solved problems so they're not repeated

### ❌ Don't

- Commit `claude.md` to git (it's ignored anyway)
- Include actual secrets/keys (use "your-key-here" placeholders)
- Let it get stale (update frequently)
- Delete sections - add to them
- Use it as a scratch pad (keep it organized)

## Template for Updates

When updating, use this template for "Recent Changes":

```markdown
### 🔥 Recent Changes (Last Session - YYYY-MM-DD)
1. [Feature/Fix] Brief description
   - File: path/to/file.py:123-456
   - Why: Reason for the change
   - Impact: What it affects

2. [Another change] Description
   - File: path/to/file.py
   - Why: Reason
   - Impact: What it affects
```

## Integration with Development

### Your Daily Workflow

**Morning (Starting Work)**:
1. Open project in VSCode
2. Read `claude.md` to remember where you left off
3. Start Claude Code session: "Read claude.md and help me continue"

**During Development**:
1. Work on features
2. Make notes in `claude.md` as you go
3. Update sections when you make changes

**Evening (Ending Work)**:
1. Review your changes
2. Update `claude.md` comprehensively
3. Commit your code (hook will remind you)
4. Push to GitHub

### Example Session

```bash
# Start work
code /Users/kevinmorrell/projects/vapi-skills-system

# In Claude Code
"Read claude.md and help me add a new export feature to the admin dashboard"

# Claude reads claude.md
# Claude understands:
# - Admin uses HTMX + Alpine.js + DaisyUI
# - Backend is FastAPI with routes in app/admin/routes.py
# - Templates are in app/admin/templates/
# - No build process needed
# Claude can help immediately without explanations

# Work together with Claude
# Make changes...

# Before committing
# Update claude.md with new export feature details
# Add to "Recent Changes"
# Save

# Commit
git add .
git commit -m "Add export feature to admin"
# Hook runs, shows checklist
# Press Enter to continue

# Done!
```

## Troubleshooting

### Hook not running?

```bash
# Check if hook exists and is executable
ls -la .git/hooks/pre-commit

# If not executable:
chmod +x .git/hooks/pre-commit
```

### claude.md accidentally committed?

```bash
# Remove from git (but keep local file)
git rm --cached claude.md

# Make sure it's in .gitignore
echo "claude.md" >> .gitignore
echo "CLAUDE.md" >> .gitignore

# Commit the removal
git commit -m "Remove claude.md from git history"
```

### claude.md too large?

That's fine! It should be comprehensive. But if it's over 50KB:
- Consider splitting into sections
- Move very old "Recent Changes" to "Version History"
- Keep current and relevant info prominent

## Benefits

### For You (Human Developer)
- ✅ Quick memory refresh when resuming work
- ✅ Document decisions as you make them
- ✅ Track project evolution over time
- ✅ Onboard new team members faster

### For Claude (AI Assistant)
- ✅ Instant project understanding
- ✅ No repeated explanations needed
- ✅ Better suggestions based on existing patterns
- ✅ Remembers your preferences and conventions

### For Your Project
- ✅ Living documentation that stays up to date
- ✅ Historical record of changes and decisions
- ✅ Knowledge base for troubleshooting
- ✅ Reduces "what was I thinking?" moments

## Summary

**Simple rule**: Update `claude.md` before every commit!

The pre-commit hook will remind you, but make it a habit:

1. **Make changes** → Update code
2. **Document** → Update claude.md
3. **Commit** → Hook reminds you
4. **Push** → Deploy with confidence

This keeps your project context fresh and makes every Claude session productive from the start.

---

**Questions?** Just ask Claude: "How do I update claude.md?"
