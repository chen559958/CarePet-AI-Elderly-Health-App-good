-- 新增寵物每日互動追蹤表 (PostgreSQL)

CREATE TABLE IF NOT EXISTS pet_daily_interactions (
  id SERIAL PRIMARY KEY,
  date TEXT NOT NULL UNIQUE,
  snack_mood_total INTEGER NOT NULL DEFAULT 0,      -- 零食累計心情值 (上限 10)
  toy_used TEXT,                                     -- 今日使用的玩具名稱
  pet_interact_used BOOLEAN NOT NULL DEFAULT FALSE, -- 是否已使用寵物互動
  all_meds_taken BOOLEAN NOT NULL DEFAULT FALSE,    -- 是否完成所有用藥
  bp_completed BOOLEAN NOT NULL DEFAULT FALSE,      -- 是否完成血壓測量
  last_decay_time TIMESTAMP,                         -- 上次心情衰減時間
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pet_daily_interactions_date ON pet_daily_interactions(date);
