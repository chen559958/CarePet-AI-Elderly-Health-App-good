-- 新增寵物每日互動追蹤表 (SQLite)

CREATE TABLE IF NOT EXISTS pet_daily_interactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL UNIQUE,
  snack_mood_total INTEGER NOT NULL DEFAULT 0,      -- 零食累計心情值 (上限 10)
  toy_used TEXT,                                     -- 今日使用的玩具名稱
  pet_interact_used INTEGER NOT NULL DEFAULT 0,     -- 是否已使用寵物互動 (0/1)
  all_meds_taken INTEGER NOT NULL DEFAULT 0,        -- 是否完成所有用藥 (0/1)
  bp_completed INTEGER NOT NULL DEFAULT 0,          -- 是否完成血壓測量 (0/1)
  last_decay_time TEXT,                              -- 上次心情衰減時間
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pet_daily_interactions_date ON pet_daily_interactions(date);
