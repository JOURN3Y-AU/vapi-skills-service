# Super Admin Guide

## 🔐 Overview

The admin interface now supports **super-admin** access, allowing you to view and manage ALL tenants from a single interface.

## 🚀 How It Works

### Two Types of Access

**1. Tenant Admin (Regular)**
- Uses tenant's own API key from Supabase `tenants` table
- Can only see their own tenant's data
- Example: `bmk-dev-key-2024`

**2. Super Admin (JOURN3Y)**
- Uses special super-admin key from environment variable
- Can see ALL tenants
- Can switch between tenants
- Sees aggregate stats across all tenants

## 🔑 Setup Super Admin Key

### 1. Add to Environment Variables

**Local Development (.env):**
```bash
SUPER_ADMIN_API_KEY=journ3y-super-admin-2024
```

**Railway Production:**
1. Go to Railway dashboard
2. Select your service
3. Go to Variables tab
4. Add: `SUPER_ADMIN_API_KEY=your-secure-key-here`

**⚠️ Security:** Use a strong, unique key in production!

### 2. Login with Super Admin Key

1. Go to http://localhost:8000/admin (or your Railway URL)
2. Click "Login"
3. Enter your super admin key (e.g., `journ3y-super-admin-2024`)
4. You're now in super-admin mode!

## 🎛️ Super Admin Features

### Dashboard
When NOT viewing a specific tenant:
- **Stats show** aggregate across ALL tenants:
  - Total tenants
  - Total users
  - Total sites
  - Total voice notes
  - Total timesheet entries

### Tenant Switcher
- **Dropdown in navbar** labeled "View Tenant:"
- **"All Tenants"** option shows aggregate data
- **Select specific tenant** to view that tenant's data in detail

### Tenants Page
- **All Tenants** mode: Shows all tenants in system
- **Specific Tenant** mode: Shows details for selected tenant

### Users Page
- **All Tenants** mode: Shows all users from all tenants (with tenant name column)
- **Specific Tenant** mode: Shows users for that tenant only

## 📊 How Tenant Switching Works

### Technical Details

**Frontend (localStorage):**
```javascript
// Stored in browser
localStorage.setItem('selected_tenant_id', 'uuid-here');
```

**Backend (HTTP Header):**
```http
GET /admin/users/data
Authorization: Bearer journ3y-super-admin-2024
X-Tenant-ID: uuid-of-selected-tenant
```

**Authentication Flow:**
1. User logs in with super-admin key
2. Frontend loads list of all tenants
3. User selects tenant from dropdown
4. Selected tenant ID stored in localStorage
5. All API requests include `X-Tenant-ID` header
6. Backend filters data by that tenant

## 🎯 Use Cases

### Scenario 1: View All Tenants
**Goal:** See how many tenants and users are in the system

**Steps:**
1. Login with super-admin key
2. Leave dropdown on "All Tenants"
3. View dashboard stats
4. Go to Tenants page to see list

### Scenario 2: Help Specific Tenant
**Goal:** Debug an issue for "Built by MK" tenant

**Steps:**
1. Login with super-admin key
2. Select "Built by MK" from dropdown
3. View their users, sites, data
4. Make changes if needed

### Scenario 3: Compare Tenants
**Goal:** See which tenants are most active

**Steps:**
1. Login with super-admin key
2. Go to Tenants page (All Tenants mode)
3. See creation dates, API keys
4. Switch between tenants to compare activity

## 🔒 Security Best Practices

### Production Setup

**1. Strong Super Admin Key**
```bash
# BAD
SUPER_ADMIN_API_KEY=admin

# GOOD
SUPER_ADMIN_API_KEY=journ3y-prod-sa-xK8mP2nQ9vL4wE6rT1yU5zA
```

**2. Environment Variables Only**
- ✅ Store in Railway environment variables
- ✅ Store in .env (not committed to git)
- ❌ Never hardcode in code
- ❌ Never commit to repository

