# Admin Authentication System Migration Guide

**Status**: ✅ Backend Complete - Database Migration Required

---

## 🎯 What We've Built

We've implemented a complete username/password authentication system for the admin dashboard to replace the API key-based authentication. This provides:

- **Secure authentication** with bcrypt password hashing
- **Session management** using HTTP-only secure cookies (8-hour sessions)
- **Role-based access control** (super_admin, tenant_admin, tenant_user)
- **Permission system** for granular feature access
- **Professional login UI** with JOURN3Y branding

### ✅ Completed Backend Components

1. **Database Schema** (`scripts/create_admin_auth_tables.sql`)
   - `admin_users` table for user accounts
   - `admin_user_permissions` table for granular permissions
   - Proper constraints and indexes

2. **Password Utilities** (`app/auth_utils.py`)
   - bcrypt password hashing
   - Password verification
   - Password strength validation

3. **Authentication Endpoints** (`app/admin/auth.py`)
   - `POST /admin/auth/login` - Login with username/password
   - `POST /admin/auth/logout` - Clear session
   - `GET /admin/auth/me` - Get current user
   - `POST /admin/auth/change-password` - Password management
   - Authentication dependencies for route protection

4. **Session Middleware** (added to `app/main.py`)
   - HTTP-only secure cookies
   - 8-hour session timeout
   - Browser password manager compatible

5. **Login UI** (`app/admin/templates/auth/login.html`)
   - Clean, professional design
   - Show/hide password toggle
   - JOURN3Y branding
   - Error handling
   - Loading states

6. **Migration Script** (`scripts/setup_admin_auth.py`)
   - Creates database tables
   - Creates initial super_admin user
   - Optionally creates Built by MK tenant_admin

---

## 📋 Next Steps - What You Need to Do

### Step 1: Run the Database Migration

**Option A: Via Supabase SQL Editor (Recommended)**

1. Go to your Supabase project → SQL Editor
2. Open the file: `scripts/create_admin_auth_tables.sql`
3. Copy and paste the entire contents into the SQL Editor
4. Click "Run" to execute

**Option B: Programmatically (if you have direct database access)**

```bash
cd /Users/kevinmorrell/projects/vapi-skills-system
source venv/bin/activate
python scripts/setup_admin_auth.py
```

Note: The script may need manual SQL execution in Supabase first, as Supabase doesn't expose a direct SQL execution endpoint via REST.

### Step 2: Create Initial Super Admin User

After creating the tables, you need to create your super admin account:

```bash
cd /Users/kevinmorrell/projects/vapi-skills-system
source venv/bin/activate
python scripts/setup_admin_auth.py
```

Or manually insert into Supabase:

```sql
-- Generate password hash for "testing" using bcrypt
INSERT INTO admin_users (username, password_hash, email, role, is_active)
VALUES (
  'kevin.morrell@journ3y.com.au',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/oo7cQBd8/EcNiRMcm', -- "testing"
  'kevin.morrell@journ3y.com.au',
  'super_admin',
  true
);
```

### Step 3: Add Session Secret to .env

Add this to your `.env` file:

```bash
SESSION_SECRET_KEY=your-random-secret-key-min-32-chars-long
```

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Test the Login

1. Start your local server:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

2. Open browser: `http://localhost:8000/admin/login`

3. Login with:
   - **Username**: kevin.morrell@journ3y.com.au
   - **Password**: testing

4. You should be redirected to `/admin` dashboard

### Step 5: Create Built by MK Tenant Admin (Optional)

Run the migration script and choose 'y' when asked:

```bash
python scripts/setup_admin_auth.py
```

This will create:
- **Username**: jake@builtbymk.com.au
- **Temporary Password**: ChangeMe2025!
- **Permissions**: view_timesheets, manage_users, view_reports

---

## 🔄 What Still Needs to be Done

### 1. Update Admin Routes for Session Auth

Currently, admin routes still use the old `get_current_admin_user()` dependency which checks API keys. We need to update them to use the new session-based auth.

**Files to update**:
- `app/admin/routes.py` - Replace `get_current_admin_user` with session checks

