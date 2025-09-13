-- Remove Settings Table Migration for Spice Tracker Bot
-- Remove settings table and all related functionality

-- Drop the settings table index first
DROP INDEX IF EXISTS idx_settings_key;

-- Drop the settings table
DROP TABLE IF EXISTS settings;
