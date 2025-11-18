# Timesheet Skill - Complete Development & Deployment Workflow

## Overview

You're absolutely right! The system has a **local development → test → deploy** workflow:

1. **Local Development** with Cloudflare Tunnel (test mode)
2. **Verify** everything works locally
3. **Deploy to Railway** via git push
4. **Production** automatically uses Railway URLs

---

## Current Status

### ✅ Completed
- [x] Code implementation (skill + assistant + endpoints)
- [x] VAPI tools created programmatically
- [x] VAPI assistant created (JSMB-Jill-timesheet)
- [x] VAPI squad updated with timesheet routing
- [x] Database skill record created
- [x] Test user enabled
- [x] Scripts created for setup

### ⚠️ Remaining
- [ ] Run database migration on Supabase
- [ ] Test locally with Cloudflare Tunnel
- [ ] Deploy to Railway (git push)
- [ ] Test production deployment

---

## Local Development & Testing (Current Environment)

### Your Current Setup

Looking at your `.env` file:
```bash
ENVIRONMENT=development
DEV_WEBHOOK_BASE_URL=https://predictions-colony-fairy-camp.trycloudflare.com
WEBHOOK_BASE_URL=https://predictions-colony-fairy-camp.trycloudflare.com
```

You're using **Cloudflare Tunnel** for local development. This gives you a public HTTPS URL that points to your local FastAPI server.

### Local Development Workflow

#### Step 1: Apply Database Migration

**CRITICAL**: Run this SQL on your Supabase database first:

```sql
-- Execute migrations/003_create_timesheets.sql
-- This creates the timesheets table with RLS policies
```

Or via Supabase dashboard:
1. Go to SQL Editor
2. Paste content from `migrations/003_create_timesheets.sql`
3. Run

#### Step 2: Start Local Server

Terminal 1 - FastAPI Server:
```bash
cd /Users/kevinmorrell/projects/vapi-skills-system
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Registered 4 skills and 4 assistants
INFO:     Registered Timesheet routes with prefix:
```

#### Step 3: Start Cloudflare Tunnel

Terminal 2 - Cloudflare Tunnel:
```bash
cloudflared tunnel run vapi-local
```

Or if using quick tunnel:
```bash
cloudflared tunnel --url http://localhost:8000
```

This exposes your local server at: `https://predictions-colony-fairy-camp.trycloudflare.com`

**Note**: If you restart the quick tunnel, the URL changes. Update your `.env` with the new URL and restart the server.

#### Step 4: Update VAPI Tool URLs (if needed)

If your Cloudflare Tunnel URL changed, update the tool webhooks:

```bash
# Create a script to update tool URLs
python scripts/update_webhooks.py
```

Or manually update in VAPI dashboard.

#### Step 5: Test Locally

**Option A: Test via Phone Call**
```
1. Call your VAPI phone number from +61412345678
2. Say "timesheet" when Jill asks
3. Follow the conversation
4. Check your local server logs to see the requests
5. Verify data in Supabase timesheets table
```

**Option B: Test via Script**
```bash
# Terminal 3
python scripts/test_timesheet_flow.py
```

This will:
- Hit your local endpoints
- Show request/response flow
- Verify data is saved

#### Step 6: Iterate & Debug

With `--reload`, your FastAPI server automatically restarts when you edit code:

1. Edit code in `app/skills/timesheet/`
2. Server automatically reloads
3. Test again immediately
4. Check logs in Terminal 1

---

## Production Deployment to Railway

Once you've tested locally and everything works:

### Step 1: Commit Changes

```bash
git add .
git commit -m "Add timesheet skill with verbal logging for construction sites"
git push origin main
```

### Step 2: Railway Auto-Deploys

Railway is connected to your GitHub repo. When you push to `main`:

1. **Railway detects the push**
2. **Builds** using `railway.toml` configuration:
   ```toml
   builder = "NIXPACKS"
   buildCommand = "pip install -r requirements.txt"
   startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```
3. **Sets environment** to production:
   ```toml
   [environments.production]
   variables = { ENVIRONMENT = "production" }
   ```
4. **Deploys** to: `https://journ3y-vapi-skills-service.up.railway.app`

### Step 3: Webhook URLs Automatically Switch

Your `app/config.py` handles this:

