-- 新增 unlock_level 到 pet_collection 表

ALTER TABLE pet_collection ADD COLUMN IF NOT EXISTS unlock_level INTEGER NOT NULL DEFAULT 1;
