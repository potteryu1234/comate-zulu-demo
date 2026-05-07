# -*- coding: utf-8 -*-
"""
插入华为天猫示例数据
用于演示系统功能
"""
import pymysql
from datetime import datetime, date

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'zol_wristband',
    'charset': 'utf8mb4'
}

# 示例商品数据（基于截图中的真实数据）
sample_products = [
    {
        'product_id': '975529162954',
        'name': '【国家补贴】HUAWEI WATCH GT 6华为手表智能运动手表情绪健康管理长续航健康监测正品华为官方正品',
        'brand': '华为',
        'current_price': 1187.90,
        'original_price': 1488.00,
        'discount': '立减300元',
        'sales_count': '已售6万+',
        'rating_score': 5.0,
        'review_count': '6000+',
        'url': 'https://detail.tmall.com/item.htm?id=975529162954',
        'image_url': '',
        'release_date': date(2025, 9, 24),
        'color': '41mm 魅影黑',
        'connection_type': '蓝牙连接',
        'strap_material': '氟橡胶/复合编织/复合素皮',
        'os': '鸿蒙系统',
        'communication': '不可插卡',
        'warranty': '1年',
        'dial_shape': '圆形',
        'case_material': '前壳：不锈钢；底壳：高性能纤维增强复合材料',
        'model': 'HUAWEI WATCH GT 6',
        'screen_resolution': '466x466像素',
        'charging_mode': '无线充电',
        'health_monitoring': '心率监测 体温监测 生理周期提醒 睡眠监测 血氧监测',
        'screen_type': 'AMOLED',
    },
    {
        'product_id': '975529162955',
        'name': '【国家补贴 送礼送健康】HUAWEI WATCH 5华为手表智能',
        'brand': '华为',
        'current_price': 2098.90,
        'original_price': 2499.00,
        'discount': '至高优惠900元',
        'sales_count': '已售2万+',
        'rating_score': 4.9,
        'review_count': '3000+',
        'url': 'https://detail.tmall.com/item.htm?id=975529162955',
        'image_url': '',
        'release_date': date(2025, 8, 15),
        'color': '46mm 雅丹黑',
        'connection_type': '蓝牙连接',
        'strap_material': '氟橡胶',
        'os': '鸿蒙系统',
        'communication': 'eSIM',
        'warranty': '1年',
        'dial_shape': '圆形',
        'case_material': '钛合金',
        'model': 'HUAWEI WATCH 5',
        'screen_resolution': '466x466像素',
        'charging_mode': '无线充电',
        'health_monitoring': '心率监测 血氧监测 睡眠监测 压力监测',
        'screen_type': 'AMOLED',
    },
    {
        'product_id': '975529162956',
        'name': '华为手环10智能手环专业睡眠分析情绪健康铝合金机身',
        'brand': '华为',
        'current_price': 228.90,
        'original_price': 269.00,
        'discount': '优惠40元',
        'sales_count': '已售10万+',
        'rating_score': 4.8,
        'review_count': '15000+',
        'url': 'https://detail.tmall.com/item.htm?id=975529162956',
        'image_url': '',
        'release_date': date(2025, 10, 1),
        'color': '幻夜黑',
        'connection_type': '蓝牙连接',
        'strap_material': 'TPU',
        'os': '鸿蒙系统',
        'communication': '不可插卡',
        'warranty': '1年',
        'dial_shape': '方形',
        'case_material': '铝合金',
        'model': '华为手环10',
        'screen_resolution': '194x368像素',
        'charging_mode': '磁吸充电',
        'health_monitoring': '睡眠监测 心率监测 血氧监测 压力监测 生理周期',
        'screen_type': 'AMOLED',
    },
]

# 示例评论关键词
sample_keywords = [
    {'product_id': '975529162954', 'keyword': '续航能力够用', 'count': 875},
    {'product_id': '975529162954', 'keyword': '功能性很强', 'count': 736},
    {'product_id': '975529162954', 'keyword': '外观很大气', 'count': 689},
    {'product_id': '975529162954', 'keyword': '表盘很大气', 'count': 499},
    {'product_id': '975529162954', 'keyword': '表带可调整', 'count': 402},
    {'product_id': '975529162954', 'keyword': '使用体验很好', 'count': 361},
    {'product_id': '975529162954', 'keyword': '图片颜色好看', 'count': 243},
]

