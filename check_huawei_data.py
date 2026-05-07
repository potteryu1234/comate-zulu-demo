# -*- coding: utf-8 -*-
"""
检查华为天猫爬虫数据
"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'zol_wristband',
    'charset': 'utf8mb4'
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 检查商品表
    cursor.execute('SELECT COUNT(*) FROM huawei_products')
    product_count = cursor.fetchone()[0]
    print(f'商品数量: {product_count}')
    
    if product_count > 0:
        cursor.execute('SELECT product_id, name, current_price FROM huawei_products LIMIT 5')
        print('\n商品示例:')
        for row in cursor.fetchall():
            print(f'  - {row[0]}: {row[1][:50]}... 价格:{row[2]}')
    
    # 检查关键词表
    cursor.execute('SELECT COUNT(*) FROM huawei_review_keywords')
    keyword_count = cursor.fetchone()[0]
    print(f'\n评论关键词数量: {keyword_count}')
    
    # 检查评论表
    cursor.execute('SELECT COUNT(*) FROM huawei_reviews')
    review_count = cursor.fetchone()[0]
    print(f'评论数量: {review_count}')
    
    cursor.execute('SELECT COUNT(*) FROM huawei_reviews WHERE is_negative = TRUE')
    negative_count = cursor.fetchone()[0]
    print(f'  - 差评数量: {negative_count}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'查询失败: {e}')
