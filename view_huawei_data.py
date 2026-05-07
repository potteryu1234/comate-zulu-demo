# -*- coding: utf-8 -*-
"""
查看华为天猫爬虫数据库内容
"""
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'zol_wristband',
    'charset': 'utf8mb4'
}

def view_data():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print('=' * 80)
    print('华为天猫智能穿戴专区 - 数据库内容查看')
    print('=' * 80)
    
    # 1. 商品表
    print('\n【商品表 (huawei_products)】')
    print('-' * 80)
    cursor.execute('SELECT COUNT(*) FROM huawei_products')
    count = cursor.fetchone()[0]
    print('总记录数: %d' % count)
    
    if count > 0:
        cursor.execute('''
            SELECT product_id, name, brand, current_price, original_price, 
                   discount, sales_count, rating_score, review_count, model
            FROM huawei_products
        ''')
        print('\n商品详情:')
        print('%-15s %-40s %-10s %-10s %-20s' % ('ID', '名称', '现价', '原价', '型号'))
        print('-' * 100)
        for row in cursor.fetchall():
            pid, name, brand, price, ori_price, discount, sales, rating, review_count, model = row
            name_short = name[:35] + '...' if len(name) > 35 else name
            print('%-15s %-40s %-10s %-10s %-20s' % (pid, name_short, str(price), str(ori_price), model or '-'))
        
        # 显示详细参数
        print('\n\n商品参数详情:')
        cursor.execute('''
            SELECT product_id, name, release_date, color, connection_type, 
                   strap_material, os, screen_resolution, health_monitoring
            FROM huawei_products
        ''')
        for row in cursor.fetchall():
            pid, name, release_date, color, conn, strap, os, resolution, health = row
            print('\n商品: %s' % name[:50])
            print('  上市时间: %s' % (release_date or '-'))
            print('  颜色: %s' % (color or '-'))
            print('  连接方式: %s' % (conn or '-'))
            print('  表带材质: %s' % (strap or '-'))
            print('  操作系统: %s' % (os or '-'))
            print('  屏幕分辨率: %s' % (resolution or '-'))
            print('  健康监测: %s' % (health or '-'))
    
    # 2. 评论关键词表
    print('\n\n' + '=' * 80)
    print('【评论关键词表 (huawei_review_keywords)】')
    print('-' * 80)
    cursor.execute('SELECT COUNT(*) FROM huawei_review_keywords')
    count = cursor.fetchone()[0]
    print('总记录数: %d' % count)
    
    if count > 0:
        cursor.execute('''
            SELECT k.product_id, p.name, k.keyword, k.count
            FROM huawei_review_keywords k
            JOIN huawei_products p ON k.product_id = p.product_id
            ORDER BY k.count DESC
        ''')
        print('\n关键词详情:')
        print('%-40s %-20s %-10s' % ('商品', '关键词', '数量'))
        print('-' * 80)
        for row in cursor.fetchall():
            pid, pname, keyword, count = row
            pname_short = pname[:35] + '...' if len(pname) > 35 else pname
            print('%-40s %-20s %-10s' % (pname_short, keyword, count))
    
    # 3. 评论表
    print('\n\n' + '=' * 80)
    print('【用户评论表 (huawei_reviews)】')
    print('-' * 80)
    cursor.execute('SELECT COUNT(*) FROM huawei_reviews')
    total_reviews = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM huawei_reviews WHERE is_negative = TRUE')
    negative_reviews = cursor.fetchone()[0]
    
    print('总评论数: %d' % total_reviews)
    if total_reviews > 0:
        print('差评数: %d (%.1f%%)' % (negative_reviews, negative_reviews/total_reviews*100))
        print('好评数: %d (%.1f%%)' % (total_reviews - negative_reviews, (total_reviews-negative_reviews)/total_reviews*100))
    
    if total_reviews > 0:
        print('\n评论详情:')
        print('-' * 80)
        cursor.execute('''
            SELECT r.product_id, p.name, r.content, r.is_negative
            FROM huawei_reviews r
            JOIN huawei_products p ON r.product_id = p.product_id
            ORDER BY r.is_negative DESC, r.id
        ''')
        for row in cursor.fetchall():
            pid, pname, content, is_negative = row
            review_type = '【差评】' if is_negative else '【好评】'
            print('\n%s %s' % (review_type, pname[:40]))
            if len(content) > 100:
                print('  %s...' % content[:100])
            else:
                print('  %s' % content)
    
    print('\n' + '=' * 80)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    view_data()
