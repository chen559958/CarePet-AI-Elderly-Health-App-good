-- Drop the incorrect unique constraint on drug_name
ALTER TABLE drugs DROP CONSTRAINT IF EXISTS unique_drug_name;

-- Add a correct unique constraint on (user_id, drug_name)
-- We use conditional execution because we can't easily check for constraint existence in standard SQL without procedural code, 
-- but adding a constraint with a new name is generally safe if we dropped the old one.
-- However, there might be duplicates already? No, the error prevented duplicates.
-- Wait, if there are multiple users with "維生素 C" already (from before constraint?), the new constraint might fail if we don't clean up.
-- But the previous constraint prevented duplicates, so there can be AT MOST ONE "維生素 C" in the whole table.
-- So adding (user_id, drug_name) unique constraint is safe.

ALTER TABLE drugs ADD CONSTRAINT unique_user_drug_name UNIQUE (user_id, drug_name);
