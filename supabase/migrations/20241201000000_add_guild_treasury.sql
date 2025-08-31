-- Guild Treasury System Migration
-- Adds guild cut functionality to expeditions and creates guild treasury

-- Add guild_cut_percentage to expeditions table
ALTER TABLE expeditions ADD COLUMN IF NOT EXISTS guild_cut_percentage FLOAT DEFAULT 10.0;

-- Create guild_treasury table
CREATE TABLE IF NOT EXISTS guild_treasury (
    id SERIAL PRIMARY KEY,
    guild_name TEXT NOT NULL,
    total_sand INTEGER DEFAULT 0,
    total_melange INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create guild_transactions table for audit trail
CREATE TABLE IF NOT EXISTS guild_transactions (
    id SERIAL PRIMARY KEY,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal')),
    sand_amount INTEGER NOT NULL,
    melange_amount INTEGER DEFAULT 0,
    expedition_id INTEGER,
    admin_user_id TEXT,
    admin_username TEXT,
    target_user_id TEXT,
    target_username TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expedition_id) REFERENCES expeditions (id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_guild_transactions_type ON guild_transactions (transaction_type);
CREATE INDEX IF NOT EXISTS idx_guild_transactions_created_at ON guild_transactions (created_at);
CREATE INDEX IF NOT EXISTS idx_guild_transactions_expedition_id ON guild_transactions (expedition_id);

-- Insert initial guild treasury record (will be updated by bot)
INSERT INTO guild_treasury (guild_name, total_sand, total_melange) 
VALUES ('Default Guild', 0, 0) 
ON CONFLICT DO NOTHING;

-- Update existing expeditions to have default guild cut
UPDATE expeditions 
SET guild_cut_percentage = 10.0 
WHERE guild_cut_percentage IS NULL;
