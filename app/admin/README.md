# JOURN3Y Admin Interface

A lightweight, server-side rendered admin dashboard for managing the VAPI Skills System using FastAPI + HTMX + Alpine.js + DaisyUI.

## 🎯 Overview

This admin interface provides a clean, modern UI for managing:
- **Dashboard**: Overview of users, sites, voice notes, and timesheet entries
- **Tenant Management**: View tenant information and API keys
- **User Management**: View, activate/deactivate users and their assigned skills
- **Site Management**: (Coming soon) Manage construction sites
- **Reports**: (Coming soon) View timesheet and voice note reports

## 🏗️ Architecture

```
app/admin/
├── __init__.py           # Admin router export
├── routes.py             # FastAPI routes and business logic
├── templates/            # Jinja2 HTML templates
│   ├── layouts/
│   │   └── base.html    # Base layout with nav, sidebar, auth
│   ├── dashboard/
│   │   ├── index.html   # Main dashboard with stats
│   │   └── sites.html   # Site management (placeholder)
│   ├── tenants/
│   │   └── list.html    # Tenant info and API key
│   ├── users/
│   │   └── list.html    # User management with actions
│   └── reports/
│       ├── timesheets.html     # Timesheet reports (placeholder)
│       └── voice_notes.html    # Voice notes reports (placeholder)
└── static/
    ├── css/
    │   └── custom.css   # Custom styles (minimal)
    ├── js/              # (Empty - using CDN for now)
    └── images/          # (Empty)
```

## 🔧 Tech Stack

### Server-Side
- **FastAPI**: Backend framework
- **Jinja2**: Template engine for server-side rendering
- **Python httpx**: Async HTTP client for Supabase API calls

### Frontend (CDN-based)
- **Tailwind CSS**: Utility-first CSS framework
- **DaisyUI v4.12.10**: Tailwind component library
- **HTMX v1.9.10**: HTML-over-the-wire for dynamic updates
- **Alpine.js v3.13.5**: Lightweight JavaScript for client-side interactivity

**Why CDN?** No build process required! Edit templates and see changes instantly with FastAPI's auto-reload.

## 🚀 Getting Started

### 1. Installation

The admin interface is already integrated into your FastAPI app. No additional dependencies needed!

### 2. Running Locally

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# Access the admin interface
open http://localhost:8000/admin
```

### 3. Authentication

The admin interface uses API key authentication:

1. Click **Login** in the top-right corner
2. Enter your tenant API key (found in Supabase `tenants` table)
3. The API key is stored in `localStorage` for subsequent requests

**Example API Key**: `bmk-dev-key-2024`

### 4. Testing with curl

```bash
# Test dashboard stats endpoint
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8000/admin/dashboard/stats

# Test users data endpoint
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8000/admin/users/data

# Test tenant data endpoint
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8000/admin/tenants/data
```

## 📋 Features

### ✅ Implemented

#### Dashboard
- Real-time stats: users, sites, voice notes, timesheet entries
- Quick action buttons
- Tenant name display
- Auto-refresh on login

#### User Management
- List all users for authenticated tenant
- View user details: name, phone, role, assigned skills
- Toggle user active/inactive status
- Skill badges showing enabled capabilities

#### Tenant Management
- View tenant details
- Display and copy API key
- Created date

### 🚧 Coming Soon

- **Site Management**: CRUD operations for construction sites
- **Timesheet Reports**: Filter, search, export timesheet data
- **Voice Notes Reports**: Play, filter, and export voice recordings
- **User Creation/Editing**: Add new users and edit existing ones
- **Role-Based Access Control**: Admin vs regular user permissions
- **Multi-tenant Admin**: Super-admin view across all tenants

## 🎨 Customization

### Styling

Edit `/app/admin/static/css/custom.css` to add custom styles:

```css
/* Example: Change primary color */
:root {
  --primary: #your-color;
}
```

Or configure DaisyUI themes in `base.html`:

```html
<html lang="en" data-theme="dark"> <!-- Change to dark theme -->
```

Available themes: light, dark, cupcake, bumblebee, emerald, corporate, synthwave, etc.

### Adding New Pages

1. **Create Template**: Add new HTML file in appropriate templates folder
2. **Add Route**: Add route handler in `routes.py`
3. **Update Navigation**: Add link in `layouts/base.html` sidebar

Example:

```python
# routes.py
@router.get("/admin/my-new-page", response_class=HTMLResponse)
async def my_new_page(request: Request):
    return templates.TemplateResponse(
        "my-folder/my-page.html",
        {"request": request, "page_title": "My New Page"}
    )
