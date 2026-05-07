-- 添加图片URL和品牌字段
USE zol_wristband;

-- 添加 brand 字段
ALTER TABLE wristbands ADD COLUMN brand VARCHAR(100) AFTER id;

-- 添加 image_url 字段
ALTER TABLE wristbands ADD COLUMN image_url TEXT AFTER url;

-- 为 image_url 添加索引（可选，如果需要根据图片URL搜索）
-- CREATE INDEX idx_image_url ON wristbands(image_url(255));

SELECT 'Migration completed: brand and image_url fields added to wristbands table' AS status;
