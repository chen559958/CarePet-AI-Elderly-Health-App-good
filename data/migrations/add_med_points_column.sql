-- 新增 med_points_today 到 pet_daily_interactions 表

ALTER TABLE pet_daily_interactions ADD COLUMN IF NOT EXISTS med_points_today INTEGER NOT NULL DEFAULT 0;
