-- ============================================
-- ADMIN AUTHENTICATION SYSTEM
-- Database Migration Script
-- ============================================
-- Purpose: Create tables for username/password authentication for admin dashboard
-- Date: 2025-01-17
-- IMPORTANT: This does NOT affect VAPI authentication (tenants.api_key remains unchanged)

-- ============================================
-- TABLE: admin_users
-- ============================================
-- Stores admin user accounts for dashboard access
-- Separate from 'users' table which stores VAPI call users

CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,  -- Email address used as username
    password_hash TEXT NOT NULL,     -- bcrypt hashed password
    email TEXT UNIQUE NOT NULL,      -- Same as username for simplicity
    role TEXT NOT NULL CHECK (role IN ('super_admin', 'tenant_admin', 'tenant_user')),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,  -- NULL for super_admins
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT admin_users_tenant_check CHECK (
        (role = 'super_admin' AND tenant_id IS NULL) OR
        (role IN ('tenant_admin', 'tenant_user') AND tenant_id IS NOT NULL)
    )
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_tenant_id ON admin_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_admin_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_admin_users_updated_at
    BEFORE UPDATE ON admin_users
    FOR EACH ROW
    EXECUTE FUNCTION update_admin_users_updated_at();

-- ============================================
-- TABLE: admin_user_permissions
-- ============================================
-- Stores granular permissions for tenant_admin users
-- Super admins have all permissions by default (no rows needed)

CREATE TABLE IF NOT EXISTS admin_user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    permission_type TEXT NOT NULL CHECK (permission_type IN (
        'view_timesheets',
        'view_voice_notes',
        'manage_users',
        'manage_sites',
        'view_reports',
        'manage_settings'
    )),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint to prevent duplicate permissions
    UNIQUE(admin_user_id, permission_type)
);

-- Index for permission lookups
CREATE INDEX IF NOT EXISTS idx_admin_user_permissions_user_id ON admin_user_permissions(admin_user_id);

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE admin_users IS 'Admin users for dashboard access (separate from VAPI users)';
COMMENT ON COLUMN admin_users.username IS 'Email address used for login';
COMMENT ON COLUMN admin_users.password_hash IS 'bcrypt hashed password (never store plaintext)';
COMMENT ON COLUMN admin_users.role IS 'Access level: super_admin (all tenants), tenant_admin (one tenant), tenant_user (limited)';
COMMENT ON COLUMN admin_users.tenant_id IS 'NULL for super_admins, required for tenant_admin/tenant_user';

COMMENT ON TABLE admin_user_permissions IS 'Granular permissions for tenant_admin users';
COMMENT ON COLUMN admin_user_permissions.permission_type IS 'Specific feature access: view_timesheets, manage_users, etc.';

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================
-- Enable RLS on admin tables
-- Note: Backend uses service_role key which bypasses RLS
-- These policies are for additional security in case of key exposure

ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_user_permissions ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can do everything (this is what our backend uses)
CREATE POLICY "Service role has full access to admin_users"
    ON admin_users
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Service role has full access to admin_user_permissions"
    ON admin_user_permissions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Authenticated users can read their own record only (for future use)
CREATE POLICY "Users can read their own admin_user record"
    ON admin_users
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

-- No direct client access to these tables - all access through backend API

-- ============================================
-- NOTES
-- ============================================
-- 1. This does NOT replace or modify the 'tenants.api_key' column
-- 2. VAPI webhooks will continue using 'tenants.api_key' for authentication
-- 3. This system is ONLY for human users accessing the admin dashboard
-- 4. Initial super_admin user will be created by separate script
-- 5. RLS is enabled but backend uses service_role which bypasses it
-- 6. Admin authentication happens server-side, never client-side
