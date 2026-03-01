-- 1. 修改 pets 表，加入 image_path
ALTER TABLE pets ADD COLUMN IF NOT EXISTS image_path TEXT;

-- 2. 重構 pet_collection 表
DROP TABLE IF EXISTS pet_collection;
CREATE TABLE pet_collection (
  id SERIAL PRIMARY KEY,
  pet_name TEXT NOT NULL,
  pet_type TEXT NOT NULL, -- 使用圖片檔名作為類型標識 (e.g. 'cat', 'dog', 'default')
  image_path TEXT NOT NULL,
  final_level INTEGER NOT NULL,
  graduated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
