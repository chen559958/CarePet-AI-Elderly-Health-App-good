PRAGMA foreign_keys = ON;

-- 1) 使用者設定
-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 1.1) 使用者設定檔
CREATE TABLE IF NOT EXISTS user_profile (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT,
  breakfast_time TEXT NOT NULL,
  lunch_time TEXT NOT NULL,
  dinner_time TEXT NOT NULL,
  sleep_time TEXT NOT NULL,
  haptics_enabled INTEGER NOT NULL DEFAULT 1,
  notifications_enabled INTEGER NOT NULL DEFAULT 1,
  snooze_minutes INTEGER NOT NULL DEFAULT 10,
  gentle_mode INTEGER NOT NULL DEFAULT 1,
  line_id TEXT,
  birthday TEXT,
  created_at TEXT NOT NULL,

  updated_at TEXT NOT NULL,
  UNIQUE(user_id)
);

-- 2) 血壓紀錄
CREATE TABLE IF NOT EXISTS blood_pressure (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  systolic INTEGER NOT NULL,
  diastolic INTEGER NOT NULL,
  pulse INTEGER,
  photo_path TEXT,
  created_at TEXT NOT NULL
);

-- 3) 藥品/保健品
CREATE TABLE IF NOT EXISTS drugs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  person_name TEXT,
  pharmacist TEXT,
  department TEXT,
  drug_name TEXT NOT NULL,
  usage_method TEXT DEFAULT '口服',  -- 新增: 吸入/口服/外敷
  dosage_text TEXT,
  intake_timing TEXT NOT NULL DEFAULT 'after_meal',  -- 餐前/餐後
  intake_periods TEXT NOT NULL,  -- 早/中/晚/睡前
  pills_per_intake INTEGER NOT NULL DEFAULT 1,
  hospital TEXT,  -- 新增: 醫院
  doctor TEXT,    -- 新增: 醫生
  warning TEXT,
  side_effect TEXT,
  notes TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  photo_path TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(user_id, drug_name)
);

-- 4) 用藥紀錄
CREATE TABLE IF NOT EXISTS medication_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  drug_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  reminder_event_id INTEGER,
  created_at TEXT NOT NULL,
  FOREIGN KEY(drug_id) REFERENCES drugs(id)
);

-- 5) 回診
CREATE TABLE IF NOT EXISTS appointments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  clinic_name TEXT NOT NULL,
  doctor TEXT,
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  notes TEXT,
  created_at TEXT NOT NULL
);

-- 6) 電子寵物
CREATE TABLE IF NOT EXISTS pets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  pet_name TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 1,
  exp INTEGER NOT NULL DEFAULT 0,
  mood INTEGER NOT NULL DEFAULT 60,
  stamina INTEGER NOT NULL DEFAULT 60,
  state TEXT NOT NULL DEFAULT 'normal',
  bowl_expires_at TEXT,
  image_path TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(user_id)
);

-- 7) 寵物圖鑑
CREATE TABLE IF NOT EXISTS pet_collection (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  pet_name TEXT NOT NULL,
  pet_type TEXT NOT NULL,
  image_path TEXT NOT NULL,
  final_level INTEGER NOT NULL,
  graduated_at TEXT NOT NULL,
  unlocked_at TEXT NOT NULL
);

-- 8) 商城品項
CREATE TABLE IF NOT EXISTS shop_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL,
  name TEXT NOT NULL,
  cost INTEGER NOT NULL,
  stock INTEGER NOT NULL DEFAULT 999999,
  effect_json TEXT,
  image_path TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

-- 9) 使用者庫存
CREATE TABLE IF NOT EXISTS user_inventory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  item_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(item_id) REFERENCES shop_items(id),
  UNIQUE(user_id, item_id)
);

-- 10) 寵物每日互動追蹤 (新增)
CREATE TABLE IF NOT EXISTS pet_daily_interactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  snack_mood_total INTEGER NOT NULL DEFAULT 0,
  toy_used TEXT,
  pet_interact_used BOOLEAN NOT NULL DEFAULT FALSE,
  all_meds_taken BOOLEAN NOT NULL DEFAULT FALSE,
  bp_completed BOOLEAN NOT NULL DEFAULT FALSE,
  bp_bonus_awarded BOOLEAN NOT NULL DEFAULT FALSE,
  med_points_today INTEGER NOT NULL DEFAULT 0,
  last_decay_time TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, date)
);
CREATE INDEX IF NOT EXISTS idx_pet_daily_interactions_date ON pet_daily_interactions(date);

-- 10) 點數帳本
CREATE TABLE IF NOT EXISTS point_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  datetime TEXT NOT NULL,
  delta INTEGER NOT NULL,
  reason TEXT NOT NULL,
  ref_type TEXT,
  ref_id INTEGER,
  note TEXT
);

-- 11) 提醒事件
CREATE TABLE IF NOT EXISTS reminder_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  drug_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  planned_time TEXT NOT NULL,
  action_time TEXT,
  status TEXT NOT NULL,
  snooze_count INTEGER NOT NULL DEFAULT 0,
  caregiver_notified INTEGER NOT NULL DEFAULT 0,
  notification_id INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(drug_id) REFERENCES drugs(id),
  UNIQUE(user_id, drug_id, date, planned_time)
);

-- 12) 撤回動作
CREATE TABLE IF NOT EXISTS undo_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  action_key TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reminder_events_date ON reminder_events(date);
CREATE INDEX IF NOT EXISTS idx_reminder_events_status ON reminder_events(status);
CREATE INDEX IF NOT EXISTS idx_med_logs_date ON medication_logs(date);
