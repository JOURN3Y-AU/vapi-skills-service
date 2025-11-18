# Testing with Phone Numbers - Complete Guide

## Understanding the Phone Number Setup

### Production Phone Number

**VAPI Phone Number:** `+61238143920` (Australian number)
- Connected to: `JSMB-Jill-multi-skill-squad`
- When someone calls this number, VAPI:
  1. Answers the call
  2. Activates the squad (greeter assistant)
  3. Extracts caller's phone number from call metadata
  4. Passes it to `authenticate_caller` tool

### Test User Phone Number

**Test User:** John Smith
- **Phone:** `+61412345678`
- **Tenant:** Built by MK
- **Enabled Skills:** Voice Notes, Site Progress, Timesheet

This user is configured in your database and can call the production number.

---

## Three Ways to Test

### Method 1: Real Phone Call (End-to-End Test)

**Best for:** Final testing before production

```bash
# Prerequisites:
1. Database migration applied
2. Server deployed to Railway (or Cloudflare Tunnel running)
3. VAPI tools pointing to your server

# How to test:
1. Call +61238143920 from +61412345678
2. Jill authenticates you automatically
3. Say "timesheet" or "log my time"
4. Follow the conversation flow
```

**What happens:**
```
User calls → VAPI answers → Squad activates
→ Greeter authenticates (extracts +61412345678 from call)
→ Greeter routes to timesheet assistant
→ Conversation flows through tools
→ Data saves to Supabase
```

### Method 2: API Testing (Local Development)

**Best for:** Development and debugging endpoints

This is what your test script does - it **simulates** VAPI requests directly to your FastAPI endpoints.

```bash
# Start local server
uvicorn app.main:app --reload

# Run test script (in another terminal)
python scripts/test_timesheet_flow.py
```

**How it works:**

The script creates **fake VAPI requests** with the test phone number embedded:

```python
auth_request = {
    "message": {
        "call": {
            "id": TEST_VAPI_CALL_ID,
            "customer": {
                "number": "+61412345678"  # Test phone injected here
            }
        },
        "toolCalls": [{...}]
    }
}
```

This hits your local endpoints directly:
- `POST http://localhost:8000/api/v1/vapi/authenticate-by-phone`
- `POST http://localhost:8000/api/v1/skills/timesheet/identify-site`
- `POST http://localhost:8000/api/v1/skills/timesheet/save-entry`

**Advantages:**
- ✅ No need to make phone calls
- ✅ Test locally without VAPI
- ✅ See detailed request/response logs
- ✅ Fast iteration

**Limitations:**
- ⚠️ Doesn't test voice interaction
- ⚠️ Doesn't test VAPI → server integration
- ⚠️ Doesn't test assistant prompts/routing

### Method 3: Test Mode Fallback (When Phone Missing)

The authentication endpoint has a **test mode fallback**:

```python
# From app/skills/authentication/endpoints.py

if not caller_phone or caller_phone.strip() == "":
    # Use TEST_DEFAULT_PHONE from .env
    test_phone = os.getenv("TEST_DEFAULT_PHONE")
    if test_phone:
        caller_phone = test_phone
        logger.info(f"Using test default: {caller_phone}")
```

**Your .env already has this:**
```bash
TEST_DEFAULT_PHONE=+61412345678
```

This means if a request comes in **without** a phone number, it uses the test user.

---

## Current Configuration

### Your .env File

```bash
# Test user for local development
TEST_DEFAULT_PHONE=+61412345678

# Environment
ENVIRONMENT=development

# Webhook URLs
DEV_WEBHOOK_BASE_URL=https://predictions-colony-fairy-camp.trycloudflare.com
WEBHOOK_BASE_URL=https://predictions-colony-fairy-camp.trycloudflare.com
```

### VAPI Configuration

**Phone Number:** `+61238143920`
- → Squad: `JSMB-Jill-multi-skill-squad` (`30016c3e-f038-4c18-9b33-5717be011eac`)
- → Greeter: `JSMB-Jill-authenticate-and-greet` (`4300f282-35d2-4a06-9a67-f5b6d45e167f`)

**Squad Members:**
1. Greeter (with routes to all skills)
2. Voice Notes Assistant
3. Site Progress Assistant
4. **Timesheet Assistant** ✅

**Tools Webhook URLs:**
Currently pointing to: `https://predictions-colony-fairy-camp.trycloudflare.com/api/v1/skills/timesheet/*`

---

## Testing Workflow - Step by Step

### Local Development Testing

#### Step 1: Apply Database Migration

```sql
-- Run in Supabase SQL Editor
-- migrations/003_create_timesheets.sql
```

#### Step 2: Start Local Server

Terminal 1:
```bash
cd /Users/kevinmorrell/projects/vapi-skills-system
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Look for:
```
INFO:     Registered 4 skills and 4 assistants
INFO:     Registered Timesheet routes with prefix:
```

#### Step 3: Start Cloudflare Tunnel (Optional - for phone testing)

Terminal 2:
```bash
cloudflared tunnel run vapi-local
```

Or:
```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the URL (e.g., `https://abc-123.trycloudflare.com`)

#### Step 4A: Test with Script (No Phone Call)

Terminal 3:
```bash
python scripts/test_timesheet_flow.py
```

This will:
```
1️⃣  AUTHENTICATION
   Status: 200
   ✅ Authenticated: John Smith
   Available sites: 2

2️⃣  SITE IDENTIFICATION
   Status: 200
   ✅ Site identified: Ocean White House
   Site ID: [uuid]

3️⃣  SAVE TIMESHEET ENTRY
   Status: 200
   ✅ Entry saved
   Entry ID: [uuid]
   Hours worked: 8.25

4️⃣  CONFIRM ALL ENTRIES
   Status: 200
   ✅ Confirmed
   Total entries: 1
   Total hours: 8.25

✅ TIMESHEET FLOW TEST COMPLETED SUCCESSFULLY
```

