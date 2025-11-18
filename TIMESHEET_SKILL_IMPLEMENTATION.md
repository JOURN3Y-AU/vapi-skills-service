# Timesheet Skill Implementation

## Overview

The Timesheet skill has been successfully implemented following your specifications. This skill allows users to verbally log their work hours at construction sites through a natural conversation with Jill.

## Implementation Summary

### Files Created

1. **Database Migration**
   - [migrations/003_create_timesheets.sql](migrations/003_create_timesheets.sql)
   - Creates `timesheets` table with RLS policies
   - Stores: site_id, user_id, work_date, start_time, end_time, hours_worked, work_description, plans_for_tomorrow

2. **Skill Implementation**
   - [app/skills/timesheet/skill.py](app/skills/timesheet/skill.py)
   - [app/skills/timesheet/endpoints.py](app/skills/timesheet/endpoints.py)
   - [app/skills/timesheet/__init__.py](app/skills/timesheet/__init__.py)

3. **Assistant Implementation**
   - [app/assistants/timesheet.py](app/assistants/timesheet.py)

4. **Setup Scripts**
   - [scripts/add_timesheet_skill.py](scripts/add_timesheet_skill.py)
   - [scripts/test_timesheet_flow.py](scripts/test_timesheet_flow.py)

### Files Modified

1. **Main Application** - [app/main.py](app/main.py:20-69)
   - Added TimesheetSkill and TimesheetAssistant imports
   - Registered skill and assistant with skill_registry

2. **Assistants Module** - [app/assistants/__init__.py](app/assistants/__init__.py:11)
   - Added TimesheetAssistant export

3. **Greeter Assistant** - [app/assistants/greeter.py](app/assistants/greeter.py:48-55)
   - Updated to include timesheet in skill routing

## Conversation Flow

The timesheet skill follows this natural conversation flow:

### 1. Authentication & Introduction
```
Jill: "Perfect! Let me help you log your time. Let's start with the first site
      you want to log time for. Don't worry if there's more than one site -
      we'll cover that off next. Which site did you work at today?"
```

### 2. Site Identification (Loop for each site)
```
User: "Ocean White House"
[Tool: identify_site_for_timesheet]
Jill: "Great! For Ocean White House..."
```

### 3. Collect Time Details
```
Jill: "What time did you start at Ocean White House?"
User: "7:30am"

Jill: "And what time did you finish there?"
User: "3:45pm"

Jill: "What did you do at Ocean White House today?"
User: "Installed roof trusses and completed framing on the northern wing"

Jill: "Are you planning to do anything at Ocean White House tomorrow?"
User: "Yes, start the roofing installation"
```

### 4. Save Entry
```
[Tool: save_timesheet_entry]
Jill: "Got it! I've logged 8.25 hours for that site."
```

### 5. Check for Additional Sites
```
Jill: "Did you work at any other sites today?"
User: "No, that's it"
```

### 6. Final Confirmation
```
Jill: "Perfect! Let me confirm what I have for you today, Monday the 10th:
      - Ocean White House: 8.25 hours (7:30am to 3:45pm) - Installed roof
        trusses and completed framing

      Is that all correct?"
User: "Yes"
```

### 7. Finalize
```
[Tool: confirm_and_save_all]
Jill: "Perfect! I've saved your timesheet for 1 site, totaling 8.25 hours.
      Have a great day!"
```

## Technical Details

### Tools Implemented

1. **identify_site_for_timesheet**
   - Matches user's site description to available sites
   - Uses OpenAI GPT-4o-mini for intelligent matching
   - Returns site_id and site_name

2. **save_timesheet_entry**
   - Saves individual timesheet entry
   - Automatically calculates hours worked
   - Stores in `timesheets` table
   - Uses Sydney timezone for date

3. **confirm_and_save_all**
   - Finalizes all entries for the call
   - Returns summary with total hours
   - Provides confirmation message

### Database Schema

```sql
CREATE TABLE timesheets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES entities(id),
    user_id UUID NOT NULL REFERENCES users(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    vapi_call_id TEXT,
    work_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hours_worked NUMERIC(5,2) NOT NULL,
    work_description TEXT,
    plans_for_tomorrow TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Key Features

1. **Time Parsing**
   - Handles colloquial formats: "7am", "7:30", "quarter to 9", "half past 7"
   - Converts to 24-hour format (HH:MM)
   - Automatically calculates hours worked

2. **Multi-Site Support**
   - Users can log time for multiple sites in one call
   - Each site is handled individually with complete details
   - All entries confirmed together at the end

3. **Sydney Timezone**
   - All dates use Sydney (Australia/Sydney) timezone
   - Jill mentions the date during conversation

4. **Site Matching**
   - AI-powered site identification
   - Handles partial names and descriptions
   - Falls back to listing available sites if unclear

5. **Session Context**
   - Retrieved via vapi_call_id from authentication logs
   - Ensures proper user/tenant isolation
   - All data properly scoped

## Setup Instructions

### 1. Run Database Migration

You need to run the migration on your Supabase database:

```bash
# Connect to Supabase and run:
migrations/003_create_timesheets.sql
```

Or use Supabase CLI:
```bash
supabase db push
```

### 2. Verify Skill Registration

The skill has already been added to the database for the test user (John Smith, +61412345678):

```bash
python scripts/add_timesheet_skill.py
```

Output should show:
```
✅ Created timesheet skill
✅ Added timesheet skill to user
John Smith has 3 enabled skill(s):
  • Site Progress Updates (site_updates)
  • voice_notes (voice_notes)
  • Timesheet (timesheet)