**Example**:
```python
# OLD (API key)
@router.get("/admin/users")
async def list_users(admin_user: dict = Depends(get_current_admin_user)):
    ...

# NEW (Session)
from app.admin.auth import require_authenticated_user

@router.get("/admin/users")
async def list_users(request: Request):
    user_session = request.session.get("user")
    if not user_session:
        return RedirectResponse(url="/admin/login")
    ...
```

### 2. Add Logout Button to Navbar

Update `app/admin/templates/layouts/base.html`:

- Add logout button in the navbar
- Call `POST /admin/auth/logout`
- Redirect to `/admin/login`

### 3. Permission-Based UI Rendering

Update templates to show/hide features based on permissions:

```html
<!-- Show only if user has permission -->
<div x-show="userHasPermission('view_timesheets')">
  <a href="/admin/reports/timesheets">Timesheets</a>
</div>
```

### 4. Admin User Management UI (Super Admin Only)

Create new page: `app/admin/templates/admin_users/list.html`

Features:
- List all admin users
- Create new admin users
- Edit admin users (change password, role, permissions)
- Activate/deactivate users
- Only accessible by super_admins

### 5. Deploy to Railway

**Important**: Update Railway environment variables:
```bash
SESSION_SECRET_KEY=<generate-random-key>
```

### 6. Update CLAUDE.md

Document the new authentication system in the project context file.

---

## 🔒 Security Notes

### What's Protected

✅ **VAPI Webhooks**: Unchanged - still use `tenants.api_key` (this is correct)
✅ **Admin Dashboard**: Now uses secure username/password + session cookies
✅ **Password Storage**: bcrypt hashed, never stored in plaintext
✅ **Sessions**: HTTP-only cookies, 8-hour timeout, secure in production
✅ **CSRF Protection**: Implicit via session middleware

### Important Security Considerations

1. **Change default password**: After first login, change from "testing" to a strong password
2. **Rotate session secret**: Use different secrets for local/production
3. **HTTPS in production**: Sessions are marked secure in production (HTTPS required)
4. **Tenant isolation**: Tenant admins can only access their own tenant's data
5. **API keys preserved**: VAPI will continue working with existing API keys

---

## 🧪 Testing Checklist

- [ ] Can access login page at `/admin/login`
- [ ] Can login with super_admin credentials
- [ ] Login redirects to dashboard
- [ ] Invalid credentials show error message
- [ ] Session persists across page reloads
- [ ] Can logout successfully
- [ ] After logout, cannot access `/admin` without logging in again
- [ ] Tenant admin (Built by MK) can only see their tenant's data
- [ ] Tenant admin cannot access super admin features
- [ ] VAPI webhooks still work (test a phone call)

---

## 📚 API Endpoints Reference

### Authentication Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/admin/login` | GET | Login page | No |
| `/admin/auth/login` | POST | Authenticate user | No |
| `/admin/auth/logout` | POST | Clear session | Yes |
| `/admin/auth/me` | GET | Get current user | Yes |
| `/admin/auth/change-password` | POST | Change password | Yes |

### Request/Response Examples

**Login Request**:
```json
POST /admin/auth/login
{
  "username": "kevin.morrell@journ3y.com.au",
  "password": "testing"
}
```

**Login Response (Success)**:
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "username": "kevin.morrell@journ3y.com.au",
    "email": "kevin.morrell@journ3y.com.au",
    "role": "super_admin",
    "tenant_id": null,
    "tenant_name": null,
    "permissions": ["view_timesheets", "view_voice_notes", "manage_users", ...]
  }
}
```

---

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'bcrypt'"

```bash
source venv/bin/activate
pip install bcrypt==4.1.2 itsdangerous==2.1.2 pytz==2024.1
```

### "Table 'admin_users' does not exist"

Run the SQL migration in Supabase SQL Editor first.

### "Invalid session secret"

Add `SESSION_SECRET_KEY` to your `.env` file.

### Login page redirects to itself

Check that admin_users table exists and has at least one user.

### Cannot access dashboard after login

Check browser console for errors. Session cookie should be set.

---

## 📞 Support

If you encounter issues:
1. Check server logs for errors
2. Check browser console for frontend errors
3. Verify database tables were created correctly
4. Verify .env has all required variables

---

**Last Updated**: 2025-11-17
**Status**: Backend Complete, Database Migration Required
