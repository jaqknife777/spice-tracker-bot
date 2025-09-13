-- Remove leftover_sand column from expedition_participants table
-- This migration removes the leftover_sand tracking functionality

-- Drop the leftover_sand column from expedition_participants table
ALTER TABLE expedition_participants DROP COLUMN IF EXISTS leftover_sand;