```

### 3. Start/Restart Server

The skill will be registered with VAPI on server startup:

```bash
# Local development
uvicorn app.main:app --reload

# You should see in logs:
# Registered 4 skills and 4 assistants
```

### 4. Test the Implementation

#### Option A: Manual Testing via Phone Call
1. Call your VAPI phone number from +61412345678
2. Jill will authenticate you
3. Say "timesheet" or "log my time"
4. Follow the conversation flow

#### Option B: Automated Testing
```bash
# Make sure server is running first
python scripts/test_timesheet_flow.py
```

This will test:
- Authentication
- Site identification
- Saving timesheet entry
- Confirmation

## Integration with Greeter

The Greeter assistant has been updated to include timesheet routing:

**Single Skill Examples:**
- "Hi Kevin, it's Jill! Ready to log your timesheet?"

**Multiple Skills Examples:**
- "Hi Kevin, it's Jill! I can help with voice notes or timesheets - what would you like to do?"
- "Hi Kevin, it's Jill! I can help with voice notes, site updates, or timesheets - what would you like to do?"

## VAPI Squad Configuration

When you setup/update your squad in VAPI, you'll need to include the timesheet assistant:

```json
{
  "name": "JSMB-Jill-multi-skill-squad",
  "members": [
    {
      "assistant": "greeter_assistant_id",
      "assistantDestinations": [
        {
          "type": "assistant",
          "assistantName": "JSMB-Jill-voice-notes",
          "message": "Perfect! Connecting you to voice notes..."
        },
        {
          "type": "assistant",
          "assistantName": "JSMB-Jill-site-progress",
          "message": "Perfect! Let's log that site update..."
        },
        {
          "type": "assistant",
          "assistantName": "JSMB-Jill-timesheet",
          "message": "Perfect! Let's log your timesheet..."
        }
      ]
    },
    {
      "assistant": "voice_notes_assistant_id"
    },
    {
      "assistant": "site_progress_assistant_id"
    },
    {
      "assistant": "timesheet_assistant_id"
    }
  ]
}
```

## Testing Checklist

- [ ] Database migration completed
- [ ] Server starts without errors
- [ ] Skill registered with VAPI (check logs)
- [ ] Test user has skill enabled
- [ ] Authentication works
- [ ] Site identification works
- [ ] Timesheet entry saves correctly
- [ ] Hours calculated correctly
- [ ] Multiple sites can be logged
- [ ] Confirmation flow works
- [ ] Data appears in Supabase `timesheets` table
- [ ] Greeter routes to timesheet correctly

## Troubleshooting

### Common Issues

1. **"Session not found" error**
   - Ensure authentication happens first
   - Check vapi_call_id is passed correctly

2. **Site not identified**
   - Check that sites exist in `entities` table
   - Verify site entity_type is "sites"
   - Ensure sites are active (is_active = true)

3. **Hours calculation wrong**
   - Time format must be HH:MM (e.g., "07:30", "15:45")
   - Script handles conversion from colloquial formats

4. **Skill not available**
   - Run `scripts/add_timesheet_skill.py`
   - Verify in `user_skills` table
   - Restart server to register skill

### Logs to Check

```bash
# Server logs should show:
Registered 4 skills and 4 assistants
Registered Timesheet routes with prefix:

# On authentication:
Authenticating phone: +61412345678
Available skills: [..., "timesheet"]

# On tool calls:
Identifying site for timesheet
Saving timesheet entry
Confirmed timesheet entries
```

## Next Steps

1. **Deploy to Production**
   - Run migration on production database
   - Enable skill for production users
   - Update VAPI squad configuration

2. **Add Reporting**
   - Create endpoint to view timesheets
   - Add daily/weekly summaries
   - Export functionality

3. **Enhance Features**
   - Edit recent entries
   - Copy yesterday's timesheet
   - Add break time tracking (if needed)

## Files Reference

| File | Purpose |
|------|---------|
| [migrations/003_create_timesheets.sql](migrations/003_create_timesheets.sql) | Database schema |
| [app/skills/timesheet/skill.py](app/skills/timesheet/skill.py) | Skill definition & tool creation |
| [app/skills/timesheet/endpoints.py](app/skills/timesheet/endpoints.py) | Webhook handlers (547 lines) |
| [app/assistants/timesheet.py](app/assistants/timesheet.py) | Conversation flow & personality |
| [app/main.py](app/main.py:55-69) | Skill registration |
| [scripts/add_timesheet_skill.py](scripts/add_timesheet_skill.py) | Database setup script |
| [scripts/test_timesheet_flow.py](scripts/test_timesheet_flow.py) | Testing script |

---

**Implementation completed:** November 10, 2025
**Status:** Ready for testing
**Test user:** John Smith (+61412345678)