**3. Limit Access**
- Only give super-admin key to JOURN3Y team
- Rotate key periodically
- Log super-admin actions (future enhancement)

**4. Use HTTPS**
- Always use HTTPS in production
- Never send super-admin key over HTTP

### Future Enhancements

- [ ] Audit logging for super-admin actions
- [ ] IP whitelist for super-admin access
- [ ] Time-limited super-admin sessions
- [ ] Multi-factor authentication
- [ ] Role-based permissions (read-only super-admin)

## 🧪 Testing

### Test Super Admin Access

**1. Local Testing:**
```bash
# Add to .env
SUPER_ADMIN_API_KEY=test-super-admin

# Start server
uvicorn app.main:app --reload

# Open browser
open http://localhost:8000/admin

# Login with: test-super-admin
```

**2. Test Tenant Switching:**
```bash
# Get tenant IDs from Supabase
# Login as super admin
# Select different tenants from dropdown
# Verify data changes
```

### Test API Endpoints

**Get tenants list (super-admin only):**
```bash
curl -H "Authorization: Bearer your-super-admin-key" \
  http://localhost:8000/admin/api/tenants-list
```

**Get users for specific tenant:**
```bash
curl -H "Authorization: Bearer your-super-admin-key" \
  -H "X-Tenant-ID: tenant-uuid-here" \
  http://localhost:8000/admin/users/data
```

**Get all users (no tenant filter):**
```bash
curl -H "Authorization: Bearer your-super-admin-key" \
  http://localhost:8000/admin/users/data
```

## 💡 Tips

### For JOURN3Y Team

**1. Default View**
- Keep dropdown on "All Tenants" for overview
- Switch to specific tenant when debugging

**2. Quick Tenant Lookup**
- Tenants page shows all tenant names and IDs
- Copy tenant ID to share with team

**3. User Management**
- Can activate/deactivate users across all tenants
- See which tenant each user belongs to

### For Tenant Admins

**Regular tenant admins:**
- Cannot access super-admin features
- Only see their own tenant data
- Cannot switch tenants (dropdown won't appear)

## 🐛 Troubleshooting

### Tenant Switcher Not Showing
**Problem:** Dropdown doesn't appear after login

**Solutions:**
- Verify you're using super-admin key (not tenant key)
- Check browser console for errors
- Verify `SUPER_ADMIN_API_KEY` is set in environment

### "Unauthorized" Error
**Problem:** API returns 401 when switching tenants

**Solutions:**
- Super-admin key is incorrect
- Key not set in environment variables
- Clear localStorage and re-login

### Shows Wrong Tenant Data
**Problem:** Still seeing old tenant after switching

**Solutions:**
- Hard refresh browser (Cmd+Shift+R)
- Clear localStorage manually
- Check browser network tab for X-Tenant-ID header

## 📚 API Reference

### Super Admin Endpoints

**GET /admin/api/tenants-list**
- Returns list of all tenants
- Requires super-admin authentication
- Used by tenant switcher dropdown

**GET /admin/dashboard/stats**
- With X-Tenant-ID: Returns stats for that tenant
- Without X-Tenant-ID: Returns aggregate stats

**GET /admin/tenants/data**
- With X-Tenant-ID: Returns that tenant only
- Without X-Tenant-ID: Returns all tenants

**GET /admin/users/data**
- With X-Tenant-ID: Returns users for that tenant
- Without X-Tenant-ID: Returns all users (with tenant column)

### Headers

**Authorization** (required)
```
Authorization: Bearer your-super-admin-key
```

**X-Tenant-ID** (optional, super-admin only)
```
X-Tenant-ID: uuid-of-tenant-to-view
```

---

## 🎉 Summary

You now have full super-admin capabilities:
- ✅ View all tenants
- ✅ Switch between tenants
- ✅ Aggregate statistics
- ✅ Secure key-based authentication
- ✅ Easy tenant management

**Next Steps:**
1. Set `SUPER_ADMIN_API_KEY` in your environment
2. Login with super-admin key
3. Explore tenant switcher
4. Manage your tenants!