# 示例评论（包含差评）
sample_reviews = [
    {'product_id': '975529162954', 'content': '非常漂亮。华为真的是非常漂亮了，价格不贵，还这么漂亮且精致，眼前一亮。值得入手，很好。满意。好评哈。', 'is_negative': False},
    {'product_id': '975529162954', 'content': '续航能力：挺好 触控效果：挺好 外观材质：挺好。功能还没使用，给老婆买的，需要注册她自己的华为健康运动账号。', 'is_negative': False},
    {'product_id': '975529162954', 'content': '手表收到了，外观很漂亮，功能也很齐全，就是电池续航没有宣传的那么好，大概能用5天左右。', 'is_negative': False},
    {'product_id': '975529162954', 'content': '外观好看，但是表带有点硬，戴久了手腕不舒服，希望能改进。', 'is_negative': True},
    {'product_id': '975529162954', 'content': '系统有时候会有卡顿，特别是切换表盘的时候，希望后续能优化。', 'is_negative': True},
    {'product_id': '975529162954', 'content': '价格有点贵，功能和其他品牌的手环差不多，性价比一般。', 'is_negative': True},
    {'product_id': '975529162954', 'content': '睡眠监测不太准，有时候明明醒着却显示深度睡眠。', 'is_negative': True},
    {'product_id': '975529162954', 'content': '充电速度有点慢，充满需要2个小时左右。', 'is_negative': True},
]


def insert_sample_data():
    """插入示例数据"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print('开始插入示例数据...\n')
    
    # 插入商品
    print('1. 插入商品数据...')
    for product in sample_products:
        sql = """
            INSERT INTO huawei_products (
                product_id, name, brand, current_price, original_price, discount,
                sales_count, rating_score, review_count, url, image_url,
                release_date, color, connection_type, strap_material, os,
                communication, warranty, dial_shape, case_material, model,
                screen_resolution, charging_mode, health_monitoring, screen_type,
                source, crawl_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                current_price = VALUES(current_price),
                crawl_time = VALUES(crawl_time)
        """
        cursor.execute(sql, (
            product['product_id'], product['name'], product['brand'],
            product['current_price'], product['original_price'], product['discount'],
            product['sales_count'], product['rating_score'], product['review_count'],
            product['url'], product['image_url'], product['release_date'],
            product['color'], product['connection_type'], product['strap_material'],
            product['os'], product['communication'], product['warranty'],
            product['dial_shape'], product['case_material'], product['model'],
            product['screen_resolution'], product['charging_mode'],
            product['health_monitoring'], product['screen_type'],
            'tmall_huawei', datetime.now()
        ))
    
    conn.commit()
    print(f'   [OK] 已插入 {len(sample_products)} 个商品\n')
    
    # 插入关键词
    print('2. 插入评论关键词...')
    for kw in sample_keywords:
        sql = """
            INSERT INTO huawei_review_keywords (product_id, keyword, count, crawl_time)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE count = VALUES(count)
        """
        cursor.execute(sql, (kw['product_id'], kw['keyword'], kw['count'], datetime.now()))
    
    conn.commit()
    print(f'   [OK] 已插入 {len(sample_keywords)} 个关键词\n')
    
    # 插入评论
    print('3. 插入用户评论...')
    negative_count = sum(1 for r in sample_reviews if r['is_negative'])
    for review in sample_reviews:
        sql = """
            INSERT INTO huawei_reviews (product_id, content, is_negative, crawl_time)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (review['product_id'], review['content'], review['is_negative'], datetime.now()))
    
    conn.commit()
    print(f'   [OK] 已插入 {len(sample_reviews)} 条评论（差评 {negative_count} 条）\n')
    
    cursor.close()
    conn.close()
    
    print('=== 示例数据插入完成 ===')
    print(f'商品: {len(sample_products)} 个')
    print(f'关键词: {len(sample_keywords)} 个')
    print(f'评论: {len(sample_reviews)} 条（差评 {negative_count} 条）')


if __name__ == '__main__':
    insert_sample_data()
