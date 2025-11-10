-- Migration: Create timesheets table
-- Description: Stores daily timesheet entries for work logged at sites

CREATE TABLE IF NOT EXISTS timesheets (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    vapi_call_id TEXT,

    -- Timesheet Data
    work_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hours_worked NUMERIC(5,2) NOT NULL, -- Calculated field, stored for convenience
    work_description TEXT,
    plans_for_tomorrow TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_timesheets_site_id ON timesheets(site_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_tenant_id ON timesheets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_user_id ON timesheets(user_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_work_date ON timesheets(work_date);
CREATE INDEX IF NOT EXISTS idx_timesheets_vapi_call_id ON timesheets(vapi_call_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_user_date ON timesheets(user_id, work_date);

-- Enable Row Level Security
ALTER TABLE timesheets ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see timesheets from their tenant
CREATE POLICY "Users can view their tenant's timesheets"
    ON timesheets
    FOR SELECT
    USING (tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid()));

-- RLS Policy: Users can insert timesheets for their tenant
CREATE POLICY "Users can create timesheets for their tenant"
    ON timesheets
    FOR INSERT
    WITH CHECK (
        tenant_id = (SELECT tenant_id FROM users WHERE id = auth.uid())
        AND user_id = auth.uid()
    );

-- RLS Policy: Users can update their own timesheets
CREATE POLICY "Users can update their own timesheets"
    ON timesheets
    FOR UPDATE
    USING (user_id = auth.uid());

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_timesheets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function
CREATE TRIGGER update_timesheets_updated_at
    BEFORE UPDATE ON timesheets
    FOR EACH ROW
    EXECUTE FUNCTION update_timesheets_updated_at();

-- Comments for documentation
COMMENT ON TABLE timesheets IS 'Stores daily timesheet entries for work performed at construction sites';
COMMENT ON COLUMN timesheets.hours_worked IS 'Calculated from start_time and end_time, stored for convenience';
COMMENT ON COLUMN timesheets.work_description IS 'Brief description of work performed at the site';
COMMENT ON COLUMN timesheets.plans_for_tomorrow IS 'What the user plans to do at this site tomorrow';
