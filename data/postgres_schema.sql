-- PostgreSQL Schema for GameMed (Full Migration)

-- Drop existing tables to ensure clean state
DROP TABLE IF EXISTS undo_actions CASCADE;
DROP TABLE IF EXISTS reminder_events CASCADE;
DROP TABLE IF EXISTS point_ledger CASCADE;
DROP TABLE IF EXISTS user_inventory CASCADE;
DROP TABLE IF EXISTS shop_items CASCADE;
DROP TABLE IF EXISTS pet_collection CASCADE;
DROP TABLE IF EXISTS pets CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS medication_logs CASCADE;
DROP TABLE IF EXISTS drugs CASCADE;
DROP TABLE IF EXISTS blood_pressure CASCADE;
DROP TABLE IF EXISTS user_profile CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1) Users table for authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 1.1) User Profile
CREATE TABLE user_profile (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT,
  breakfast_time TEXT NOT NULL,
  lunch_time TEXT NOT NULL,
  dinner_time TEXT NOT NULL,
  sleep_time TEXT NOT NULL,
  haptics_enabled INTEGER NOT NULL DEFAULT 1,
  snooze_minutes INTEGER NOT NULL DEFAULT 10,
  gentle_mode INTEGER NOT NULL DEFAULT 1,
  line_id TEXT,
  birthday TEXT,
  notifications_enabled INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id)
);

-- 2) Blood Pressure Records
CREATE TABLE blood_pressure (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  systolic INTEGER NOT NULL,
  diastolic INTEGER NOT NULL,
  pulse INTEGER,
  photo_path TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3) Drugs/Supplements
CREATE TABLE drugs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  person_name TEXT,
  pharmacist TEXT,
  department TEXT,
  drug_name TEXT NOT NULL,
  usage_method TEXT DEFAULT '口服',
  dosage_text TEXT,
  intake_timing TEXT NOT NULL DEFAULT 'after_meal',
  intake_periods TEXT NOT NULL,
  pills_per_intake INTEGER NOT NULL DEFAULT 1,
  hospital TEXT,
  doctor TEXT,
  warning TEXT,
  side_effect TEXT,
  notes TEXT,
  active INTEGER NOT NULL DEFAULT 1,
  photo_path TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, drug_name)
);

-- 4) Medication Logs
CREATE TABLE medication_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  drug_id INTEGER NOT NULL REFERENCES drugs(id),
  status TEXT NOT NULL,
  reminder_event_id INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5) Appointments
CREATE TABLE appointments (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  clinic_name TEXT NOT NULL,
  doctor TEXT,
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6) Pets
CREATE TABLE pets (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  pet_name TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 1,
  exp INTEGER NOT NULL DEFAULT 0,
  mood INTEGER NOT NULL DEFAULT 60,
  stamina INTEGER NOT NULL DEFAULT 60,
  state TEXT NOT NULL DEFAULT 'normal',
  bowl_expires_at TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP + interval '48 hours'),
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id)
);

-- 7) Pet Collection
CREATE TABLE pet_collection (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  pet_name TEXT NOT NULL,
  pet_type TEXT NOT NULL,
  unlocked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8) Shop Items
CREATE TABLE shop_items (
  id SERIAL PRIMARY KEY,
  category TEXT NOT NULL,
  name TEXT NOT NULL,
  cost INTEGER NOT NULL,
  stock INTEGER NOT NULL DEFAULT 999999,
  effect_json TEXT,
  image_path TEXT,
  active INTEGER NOT NULL DEFAULT 1
);

-- 9) User Inventory
CREATE TABLE user_inventory (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  item_id INTEGER NOT NULL REFERENCES shop_items(id),
  quantity INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, item_id)
);

-- 10) Point Ledger
CREATE TABLE point_ledger (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  delta INTEGER NOT NULL,
  reason TEXT NOT NULL,
  ref_type TEXT,
  ref_id INTEGER,
  note TEXT
);

-- 11) Reminder Events
CREATE TABLE reminder_events (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  drug_id INTEGER NOT NULL REFERENCES drugs(id),
  date TEXT NOT NULL,
  planned_time TIMESTAMP NOT NULL,
  action_time TIMESTAMP,
  status TEXT NOT NULL,
  snooze_count INTEGER NOT NULL DEFAULT 0,
  caregiver_notified INTEGER NOT NULL DEFAULT 0,
  notification_id INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, drug_id, date, planned_time)
);

-- 12) Pet Daily Interactions
CREATE TABLE pet_daily_interactions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  snack_mood_total INTEGER NOT NULL DEFAULT 0,
  toy_used TEXT,
  pet_interact_used INTEGER NOT NULL DEFAULT 0,
  all_meds_taken INTEGER NOT NULL DEFAULT 0,
  bp_completed INTEGER NOT NULL DEFAULT 0,
  bp_bonus_awarded INTEGER NOT NULL DEFAULT 0,
  med_points_today INTEGER NOT NULL DEFAULT 0,
  last_decay_time TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, date)
);
CREATE INDEX idx_pet_daily_interactions_date ON pet_daily_interactions(date);

-- 13) Undo Actions
CREATE TABLE undo_actions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  action_key TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  payload_json TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_reminder_events_date ON reminder_events(date);
CREATE INDEX idx_reminder_events_status ON reminder_events(status);
CREATE INDEX idx_med_logs_date ON medication_logs(date);

-- New Optimization Indices
CREATE INDEX idx_reminder_events_user_date ON reminder_events(user_id, date);
CREATE INDEX idx_reminder_events_user_id ON reminder_events(user_id);
CREATE INDEX idx_med_logs_user_id ON medication_logs(user_id);
CREATE INDEX idx_drugs_user_id ON drugs(user_id);
CREATE INDEX idx_bp_user_id ON blood_pressure(user_id);

