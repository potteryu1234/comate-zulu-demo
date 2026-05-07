# -*- coding: utf-8 -*-
"""
爬取剩余品牌：iQOO、苹果、dido
苹果产品做筛选：名字相似、评分和点评数一样则跳过
"""
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import random
import re
from difflib import SequenceMatcher

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-proxy-server')
    options.add_argument('--proxy-server="direct://"')
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    service = Service()
    return webdriver.Chrome(service=service, options=options)

def get_brand_products(driver, brand_url, brand_name, max_pages=5):
    """获取品牌产品列表"""
    products = []
    base_url = brand_url.rstrip('/')
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}/" if page == 1 else f"{base_url}/{page}.html"
        print(f"  Loading page {page}: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for pic in soup.select('.pic'):
            href = pic.get('href', '')
            if 'index' not in href or '.shtml' not in href:
                continue
            
            img = pic.find('img')
            name = img.get('alt', '') if img else ''
            img_url = img.get('src', '') if img else ''
            
            # 获取价格
            price = ''
            parent = pic.find_parent()
            if parent:
                price_elem = parent.find(string=re.compile(r'参考价|￥'))
                if price_elem:
                    price_match = re.search(r'￥([\d,]+)', price_elem)
                    if price_match:
                        price = price_match.group(1)
            
            # 获取评分和点评数
            rating = ''
            review_count = ''
            score_elem = parent.select_one('.score, .rating') if parent else None
            if score_elem:
                rating = score_elem.get_text(strip=True)
            count_elem = parent.select_one('.comment-count, .review-count') if parent else None
            if count_elem:
                review_count = count_elem.get_text(strip=True)
            
            if name:
                full_url = href if href.startswith('http') else f"https:{href}" if href.startswith('//') else f"https://detail.zol.com.cn{href}"
                full_img_url = img_url if img_url.startswith('http') else f"https:{img_url}" if img_url.startswith('//') else img_url
                products.append({
                    'brand': brand_name,
                    'name': name,
                    'price': price,
                    'url': full_url,
                    'image_url': full_img_url,
                    'rating': rating,
                    'review_count': review_count
                })
        
        if len(products) >= page * 50:
            break
        
        next_btn = soup.select_one('.next-page, .next')
        disabled_next = soup.select_one('.next-page.disabled, .next.disabled')
        if disabled_next or not next_btn:
            break
    
    return products

def is_similar(name1, name2):
    """判断两个产品名是否相似"""
    # 提取核心名称（去掉尺寸、颜色等）
    core1 = re.sub(r'[\(\)（）\[\]\/\d]+.*$', '', name1).strip()
    core2 = re.sub(r'[\(\)（）\[\]\/\d]+.*$', '', name2).strip()
    similarity = SequenceMatcher(None, core1, core2).ratio()
    return similarity > 0.8

def filter_apple_products(products):
    """筛选苹果产品：名字相似、评分和点评数一样则跳过"""
    filtered = []
    seen = {}  # 用核心名称+评分+点评数作为key
    
    for p in products:
        core_name = re.sub(r'[\(\)（）\[\]\/\d]+.*$', '', p['name']).strip()
        key = f"{core_name}_{p['rating']}_{p['review_count']}"
        
        if key in seen:
            print(f"    [SKIP] 相似产品: {p['name'][:50]} (与 {seen[key]['name'][:50]} 相似)")
            continue
        
        # 检查是否与已保存的相似
        is_dup = False
        for saved_key, saved in seen.items():
            if is_similar(p['name'], saved['name']) and p['rating'] == saved['rating'] and p['review_count'] == saved['review_count']:
                print(f"    [SKIP] 相似产品: {p['name'][:50]} (评分:{p['rating']}, 点评:{p['review_count']})")
                is_dup = True
                break
        
        if not is_dup:
            seen[key] = p
            filtered.append(p)
    
    return filtered

def get_product_detail(driver, url):
    """获取产品详情"""
    driver.get(url)
    time.sleep(random.uniform(2, 4))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    title = soup.select_one('h1, .product-title')
    name = title.get_text(strip=True) if title else ''
    
    intro = soup.select_one('.summary, .description')
    intro_text = intro.get_text(strip=True) if intro else ''
    
    # 获取评分
    rating = ''
    rating_elem = soup.select_one('.score, .rating')
    if rating_elem:
        rating = rating_elem.get_text(strip=True)
    
    return {
        'name': name[:200] or 'Unknown',
        'intro': intro_text[:2000],
        'rating': rating
    }

def get_reviews(driver, url):
    """获取评论"""
    match = re.search(r'index(\d+)\.shtml', url)
    if not match:
        return []
    
    product_id = match.group(1)
    review_url = f"https://detail.zol.com.cn/GPSwatch/{product_id}/review.shtml"
    
    driver.get(review_url)
    time.sleep(random.uniform(2, 4))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    reviews = []
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if text and len(text) > 20 and '提示：' not in text:
            reviews.append(text[:1000])
    
    return reviews if reviews else ['[无用户评论]']

def save_to_db(cursor, conn, product, detail, reviews):
    try:
        cursor.execute("""
            INSERT INTO wristbands (brand, name, price, intro, keywords, features, specs, url, image_url, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            product['brand'],
            detail['name'],
            product['price'],
            detail.get('intro', ''),
            '', '', '',
            product['url'],
            product.get('image_url', ''),
            detail.get('rating', product.get('rating', ''))
        ))
        wristband_id = cursor.lastrowid
        
        for review in reviews:
            cursor.execute("""
                INSERT INTO reviews (wristband_id, rating, comment)
                VALUES (%s, %s, %s)
            """, (wristband_id, '', review))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Save error: {e}")
        conn.rollback()
        return False

def main():
    print("=" * 60)
    print("爬取剩余品牌: iQOO、苹果、dido")
    print("=" * 60)
    
    brands = [
        {'name': 'iQOO', 'url': 'https://detail.zol.com.cn/gpswatch/iqoo/'},
        {'name': 'dido', 'url': 'https://detail.zol.com.cn/gpswatch/dido/'},
        {'name': '苹果', 'url': 'https://detail.zol.com.cn/gpswatch/apple/'},
    ]
    
    driver = init_driver()
    conn = pymysql.connect(**DB_CONFIG, database='zol_wristband')
    cursor = conn.cursor()
    
    total_saved = 0
    
    try:
        for brand in brands:
            print(f"\n[Brand] {brand['name']}")
            products = get_brand_products(driver, brand['url'], brand['name'])
            print(f"  找到 {len(products)} 个产品")
            
            # 苹果品牌做筛选
            if brand['name'] == '苹果':
                products = filter_apple_products(products)
                print(f"  筛选后剩余 {len(products)} 个产品")
            
            for idx, product in enumerate(products, 1):
                print(f"  [{idx}/{len(products)}] {product['name'][:50]}...")
                
                detail = get_product_detail(driver, product['url'])
                reviews = get_reviews(driver, product['url'])
                
                if save_to_db(cursor, conn, product, detail, reviews):
                    print(f"      [OK] Saved, reviews: {len(reviews)}")
                    total_saved += 1
                else:
                    print(f"      [FAIL]")
                
                time.sleep(random.uniform(1, 2))
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        cursor.close()
        conn.close()
    
    print("\n" + "=" * 60)
    print(f"Done! Total products saved: {total_saved}")
    print("=" * 60)

if __name__ == "__main__":
    main()