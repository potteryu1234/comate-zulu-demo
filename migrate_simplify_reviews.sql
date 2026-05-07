-- 简化 reviews 表结构，舍弃不必要的字段
USE zol_wristband;

-- 备份现有数据（可选）
CREATE TABLE IF NOT EXISTS reviews_backup AS SELECT * FROM reviews;

-- 删除不必要的字段
ALTER TABLE reviews DROP COLUMN upvote;
ALTER TABLE reviews DROP COLUMN comment_time;
ALTER TABLE reviews DROP COLUMN created_at;
ALTER TABLE reviews DROP COLUMN source_url;
ALTER TABLE reviews DROP COLUMN username;

-- 查看简化后的表结构
DESCRIBE reviews;

SELECT 'Migration completed: reviews table simplified' AS status;
SELECT 'Backup table: reviews_backup created' AS info;