Check Supabase `timesheets` table for the new entry.

#### Step 4B: Test with Phone Call (Full E2E)

```
1. Make sure Cloudflare Tunnel is running
2. Your tools in VAPI point to the tunnel URL
3. Call +61238143920 from +61412345678
4. Follow the conversation
5. Check Supabase for the data
```

---

## Troubleshooting

### Issue: "Phone number not found or not authorized"

**Cause:** The phone number isn't in your database or isn't active.

**Solution:**
```sql
-- Check if user exists
SELECT * FROM users WHERE phone_number = '+61412345678';

-- If not, add them:
INSERT INTO users (id, tenant_id, name, phone_number, is_active)
VALUES (
  gen_random_uuid(),
  '[tenant_id]',
  'John Smith',
  '+61412345678',
  true
);

-- Enable timesheet skill
INSERT INTO user_skills (user_id, skill_id, is_enabled)
SELECT u.id, s.id, true
FROM users u, skills s
WHERE u.phone_number = '+61412345678'
  AND s.skill_key = 'timesheet';
```

### Issue: "Session not found"

**Cause:** Authentication didn't run first, or vapi_call_id is wrong.

**Solution:**
- Ensure authentication endpoint is called first
- Check that `vapi_call_id` is consistent across all requests in the same flow
- Look for the authentication log in `vapi_logs` table

### Issue: Test script can't connect to server

**Cause:** Server not running or wrong port.

**Solution:**
```bash
# Check if server is running
lsof -i :8000

# If not, start it
uvicorn app.main:app --reload --port 8000

# Update BASE_URL in test script if needed
```

### Issue: Real phone call doesn't authenticate

**Cause:** VAPI tools pointing to wrong URL, or Cloudflare Tunnel not running.

**Solution:**
1. Check tunnel is running: `cloudflared tunnel run vapi-local`
2. Check tunnel URL matches tool URLs in VAPI
3. Check server logs for incoming requests
4. Test webhook URL manually: `curl https://your-tunnel.trycloudflare.com/health`

### Issue: Tools returning 404

**Cause:** Routes not registered or wrong URL.

**Solution:**
```bash
# Check server logs for route registration
INFO:     Registered Timesheet routes with prefix:

# Test endpoints manually
curl -X POST http://localhost:8000/api/v1/vapi/authenticate-by-phone \
  -H "Content-Type: application/json" \
  -d '{"message": {"call": {"id": "test", "customer": {"number": "+61412345678"}}, "toolCalls": [{"id": "test", "function": {"name": "authenticate_caller", "arguments": {}}}]}}'
```

---

## Adding More Test Users

If you want to test with different phone numbers:

### Option 1: Add to Database

```sql
-- Add new user
INSERT INTO users (id, tenant_id, name, phone_number, is_active)
VALUES (
  gen_random_uuid(),
  '[your_tenant_id]',
  'Jane Doe',
  '+61400000000',  -- Different number
  true
);

-- Enable skills for new user
INSERT INTO user_skills (user_id, skill_id, is_enabled)
SELECT u.id, s.id, true
FROM users u
CROSS JOIN skills s
WHERE u.phone_number = '+61400000000'
  AND s.skill_key IN ('voice_notes', 'site_updates', 'timesheet');
```

### Option 2: Update Test Script

Edit `scripts/test_timesheet_flow.py`:

```python
# Line 59 - change test number
"customer": {
    "number": "+61400000000"  # Your new test number
}
```

---

## Phone Number Format

VAPI uses **E.164 format**:
- ✅ Correct: `+61412345678` (country code + number)
- ❌ Wrong: `0412345678` (missing country code)
- ❌ Wrong: `+61 412 345 678` (spaces)
- ❌ Wrong: `+61-412-345-678` (hyphens)

Always use: `+[country code][number]` with no spaces or punctuation.

---

## Testing Checklist

### Before Testing
- [ ] Database migration applied
- [ ] Test user exists in database (`+61412345678`)
- [ ] Test user has timesheet skill enabled
- [ ] Local server running (`uvicorn app.main:app --reload`)
- [ ] Cloudflare Tunnel running (for phone calls only)

### API Testing (Script)
- [ ] Run `python scripts/test_timesheet_flow.py`
- [ ] All steps pass (✅)
- [ ] Check Supabase `timesheets` table
- [ ] Verify data is correct

### Phone Call Testing
- [ ] Call +61238143920 from +61412345678
- [ ] Greeter authenticates automatically
- [ ] Say "timesheet"
- [ ] Transfer to timesheet assistant works
- [ ] Complete the conversation
- [ ] Data saves to Supabase

### Production Testing
- [ ] Deploy to Railway (`git push origin main`)
- [ ] Update tool URLs to Railway (optional)
- [ ] Call from production number
- [ ] Verify in production database

---

## Summary

You have **three testing methods**:

1. **API Testing** (fastest, for development)
   - Uses test script
   - Simulates VAPI requests
   - Tests endpoints directly
   - Phone: `+61412345678` (hardcoded in script)

2. **Local Phone Testing** (full integration)
   - Real call to VAPI number
   - Through Cloudflare Tunnel
   - Tests complete flow
   - Phone: Call from `+61412345678`

3. **Production Testing** (final validation)
   - Real call to VAPI number
   - Through Railway deployment
   - Tests production setup
   - Phone: Any enabled user

**Your test user:** `+61412345678` (John Smith)
**VAPI number:** `+61238143920`
**Test mode fallback:** Configured in `.env`

Start with API testing (script), then do phone testing once that works!
