# Admin Interface - Quick Start Guide

## 🚀 What We Built

A **lightweight admin dashboard** for your VAPI Skills System that runs inside your existing FastAPI application. No separate frontend build, no separate deployment!

## 📍 Access

### Local Development
```bash
# Start your server
uvicorn app.main:app --reload

# Open in browser
http://localhost:8000/admin
```

### Production (Railway)
```
https://your-app.railway.app/admin
```

## 🔑 Login

1. Click **Login** button in top-right
2. Enter your tenant API key
3. You're in!

**Where to find your API key:**
- Supabase → Tables → `tenants` → `api_key` column
- Example: `bmk-dev-key-2024`

## 📊 Features Available Now

### ✅ Dashboard
- View stats: users, sites, voice notes, timesheets
- Quick navigation to other sections

### ✅ User Management
- See all users in your tenant
- View their assigned skills
- Activate/deactivate users

### ✅ Tenant Info
- View company details
- Copy API key

### 🚧 Coming Soon
- Site management (CRUD)
- Timesheet reports (filter, export)
- Voice notes reports (play, export)
- User creation/editing
- Role-based permissions

## 🏗️ Tech Stack

**Why these choices?**

| Technology | Why? |
|------------|------|
| **FastAPI + Jinja2** | Server-side rendering = fast, simple, no build process |
| **HTMX** | Dynamic updates without JavaScript frameworks |
| **Alpine.js** | Lightweight client-side interactivity (15kb) |
| **DaisyUI + Tailwind** | Beautiful components out-of-the-box |
| **All via CDN** | No npm, no webpack, no build step! |

## 📁 Project Structure

```
app/
├── admin/
│   ├── routes.py              # All backend logic
│   ├── templates/
│   │   ├── layouts/base.html  # Main layout
│   │   ├── dashboard/         # Dashboard pages
│   │   ├── users/             # User management
│   │   ├── tenants/           # Tenant info
│   │   └── reports/           # Reports (placeholder)
│   └── static/
│       └── css/custom.css     # Your custom styles
└── main.py                    # Admin router integrated here
```

## 🎯 Development Workflow

### Making Changes

**Edit a template:**
```bash
# 1. Open template file
code app/admin/templates/users/list.html

# 2. Make changes

# 3. Refresh browser - changes appear instantly!
```

**Add new page:**
```python
# 1. Create template
app/admin/templates/my-page.html

# 2. Add route in routes.py
@router.get("/admin/my-page")
async def my_page(request: Request):
    return templates.TemplateResponse("my-page.html", {"request": request})

# 3. Add link in base.html sidebar
<li><a href="/admin/my-page">My Page</a></li>
```

### No Build Process!

- Edit HTML → Refresh browser ✓
- Edit Python → Auto-reloads ✓
- Edit CSS → Refresh browser ✓

**That's it!**

## 🔐 Security

### Current Setup
- API key authentication
- Tenant isolation (users only see their tenant data)
- Keys stored in browser localStorage

### For Production
- [ ] Add HTTPS (required!)
- [ ] Implement role-based access control
- [ ] Add audit logging
- [ ] Consider JWT tokens with expiration
- [ ] Add rate limiting

## 🎨 Customization

### Change Theme
```html
<!-- In layouts/base.html -->
<html data-theme="dark">  <!-- or: light, cupcake, corporate, etc. -->
```

### Custom Colors
```css
/* In static/css/custom.css */
:root {
  --primary: #your-brand-color;
}
```

### Add Logo
```html
<!-- In layouts/base.html navbar -->
<img src="/static/images/logo.png" class="h-8">
```

## 📊 Architecture Decisions

### ✅ What This Is
- **Lightweight admin interface** for tenant/user management
- **Internal tool** for JOURN3Y staff and select client admins
- **Rapid development** - build features as you need them
- **Server-side rendered** - simple, fast, no complex frontend

### ❌ What This Is Not
- Public-facing application
- Replacement for your VAPI system
- Heavy data analytics platform (yet!)
- Mobile app (responsive web only)

## 🚀 Deployment

### Railway
**Good news:** Already deployed with your FastAPI app!

- ✅ Same Railway service
- ✅ Same environment variables
- ✅ No extra configuration needed

Just push to GitHub and it deploys automatically.

### Environment Variables
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your-key
```

That's all you need!

## 🎯 Next Steps

### Phase 1 (Now)
- [x] Basic dashboard
- [x] User management
- [x] Tenant info
- [x] Authentication

### Phase 2 (Next)
- [ ] Site management (CRUD)
- [ ] User creation/editing forms
- [ ] Basic reports (timesheet, voice notes)

### Phase 3 (Future)
- [ ] Advanced reporting with charts
- [ ] Export to CSV/Excel
- [ ] Role-based access control
- [ ] Audit logs
- [ ] Email notifications

### Phase 4 (Later)
- [ ] Mobile app (if needed)
- [ ] Advanced analytics
- [ ] Custom dashboards per user
- [ ] Integration with external tools

## 💡 Tips

### HTMX is Your Friend
```html
<!-- Instead of writing JavaScript for API calls -->
<button hx-post="/api/endpoint" hx-target="#result">
    Click Me
</button>
<div id="result"></div>

<!-- Server returns HTML, HTMX swaps it in -->
```

### Alpine.js for Simple Interactions
```html
<!-- Dropdown, modals, tabs - no framework needed -->
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open">Content</div>
</div>
```

### DaisyUI Components
Browse [daisyui.com/components](https://daisyui.com/components/) for ready-to-use components:
- Modals, alerts, cards, tables
- Forms, buttons, badges
- All styled and accessible

## 🐛 Troubleshooting

**Admin page shows 404?**
```python
# Check main.py has:
app.include_router(admin_router)
```

**Login fails?**
- Check API key is correct
- Verify SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
- Check browser console for errors

**Templates not updating?**
```bash
# Run with --reload flag
uvicorn app.main:app --reload
```

## 📚 Resources

- **Full Documentation**: `/app/admin/README.md`
- **HTMX Docs**: [htmx.org](https://htmx.org)
- **Alpine.js Docs**: [alpinejs.dev](https://alpinejs.dev)
- **DaisyUI Components**: [daisyui.com](https://daisyui.com)

## 🎉 You're Ready!

Your admin interface is set up and ready to grow with your needs. Start with what's there, add features as you need them.

**Questions?** Check the full README at `/app/admin/README.md`

---

Built with ❤️ using FastAPI, HTMX, Alpine.js, and DaisyUI
