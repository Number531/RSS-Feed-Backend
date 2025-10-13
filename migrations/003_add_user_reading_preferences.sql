-- Migration: Add user_reading_preferences table
-- Date: 2025-10-10
-- Purpose: Store user privacy and reading preferences

CREATE TABLE IF NOT EXISTS user_reading_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Tracking preferences
    tracking_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    analytics_opt_in BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Auto-cleanup settings
    auto_cleanup_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    retention_days INTEGER NOT NULL DEFAULT 365,
    
    -- Privacy settings
    exclude_categories TEXT[] NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_user_reading_preferences_user_id ON user_reading_preferences(user_id);

-- Add check constraint for retention_days
ALTER TABLE user_reading_preferences
ADD CONSTRAINT ck_retention_days_positive CHECK (retention_days > 0 AND retention_days <= 3650);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_reading_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_reading_preferences_updated_at
    BEFORE UPDATE ON user_reading_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_user_reading_preferences_updated_at();

-- Verify table creation
SELECT 'user_reading_preferences table created successfully' AS status;
