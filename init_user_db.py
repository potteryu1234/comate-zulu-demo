# -*- coding: utf-8 -*-
"""
用户系统数据库初始化
添加用户表、行为记录表、收藏表等
"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

def init_user_tables():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("USE zol_wristband")
    
    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100),
            nickname VARCHAR(50),
            avatar VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # 用户行为记录表（浏览、收藏、对比）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_behaviors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            behavior_type ENUM('view', 'favorite', 'compare', 'search') NOT NULL,
            behavior_value VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES wristbands(id) ON DELETE CASCADE,
            INDEX idx_user_behavior (user_id, behavior_type),
            INDEX idx_product_behavior (product_id, behavior_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # 用户评分表（显式评分）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_ratings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            rating DECIMAL(2,1) NOT NULL CHECK (rating >= 0 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES wristbands(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_product_rating (user_id, product_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # 用户权重偏好表（保存用户的自定义权重设置）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            preference_name VARCHAR(50) NOT NULL,
            health_breadth INT DEFAULT 20,
            data_accuracy INT DEFAULT 20,
            battery_life INT DEFAULT 20,
            comfort INT DEFAULT 15,
            brand_reputation INT DEFAULT 15,
            price_performance INT DEFAULT 10,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_user_pref_name (user_id, preference_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    
    # 插入测试用户
    cursor.execute("""
        INSERT IGNORE INTO users (id, username, password, email, nickname) VALUES
        (1, 'test_user', 'test123', 'test@example.com', '测试用户'),
        (2, 'user_a', 'pass123', 'usera@example.com', '用户A'),
        (3, 'user_b', 'pass123', 'userb@example.com', '用户B'),
        (4, 'user_c', 'pass123', 'userc@example.com', '用户C')
    """)
    
    # 插入模拟行为数据（用于协同过滤）
    cursor.execute("""
        INSERT IGNORE INTO user_behaviors (user_id, product_id, behavior_type, created_at)
        SELECT 
            FLOOR(1 + RAND() * 4) as user_id,
            FLOOR(1 + RAND() * 50) as product_id,
            ELT(FLOOR(1 + RAND() * 3), 'view', 'favorite', 'compare') as behavior_type,
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND() * 30) DAY) as created_at
        FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) t1,
             (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) t2,
             (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) t3
    """)
    
    # 插入模拟评分数据
    cursor.execute("""
        INSERT IGNORE INTO user_ratings (user_id, product_id, rating, comment)
        SELECT 
            FLOOR(1 + RAND() * 4) as user_id,
            FLOOR(1 + RAND() * 50) as product_id,
            ROUND(3 + RAND() * 2, 1) as rating,
            ELT(FLOOR(1 + RAND() * 5), '很好用', '性价比不错', '功能齐全', '续航一般', '外观好看') as comment
        FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) t1,
             (SELECT 1 UNION SELECT 2 UNION SELECT 3) t2
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("用户系统数据库表初始化成功！")
    print("测试用户：test_user/test123, user_a/pass123, user_b/pass123, user_c/pass123")

if __name__ == '__main__':
    init_user_tables()
