-- Update sand_per_melange to REAL and remove leftover_sand

-- Alter the expeditions table to change the data type of sand_per_melange
ALTER TABLE expeditions
ALTER COLUMN sand_per_melange TYPE REAL;

-- Alter the expedition_participants table to remove the leftover_sand column
ALTER TABLE expedition_participants
DROP COLUMN leftover_sand;