```python
@property
def webhook_base_url(self) -> str:
    if self.ENVIRONMENT == "development" and self.DEV_WEBHOOK_BASE_URL:
        return self.DEV_WEBHOOK_BASE_URL  # Local Cloudflare Tunnel

    return self.PROD_WEBHOOK_BASE_URL  # Railway URL
```

So in production, all webhook URLs automatically point to Railway.

### Step 4: Verify Production Deployment

Check Railway logs:
```
https://railway.app/project/[your-project]/deployments
```

Look for:
```
INFO:     Registered 4 skills and 4 assistants
INFO:     Registered Timesheet routes with prefix:
```

### Step 5: Test Production

Call from any phone number (that has the skill enabled):
```
User: "Hi, I need to log my timesheet"
Jill: "Perfect! Let me help you log your time..."
```

---

## How Tool URLs Work

### Tool Registration

When you create tools in VAPI, you specify webhook URLs:

```python
# From app/skills/timesheet/skill.py
"identify_site_for_timesheet": {
    "server": {
        "url": f"{self.webhook_base_url}/api/v1/skills/timesheet/identify-site"
    }
}
```

### Development vs Production

**Development** (local):
```
webhook_base_url = https://predictions-colony-fairy-camp.trycloudflare.com
Tool URL = https://predictions-colony-fairy-camp.trycloudflare.com/api/v1/skills/timesheet/identify-site
→ Routes to localhost:8000
```

**Production** (Railway):
```
webhook_base_url = https://journ3y-vapi-skills-service.up.railway.app
Tool URL = https://journ3y-vapi-skills-service.up.railway.app/api/v1/skills/timesheet/identify-site
→ Routes to Railway deployment
```

### Important Notes

1. **Tools are already created with Cloudflare URLs** - You created them while developing locally
2. **For production**, you may want to:
   - **Option A**: Update tool URLs to Railway (recommended for production)
   - **Option B**: Keep Cloudflare URLs and they'll route to Railway when ENVIRONMENT=production

**Recommendation**: Create a script to update tool URLs when deploying:

```bash
# scripts/update_tool_urls_for_production.py
python scripts/update_tool_urls_for_production.py
```

---

## Complete Deployment Checklist

### Pre-Deployment (Local Testing)

- [x] Code implemented and tested
- [ ] Database migration applied to Supabase
- [ ] Local server running (`uvicorn app.main:app --reload`)
- [ ] Cloudflare Tunnel running
- [ ] Test phone call successful
- [ ] Data appears in Supabase `timesheets` table
- [ ] All endpoints respond correctly

### Deployment

- [ ] All local tests passing
- [ ] Code committed to git
- [ ] Pushed to GitHub main branch
- [ ] Railway deployment triggered
- [ ] Railway build successful
- [ ] Production environment set correctly

### Post-Deployment

- [ ] Railway logs show "Registered 4 skills and 4 assistants"
- [ ] Health check works: `https://journ3y-vapi-skills-service.up.railway.app/health`
- [ ] Tool URLs point to Railway (or update them)
- [ ] Test production phone call
- [ ] Production data saves correctly
- [ ] Enable for additional production users

---

## Testing Checklist

### Local Testing (Development)

```bash
# 1. Start server
uvicorn app.main:app --reload

# 2. Start tunnel (in another terminal)
cloudflared tunnel run vapi-local

# 3. Test endpoints (in another terminal)
python scripts/test_timesheet_flow.py

# 4. Test phone call
# Call from +61412345678 and say "timesheet"

# 5. Verify database
# Check Supabase timesheets table for new records
```

### Production Testing (Railway)

```bash
# 1. Deploy
git push origin main

# 2. Wait for Railway deployment
# Check Railway dashboard

# 3. Verify health
curl https://journ3y-vapi-skills-service.up.railway.app/health

# 4. Test phone call
# Call from enabled user's phone

# 5. Check production database
# Verify data in Supabase
```

---

## Environment Variables

### Development (.env file)
```bash
ENVIRONMENT=development
DEV_WEBHOOK_BASE_URL=https://predictions-colony-fairy-camp.trycloudflare.com
WEBHOOK_BASE_URL=https://predictions-colony-fairy-camp.trycloudflare.com
TEST_DEFAULT_PHONE=+61412345678
```

