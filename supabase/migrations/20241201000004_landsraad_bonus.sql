-- Landsraad Bonus Migration
-- Adds global landsraad bonus state tracking for melange conversion rates

-- Global settings table for bot-wide configuration
CREATE TABLE global_settings (
    id SERIAL PRIMARY KEY,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default landsraad bonus setting (disabled by default)
INSERT INTO global_settings (setting_key, setting_value, description)
VALUES ('landsraad_bonus_active', 'false', 'Whether the landsraad bonus is active (37.5 sand = 1 melange instead of 50)');

-- Create index for fast lookups
CREATE INDEX idx_global_settings_key ON global_settings (setting_key);

-- Function to update setting timestamp
CREATE OR REPLACE FUNCTION update_setting_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for setting timestamp updates
CREATE TRIGGER update_global_settings_timestamp
    BEFORE UPDATE ON global_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_setting_timestamp();

-- Comments for documentation
COMMENT ON TABLE global_settings IS 'Global bot configuration settings';
COMMENT ON COLUMN global_settings.setting_key IS 'Unique identifier for the setting';
COMMENT ON COLUMN global_settings.setting_value IS 'String value of the setting (can be boolean, number, etc.)';
COMMENT ON COLUMN global_settings.description IS 'Human-readable description of what this setting controls';
