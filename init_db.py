# -*- coding: utf-8 -*-
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

cursor.execute("CREATE DATABASE IF NOT EXISTS zol_wristband CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cursor.execute('USE zol_wristband')

cursor.execute('''
CREATE TABLE IF NOT EXISTS wristbands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price VARCHAR(50),
    intro TEXT,
    keywords TEXT,
    features TEXT,
    specs TEXT,
    url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wristband_id INT,
    rating VARCHAR(20),
    comment TEXT,
    FOREIGN KEY (wristband_id) REFERENCES wristbands(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
''')

# 用户行为表（用于协同过滤）
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_behaviors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100),
    wristband_id INT,
    behavior_type ENUM('view', 'compare', 'favorite', 'score') DEFAULT 'view',
    score INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wristband_id) REFERENCES wristbands(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_product (wristband_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
''')

conn.commit()
cursor.close()
conn.close()
print('数据库初始化成功')