# -*- coding: utf-8 -*-
"""
华为天猫智能穿戴数据库初始化脚本
"""
import pymysql

# MySQL连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

# 创建数据库
cursor.execute("CREATE DATABASE IF NOT EXISTS zol_wristband CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute('USE zol_wristband')

# 商品表
cursor.execute('''
CREATE TABLE IF NOT EXISTS huawei_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL COMMENT '天猫商品ID',
    name VARCHAR(500) NOT NULL COMMENT '商品名称',
    brand VARCHAR(100) COMMENT '品牌',
    current_price DECIMAL(10,2) COMMENT '当前售价',
    original_price DECIMAL(10,2) COMMENT '原价',
    discount VARCHAR(200) COMMENT '优惠信息',
    sales_count VARCHAR(50) COMMENT '销量文本',
    rating_score DECIMAL(2,1) COMMENT '评分',
    review_count VARCHAR(50) COMMENT '评价数量文本',
    url VARCHAR(500) COMMENT '商品链接',
    image_url VARCHAR(500) COMMENT '主图链接',
    
    -- 参数详情
    release_date DATE COMMENT '上市时间',
    color VARCHAR(200) COMMENT '外观颜色',
    connection_type VARCHAR(100) COMMENT '连接方式',
    strap_material VARCHAR(200) COMMENT '表带材质',
    os VARCHAR(100) COMMENT '操作系统',
    communication VARCHAR(100) COMMENT '通讯类型',
    warranty VARCHAR(50) COMMENT '保修期',
    dial_shape VARCHAR(50) COMMENT '表盘形状',
    case_material VARCHAR(300) COMMENT '表壳材质',
    model VARCHAR(100) COMMENT '型号',
    screen_resolution VARCHAR(100) COMMENT '屏幕分辨率',
    charging_mode VARCHAR(100) COMMENT '充电模式',
    health_monitoring TEXT COMMENT '健康监测功能',
    screen_type VARCHAR(100) COMMENT '屏幕类型',
    
    source VARCHAR(50) DEFAULT 'tmall_huawei' COMMENT '数据来源',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '爬取时间',
    INDEX idx_product_id (product_id),
    INDEX idx_model (model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
''')

# 评论关键词表
cursor.execute('''
CREATE TABLE IF NOT EXISTS huawei_review_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL COMMENT '商品ID',
    keyword VARCHAR(200) NOT NULL COMMENT '关键词',
    count INT DEFAULT 0 COMMENT '出现次数',
    percentage DECIMAL(5,2) COMMENT '占比(%)',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES huawei_products(product_id) ON DELETE CASCADE,
    INDEX idx_product_keyword (product_id, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
''')

# 用户评论表（简化版，只保留评论内容）
cursor.execute('''
CREATE TABLE IF NOT EXISTS huawei_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL COMMENT '商品ID',
    content TEXT COMMENT '评论内容',
    is_negative BOOLEAN DEFAULT FALSE COMMENT '是否为差评（优先爬取）',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES huawei_products(product_id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_is_negative (is_negative)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
''')

conn.commit()
cursor.close()
conn.close()
print('华为天猫数据库初始化成功')