```

```html
<!-- layouts/base.html -->
<li>
    <a href="/admin/my-new-page">
        <!-- Icon SVG -->
        My New Page
    </a>
</li>
```

## 🔐 Security Considerations

### Current Implementation
- API key authentication via Bearer token
- Keys stored in browser `localStorage`
- All requests include Authorization header
- No role-based access control yet

### Recommendations for Production

1. **Add HTTPS**: Never use in production without HTTPS
2. **Implement RBAC**: Add role checking (admin, tenant_admin, user)
3. **Session Management**: Consider JWT tokens with expiration
4. **Audit Logging**: Log all admin actions
5. **Rate Limiting**: Add rate limiting to admin endpoints
6. **CSRF Protection**: Add CSRF tokens for state-changing operations

### Planned Security Enhancements

```python
# Future: Role-based access decorator
@require_role("admin")
async def sensitive_operation():
    pass

# Future: Tenant isolation check
@verify_tenant_access
async def get_tenant_data(tenant_id: str):
    pass
```

## 🎯 HTMX Patterns

The admin interface uses HTMX for dynamic updates without full page reloads:

### Example: Toggle User Status

```html
<!-- Button triggers POST request -->
<button
    hx-post="/admin/users/{user_id}/toggle-active"
    hx-swap="outerHTML"
    hx-target="#user-row-{user_id}"
>
    Toggle Status
</button>

<!-- Server returns updated HTML fragment -->
<tr id="user-row-{user_id}">
    <td>Updated content...</td>
</tr>
```

### Global HTMX Configuration

Auth headers are automatically added to all HTMX requests:

```javascript
// In base.html
document.body.addEventListener('htmx:configRequest', (event) => {
    const apiKey = localStorage.getItem('admin_api_key');
    if (apiKey) {
        event.detail.headers['Authorization'] = 'Bearer ' + apiKey;
    }
});
```

## 🐛 Troubleshooting

### "Not Found" on /admin

**Problem**: Admin routes not registered

**Solution**: Ensure `app.include_router(admin_router)` is in `main.py`

### "401 Unauthorized" on API calls

**Problem**: Invalid or missing API key

**Solution**:
1. Check API key in Supabase `tenants` table
2. Clear `localStorage` and re-login
3. Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` env vars

### Templates not updating

**Problem**: FastAPI not reloading templates

**Solution**: Run with `--reload` flag:
```bash
uvicorn app.main:app --reload
```

### Static files 404

**Problem**: Static files not mounted

**Solution**: Verify in `main.py`:
```python
app.mount("/static", StaticFiles(directory="app/admin/static"), name="static")
```

## 📦 Deployment

### Railway Deployment

The admin interface deploys automatically with your FastAPI app:

1. **No separate deployment needed** - it's part of the same FastAPI app
2. **Single Railway service** - no additional costs
3. **Same environment variables** - uses existing Supabase config

### Environment Variables Required

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
```

### Access in Production

```
https://your-app.railway.app/admin
```

## 🔄 Development Workflow

### Making Frontend Changes

1. Edit HTML templates in `app/admin/templates/`
2. Save file
3. Refresh browser (FastAPI auto-reloads templates)
4. No build process needed!

### Making Backend Changes

1. Edit routes in `app/admin/routes.py`
2. Save file
3. FastAPI auto-reloads (with `--reload` flag)
4. Test in browser

### Adding New Functionality

```bash
# 1. Create template
touch app/admin/templates/my-feature/page.html

# 2. Add route
# Edit app/admin/routes.py

# 3. Add nav link
# Edit app/admin/templates/layouts/base.html

# 4. Test
open http://localhost:8000/admin/my-feature
```

## 📚 Resources

- [HTMX Documentation](https://htmx.org/docs/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [DaisyUI Components](https://daisyui.com/components/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/)

## 🎉 Next Steps

1. **Test the interface**: Login and explore the dashboard
2. **Customize styling**: Update colors and branding in `custom.css`
3. **Add features**: Build out the placeholder pages (sites, reports)
4. **Implement RBAC**: Add role-based permissions
5. **Add user creation**: Build forms for adding/editing users
6. **Export functionality**: Add CSV/Excel exports for reports

---

**Questions?** This is a lightweight admin interface designed to grow with your needs. Start simple, add features as you need them!