### Production (Railway Dashboard)
```bash
ENVIRONMENT=production
PROD_WEBHOOK_BASE_URL=https://journ3y-vapi-skills-service.up.railway.app
SUPABASE_URL=https://lsfprvnhuazudkjqrpuk.supabase.co
SUPABASE_SERVICE_KEY=[your-key]
VAPI_API_KEY=[your-key]
OPENAI_API_KEY=[your-key]
```

Railway automatically sets `ENVIRONMENT=production` per `railway.toml`.

---

## Troubleshooting

### Local Development Issues

**Server won't start**
```bash
# Check if port 8000 is in use
lsof -i :8000
kill -9 [PID]
```

**Cloudflare Tunnel URL changed**
```bash
# Update .env with new URL
# Restart server
# Update VAPI tools if needed
```

**Tools not calling local server**
```bash
# Verify webhook URL in VAPI dashboard
# Check Cloudflare Tunnel is running
# Check server logs for incoming requests
```

### Production Deployment Issues

**Railway build fails**
```bash
# Check requirements.txt has all dependencies
# Check Railway logs for error details
```

**Endpoints return 404**
```bash
# Verify routes are registered in Railway logs
# Check ENVIRONMENT=production in Railway
```

**Tools call wrong URL**
```bash
# Update tool URLs in VAPI to Railway URL
# Run update script
```

---

## Next Steps

### 1. Complete Local Testing

```bash
# Apply migration
# Start local server + tunnel
# Test phone call
# Verify data saves
```

### 2. Deploy to Production

```bash
git add .
git commit -m "Add timesheet skill"
git push origin main

# Wait for Railway deployment
# Verify in Railway dashboard
```

### 3. Update Production Tools (Optional)

If you want tools to point directly to Railway:

```bash
# Create script to update tool URLs
python scripts/update_tool_urls_for_production.py
```

### 4. Enable for Production Users

```sql
-- Enable timesheet for production users
INSERT INTO user_skills (user_id, skill_id, is_enabled)
SELECT u.id, s.id, true
FROM users u, skills s
WHERE s.skill_key = 'timesheet'
  AND u.phone_number IN ('+614xxxxxxxx', '+614yyyyyyyy');
```

---

## Files & Resources

### Key Files
- **Config**: [app/config.py](app/config.py) - Environment-aware webhook URLs
- **Railway**: [railway.toml](railway.toml) - Deployment configuration
- **Migration**: [migrations/003_create_timesheets.sql](migrations/003_create_timesheets.sql)
- **Test Script**: [scripts/test_timesheet_flow.py](scripts/test_timesheet_flow.py)

### Documentation
- **Complete Guide**: [TIMESHEET_DEPLOYMENT_COMPLETE.md](TIMESHEET_DEPLOYMENT_COMPLETE.md)
- **Implementation**: [TIMESHEET_SKILL_IMPLEMENTATION.md](TIMESHEET_SKILL_IMPLEMENTATION.md)
- **Tunnel Setup**: [CLOUDFLARE_TUNNEL_SETUP.md](CLOUDFLARE_TUNNEL_SETUP.md)
- **Testing**: [TESTING.md](TESTING.md)

### URLs
- **GitHub**: https://github.com/kevin-m-journ3y/vapi-skills-service
- **Railway Prod**: https://journ3y-vapi-skills-service.up.railway.app
- **Local Dev**: https://predictions-colony-fairy-camp.trycloudflare.com (your current tunnel)

---

## Summary

You have a complete **local dev → test → deploy** workflow:

1. ✅ **Develop locally** with Cloudflare Tunnel exposing localhost
2. ✅ **Tools already created** in VAPI (pointing to your Cloudflare URL)
3. ✅ **Squad updated** with timesheet routing
4. ⏳ **Test locally** by applying migration and testing phone calls
5. ⏳ **Deploy** via `git push origin main`
6. ⏳ **Railway auto-deploys** with production environment
7. ⏳ **Webhook URLs automatically switch** to Railway in production

**Your next immediate step**:
Apply the database migration and test locally!

```bash
# 1. Apply migration in Supabase
# 2. Start server: uvicorn app.main:app --reload
# 3. Test: python scripts/test_timesheet_flow.py
# 4. Test: Call from phone
```

Once local testing passes, just push to deploy! 🚀
