-- Performance Index Migration for Spice Tracker Bot
-- Add composite indexes for improved query performance

-- Index for leaderboard queries - optimizes ordering by total_melange DESC, username ASC
CREATE INDEX idx_users_leaderboard ON users (total_melange DESC, username ASC);

-- Index for user deposit history queries - optimizes filtering by user_id and ordering by created_at DESC
CREATE INDEX idx_deposits_user_id_created_at ON deposits (user_id, created_at DESC);

-- Additional performance indexes based on common query patterns

-- Index for pending melange queries - optimizes filtering users with pending payments
CREATE INDEX idx_users_pending_melange ON users (total_melange, paid_melange)
WHERE total_melange > paid_melange;

-- Index for expedition participants ordering - optimizes harvester-first, then username ordering
CREATE INDEX idx_expedition_participants_harvester_username ON expedition_participants (expedition_id, is_harvester DESC, username ASC);

-- Index for unpaid deposits queries - optimizes filtering and ordering unpaid deposits
CREATE INDEX idx_deposits_unpaid_created_at ON deposits (paid, created_at ASC)
WHERE paid = FALSE;

-- Index for expedition deposits with user filtering - optimizes user expedition history queries
CREATE INDEX idx_deposits_user_type_created_at ON deposits (user_id, type, created_at DESC);

-- Index for guild transactions by type and date - optimizes transaction history queries
CREATE INDEX idx_guild_transactions_type_created_at ON guild_transactions (transaction_type, created_at DESC);

-- Index for melange payments by user and date - optimizes payment history queries
CREATE INDEX idx_melange_payments_user_created_at ON melange_payments (user_id, created_at DESC);

-- Index for expedition lookups by initiator - optimizes finding expeditions by creator
CREATE INDEX idx_expeditions_initiator_created_at ON expeditions (initiator_id, created_at DESC);

-- Index for guild treasury updates - optimizes finding the latest treasury record
CREATE INDEX idx_guild_treasury_id_desc ON guild_treasury (id DESC);
