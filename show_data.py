# -*- coding: utf-8 -*-
import pymysql

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

def show_data():
    conn = pymysql.connect(**DB_CONFIG, database='zol_wristband')
    cursor = conn.cursor()

    # 统计
    cursor.execute("SELECT COUNT(*) FROM wristbands")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT brand) FROM wristbands")
    total_brands = cursor.fetchone()[0]

    print("=" * 80)
    print("ZOL 智能手表爬虫数据概览")
    print("=" * 80)
    print(f"品牌数量: {total_brands}")
    print(f"产品数量: {total_products}")
    print(f"评论数量: {total_reviews}")
    print()

    # 按品牌统计
    if total_products > 0:
        print("-" * 80)
        print("各品牌产品数量:")
        print("-" * 80)
        cursor.execute("""
            SELECT brand, COUNT(*) as cnt
            FROM wristbands
            GROUP BY brand
            ORDER BY cnt DESC
            LIMIT 15
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]:15s} : {row[1]:3d} 款")
        print()

        # 显示最近10个产品
        print("-" * 80)
        print("最近爬取的10个产品:")
        print("-" * 80)
        cursor.execute("""
            SELECT brand, name, price, created_at
            FROM wristbands
            ORDER BY id DESC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            brand, name, price, created = row
            price_str = f"￥{price}" if price else "暂无价格"
            print(f"  [{brand}] {name[:40]:40s} {price_str:10s}")
        print()

        # 显示有评论的产品
        cursor.execute("""
            SELECT w.brand, w.name, COUNT(r.id) as review_count
            FROM wristbands w
            JOIN reviews r ON w.id = r.wristband_id
            WHERE r.comment != '[无用户评论]'
            GROUP BY w.id
            ORDER BY review_count DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        if rows:
            print("-" * 80)
            print("评论最多的10个产品:")
            print("-" * 80)
            for row in rows:
                print(f"  [{row[0]}] {row[1][:40]:40s} 评论: {row[2]}条")
            print()

        # 显示无评论的产品数量
        cursor.execute("""
            SELECT COUNT(DISTINCT w.id)
            FROM wristbands w
            JOIN reviews r ON w.id = r.wristband_id
            WHERE r.comment = '[无用户评论]'
        """)
        no_review_count = cursor.fetchone()[0]
        if no_review_count > 0:
            print(f"无评论的产品: {no_review_count} 款")

    cursor.close()
    conn.close()
    print("=" * 80)

if __name__ == "__main__":
    show_data()