-- Migration: Add tenant timezone and timesheet indexes for historical entries
-- Description: Enables multi-timezone support and historical timesheet management

-- 1. Add timezone column to tenants table
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'Australia/Sydney' NOT NULL;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_tenants_timezone ON tenants(timezone);

-- Update existing Built by MK tenant explicitly
UPDATE tenants
SET timezone = 'Australia/Sydney'
WHERE id = 'ba920f42-43df-44b5-a2e8-f740764a56d5';

-- Add comment for documentation
COMMENT ON COLUMN tenants.timezone IS 'IANA timezone identifier (e.g., Australia/Sydney, America/New_York, Europe/London). Used for all date/time operations for this tenant.';

-- 2. Add indexes for historical timesheet queries
-- Index for fetching recent timesheets (ordered by date descending)
CREATE INDEX IF NOT EXISTS idx_timesheets_user_date_range
ON timesheets(user_id, work_date DESC);

-- Index for checking conflicts by user, site, and date
CREATE INDEX IF NOT EXISTS idx_timesheets_user_site_date
ON timesheets(user_id, site_id, work_date);

-- Index for date range queries by tenant
CREATE INDEX IF NOT EXISTS idx_timesheets_tenant_date
ON timesheets(tenant_id, work_date DESC);

-- 3. Add comments for new indexes
COMMENT ON INDEX idx_timesheets_user_date_range IS 'Optimizes queries for recent timesheet history per user';
COMMENT ON INDEX idx_timesheets_user_site_date IS 'Optimizes conflict detection for duplicate entries';
COMMENT ON INDEX idx_timesheets_tenant_date IS 'Optimizes tenant-wide timesheet reporting';

-- Note: We allow multiple entries per site per day (split shifts, return visits)
-- No unique constraint added - workers can legitimately work same site multiple times per day
