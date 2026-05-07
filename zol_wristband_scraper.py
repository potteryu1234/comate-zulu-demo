# -*- coding: utf-8 -*-
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import random
import re
import json
import os

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

# 进度记录文件
PROGRESS_FILE = 'scraper_progress.json'

def load_progress():
    """加载进度记录"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_update': '',
        'completed_brands': [],
        'completed_product_ids': [],
        'pending_brands': [],
        'total_products': 0,
        'total_reviews': 0
    }

def save_progress(progress):
    """保存进度记录"""
    progress['last_update'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def extract_product_id(url):
    """从URL中提取产品ID (index后面的数字)"""
    match = re.search(r'index(\d+)\.shtml', url)
    if match:
        return match.group(1)
    return None

def init_database():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS zol_wristband CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute("USE zol_wristband")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wristbands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand VARCHAR(100),
            name VARCHAR(255) NOT NULL,
            price VARCHAR(50),
            intro TEXT,
            keywords TEXT,
            features TEXT,
            specs TEXT,
            url VARCHAR(500),
            image_url TEXT,
            rating VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            wristband_id INT,
            rating VARCHAR(20),
            comment TEXT,
            FOREIGN KEY (wristband_id) REFERENCES wristbands(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized")

def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_brand_list(driver):
    """从底部获取品牌列表"""
    url = "https://detail.zol.com.cn/gpswatch/"
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    brands = []

    # 查找品牌链接
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        match = re.search(r'/gpswatch/([^/]+)/?$', href)
        if match:
            brand_name = match.group(1)
            if brand_name and brand_name not in ['', 'gpswatch']:
                full_url = href if href.startswith('http') else f"https://detail.zol.com.cn{href}"
                text = a.get_text(strip=True)
                brand_cn = text.replace('智能手表', '').replace('(', '').replace(')', '').split('/')[0] if text else brand_name
                brands.append({
                    'name_en': brand_name,
                    'name_cn': brand_cn,
                    'url': full_url.rstrip('/')
                })

    # 去重
    seen = set()
    unique = []
    for b in brands:
        if b['name_en'] not in seen:
            seen.add(b['name_en'])
            unique.append(b)

    print(f"Found {len(unique)} brands")
    return unique

def get_brand_products(driver, brand_url, brand_name, max_pages=5):
    """获取某品牌的所有产品 (每页最多50款, 最多5页)"""
    products = []
    base_url = brand_url.rstrip('/')

    for page in range(1, max_pages + 1):
        if page == 1:
            url = f"{base_url}/"
        else:
            url = f"{base_url}/{page}.html"

        print(f"  Loading page {page}: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 查找产品链接 (.pic 类就是 a 标签)
        for pic in soup.select('.pic'):
            href = pic.get('href', '')
            # 匹配 /GPSwatch/index2141422.shtml 格式
            if 'index' not in href or '.shtml' not in href:
                continue

            # 获取产品名称 (从 img alt)
            img = pic.find('img')
            name = img.get('alt', '') if img else ''
            img_url = img.get('src', '') if img else ''

            # 获取价格 (从父元素 li 中查找)
            price = ''
            parent = pic.find_parent()
            if parent:
                price_elem = parent.find(string=re.compile(r'参考价|￥'))
                if price_elem:
                    price_match = re.search(r'￥([\d,]+)', price_elem)
                    if price_match:
                        price = price_match.group(1)

            if name:
                full_url = href if href.startswith('http') else f"https:{href}" if href.startswith('//') else f"https://detail.zol.com.cn{href}"
                full_img_url = img_url if img_url.startswith('http') else f"https:{img_url}" if img_url.startswith('//') else img_url
                products.append({
                    'brand': brand_name,
                    'name': name,
                    'price': price,
                    'url': full_url,
                    'image_url': full_img_url
                })

            # 每页最多50款
            if len(products) >= page * 50:
                print(f"  Reached 50 products limit for page {page}")
                break

        # 检查是否有下一页
        next_btn = soup.select_one('.next-page, .next')
        disabled_next = soup.select_one('.next-page.disabled, .next.disabled')
        if disabled_next or not next_btn:
            print(f"  No more pages for {brand_name}")
            break

    print(f"  Total products for {brand_name}: {len(products)}")
    return products

def get_product_detail(driver, base_url):
    """获取产品详情（从综述页、参数页、图片页抓取）"""

    # 从 base_url 提取类别ID和产品ID
    # 支持两种URL格式:
    # 1. https://detail.zol.com.cn/2142/index2141422.shtml (类别ID + 产品ID)
    # 2. https://detail.zol.com.cn/GPSwatch/index2141422.shtml (类别名 + 产品ID)

    category_id = None
    product_id = None

    # 尝试匹配格式1: /类别ID/index产品ID.shtml
    match1 = re.search(r'/(\d+)/index(\d+)\.shtml', base_url)
    if match1:
        category_id = match1.group(1)
        product_id = match1.group(2)
    else:
        # 尝试匹配格式2: /类别名/index产品ID.shtml
        match2 = re.search(r'/(\w+)/index(\d+)\.shtml', base_url)
        if match2:
            category_id = match2.group(1)  # GPSwatch
            # 从类别名推断类别ID
            category_map = {'gpswatch': '2142'}
            category_id = category_map.get(category_id.lower(), category_id)
            product_id = match2.group(2)

    if category_id and product_id:
        base_domain = "https://detail.zol.com.cn"
    else:
        print(f"  [WARN] Failed to parse URL: {base_url}")
        return {'name': 'Unknown', 'intro': '', 'specs': '', 'keywords': '', 'image_urls': '', 'has_reviews': False}

    # 1. 抓取综述页（默认页）
    driver.get(base_url)
    time.sleep(random.uniform(2, 4))
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # 标题
    title = soup.select_one('h1, .product-title, .goods-name')
    name = title.get_text(strip=True) if title else ''

    # 简介 - 从页面描述或特色功能获取
    intro_text = ''
    # 尝试多种选择器
    intro_selectors = ['.summary', '.description', '.intro', '.product-desc', '[class*="summary"]', '[class*="desc"]']
    for selector in intro_selectors:
        intro_elem = soup.select_one(selector)
        if intro_elem:
            intro_text = intro_elem.get_text(strip=True)
            if intro_text:
                break
    
    # 如果没有找到简介，尝试从产品特色获取
    if not intro_text:
        feature_elems = soup.select('.feature-list li, .highlight li, .product-feature li')
        if feature_elems:
            intro_text = '；'.join([elem.get_text(strip=True) for elem in feature_elems[:5]])

    # 关键词/特色
    keywords = []
    for tag in soup.select('.tag, .keyword, .feature-tag, .product-tag'):
        keywords.append(tag.get_text(strip=True))
    keywords_str = ','.join(keywords)

    # 检查是否有点评数和评分
    review_count_elem = soup.select_one('.review-count, .comment-count, .pingfen, .score-num')
    review_count = review_count_elem.get_text(strip=True) if review_count_elem else '0人点评'
    
    # 获取评分
    rating = ''
    rating_elem = soup.select_one('.score, .rating, .star-num, [class*="score"]')
    if rating_elem:
        rating = rating_elem.get_text(strip=True)

    if '0人' in review_count or review_count == '':
        has_reviews = False
        keywords_str = '[无点评] ' + keywords_str
    else:
        has_reviews = True

    # 2. 抓取参数页
    param_url = f"{base_domain}/{category_id}/{product_id}/param.shtml"
    driver.get(param_url)
    time.sleep(random.uniform(2, 3))
    soup_param = BeautifulSoup(driver.page_source, 'html.parser')

    specs = []
    
    # 尝试多种参数表格选择器
    # 1. 标准参数表格
    for tr in soup_param.select('.param-table tr, table tr, .parameter-table tr'):
        tds = tr.find_all('td')
        if len(tds) >= 2:
            spec_name = tds[0].get_text(strip=True)
            spec_value = tds[1].get_text(strip=True)
            if spec_name and spec_value and spec_value != '暂无数据':
                specs.append(f"{spec_name}: {spec_value}")
    
    # 2. 如果表格为空，尝试从详细参数区域提取
    if not specs:
        # 查找所有参数项
        param_items = soup_param.select('.param-item, .parameter-item, dl dt, .param-list dt')
        for item in param_items:
            # 获取参数名
            param_name = item.get_text(strip=True)
            # 获取对应的参数值（下一个兄弟元素或dd标签）
            param_value_elem = item.find_next_sibling(['dd', 'dt']) or item.find_next('dd')
            if param_value_elem:
                param_value = param_value_elem.get_text(strip=True)
                if param_name and param_value and param_value != '暂无数据':
                    specs.append(f"{param_name}: {param_value}")
    
    # 3. 尝试从dl/dt/dd结构提取
    if not specs:
        for dl in soup_param.find_all('dl'):
            dt = dl.find('dt')
            dd = dl.find('dd')
            if dt and dd:
                spec_name = dt.get_text(strip=True)
                spec_value = dd.get_text(strip=True)
                if spec_name and spec_value and spec_value != '暂无数据':
                    specs.append(f"{spec_name}: {spec_value}")
    
    specs_str = '; '.join(specs[:50])  # 增加到50条参数

    # 3. 抓取图片页（取前5张）
    pic_url = f"{base_domain}/{category_id}/{product_id}/pic.shtml"
    driver.get(pic_url)
    time.sleep(random.uniform(2, 3))
    soup_pic = BeautifulSoup(driver.page_source, 'html.parser')

    image_urls = []
    # 查找所有产品图片，排除icon和广告
    for img in soup_pic.find_all('img'):
        src = img.get('src', '')
        alt = img.get('alt', '')
        # 筛选产品图片：包含'product'或alt文本为'外观图'等
        if src and ('product' in src or ('外观图' in alt and len(src) > 50)):
            full_url = src if src.startswith('http') else f"https:{src}" if src.startswith('//') else f"{base_domain}{src}"
            if full_url not in image_urls:  # 去重
                image_urls.append(full_url)
    image_urls_str = ','.join(image_urls[:5])

    # 获取价格（从综述页或参数页）
    price = ''
    price_elem = soup.select_one('.price, .reference-price, [class*="price"], [class*="Price"]')
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        price_match = re.search(r'[￥¥]([\d,]+)', price_text)
        if price_match:
            price = price_match.group(1)
    
    # 如果综述页没有价格，尝试从参数页获取
    if not price:
        price_elem_param = soup_param.select_one('.price, .reference-price, [class*="price"]')
        if price_elem_param:
            price_text_param = price_elem_param.get_text(strip=True)
            price_match_param = re.search(r'[￥¥]([\d,]+)', price_text_param)
            if price_match_param:
                price = price_match_param.group(1)

    return {
        'name': name[:200] or 'Unknown',
        'intro': intro_text[:2000],
        'specs': specs_str[:3000],
        'keywords': keywords_str[:500],
        'image_urls': image_urls_str[:1000],
        'has_reviews': has_reviews,
        'rating': rating,
        'price': price
    }

def get_reviews(driver, product_url, wristband_id):
    """获取评论"""
    # 从 product_url 提取类别ID和产品ID
    # 支持两种URL格式
    category_id = None
    product_id = None

    # 尝试匹配格式1: /类别ID/index产品ID.shtml
    match1 = re.search(r'/(\d+)/index(\d+)\.shtml', product_url)
    if match1:
        category_id = match1.group(1)
        product_id = match1.group(2)
    else:
        # 尝试匹配格式2: /类别名/index产品ID.shtml
        match2 = re.search(r'/(\w+)/index(\d+)\.shtml', product_url)
        if match2:
            category_id = match2.group(1)
            # 从类别名推断类别ID
            category_map = {'gpswatch': '2142'}
            category_id = category_map.get(category_id.lower(), category_id)
            product_id = match2.group(2)

    if category_id and product_id:
        review_url = f"https://detail.zol.com.cn/{category_id}/{product_id}/review.shtml"
    else:
        return []

    driver.get(review_url)
    time.sleep(random.uniform(2, 4))
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    reviews = []
    # 评论页结构：直接显示的文本段落
    # 查找所有可能包含评论的文本段落
    for p in soup.find_all('p'):
        comment_text = p.get_text(strip=True)
        # 筛选有效的评论（排除太短或明显是页面元素的文本）
        if comment_text and len(comment_text) > 20 and comment_text not in [
            '提示：图片部分来源于网络，如有侵权请联系删除。',
            '颜色：',
            '产品型号',
            '外观图',
            '产品图片',
            '相关产品图片',
            '精选推荐',
            '大家都在看'
        ]:
            reviews.append({
                'wristband_id': wristband_id,
                'rating': '',
                'comment': comment_text[:1000]
            })

    # 如果没有评论，添加一条标注记录
    if not reviews:
        reviews.append({
            'wristband_id': wristband_id,
            'rating': '',
            'comment': '[无用户评论]'
        })

    return reviews

def save_to_db(cursor, conn, product, detail, reviews):
    try:
        # 使用详情页获取的价格（如果列表页没有）
        final_price = product.get('price', '') or detail.get('price', '')
        
        cursor.execute("""
            INSERT INTO wristbands (brand, name, price, intro, keywords, features, specs, url, image_url, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            product['brand'],
            detail['name'],
            final_price,
            detail.get('intro', ''),
            detail.get('keywords', ''),
            '',
            detail.get('specs', ''),
            product['url'],
            detail.get('image_urls', product.get('image_url', '')),
            detail.get('rating', '')
        ))
        wristband_id = cursor.lastrowid

        for review in reviews:
            cursor.execute("""
                INSERT INTO reviews (wristband_id, rating, comment)
                VALUES (%s, %s, %s)
            """, (
                wristband_id,
                review['rating'],
                review['comment']
            ))

        conn.commit()
        return True
    except Exception as e:
        print(f"Save error: {e}")
        conn.rollback()
        return False

# 定义要爬取的品牌列表（苹果放在最后）
TARGET_BRANDS = [
    {'name_cn': '华为', 'name_en': 'huawei', 'url': 'https://detail.zol.com.cn/gpswatch/huawei'},
    {'name_cn': '三星', 'name_en': 'samsung', 'url': 'https://detail.zol.com.cn/gpswatch/samsung'},
    {'name_cn': '小天才', 'name_en': 'xiaotiancai', 'url': 'https://detail.zol.com.cn/gpswatch/xiaotiancai'},
    {'name_cn': '荣耀', 'name_en': 'honor', 'url': 'https://detail.zol.com.cn/gpswatch/honor'},
    {'name_cn': 'OPPO', 'name_en': 'oppo', 'url': 'https://detail.zol.com.cn/gpswatch/oppo'},
    {'name_cn': '华米', 'name_en': 'amazfit', 'url': 'https://detail.zol.com.cn/gpswatch/amazfit'},
    {'name_cn': 'Ticwatch', 'name_en': 'ticwatch', 'url': 'https://detail.zol.com.cn/gpswatch/ticwatch'},
    {'name_cn': '小米', 'name_en': 'xiaomi', 'url': 'https://detail.zol.com.cn/gpswatch/xiaomi'},
    {'name_cn': 'garmin', 'name_en': 'garmin', 'url': 'https://detail.zol.com.cn/gpswatch/garmin'},
    {'name_cn': '360', 'name_en': '360', 'url': 'https://detail.zol.com.cn/gpswatch/360'},
    {'name_cn': '红米', 'name_en': 'redmi', 'url': 'https://detail.zol.com.cn/gpswatch/redmi'},
    {'name_cn': 'vivo', 'name_en': 'vivo', 'url': 'https://detail.zol.com.cn/gpswatch/vivo'},
    {'name_cn': '颂拓', 'name_en': 'suunto', 'url': 'https://detail.zol.com.cn/gpswatch/suunto'},
    {'name_cn': 'iQOO', 'name_en': 'iqoo', 'url': 'https://detail.zol.com.cn/gpswatch/iqoo'},
    {'name_cn': 'dido', 'name_en': 'dido', 'url': 'https://detail.zol.com.cn/gpswatch/dido'},
    # 苹果品牌放在最后爬取
    {'name_cn': '苹果', 'name_en': 'apple', 'url': 'https://detail.zol.com.cn/gpswatch/apple'},
]

def main():
    print("=" * 60)
    print("ZOL GPS Watch Scraper - By Brand")
    print("=" * 60)

    # 加载进度
    progress = load_progress()
    print(f"\n[进度] 已爬取品牌: {progress.get('completed_brands', [])}")
    print(f"[进度] 已爬取产品数: {progress.get('total_products', 0)}")
    print(f"[进度] 已爬取产品ID: {len(progress.get('completed_product_ids', []))} 个")

    init_database()
    driver = init_driver()

    try:
        conn = pymysql.connect(**DB_CONFIG, database='zol_wristband')
        cursor = conn.cursor()

        total_saved = progress.get('total_products', 0)
        completed_brands = progress.get('completed_brands', [])
        completed_product_ids = set(progress.get('completed_product_ids', []))

        for brand in TARGET_BRANDS:
            # 跳过已完成的品牌
            if brand['name_cn'] in completed_brands:
                print(f"\n[跳过] {brand['name_cn']} 已爬取完成")
                continue

            print(f"\n[Brand] {brand['name_cn']} ({brand['name_en']})")

            products = get_brand_products(driver, brand['url'], brand['name_cn'], max_pages=5)
            brand_saved = 0

            for idx, product in enumerate(products, 1):  # 爬取所有产品（每页最多50，最多5页=250个）
                # 提取产品ID
                product_id = extract_product_id(product['url'])
                
                # 跳过已爬取的产品
                if product_id and product_id in completed_product_ids:
                    print(f"  [{idx}/{len(products)}] 跳过已爬取产品 ID:{product_id}")
                    continue

                print(f"  [{idx}/{len(products)}] ID:{product_id} {product['name'][:50]}...")

                detail = get_product_detail(driver, product['url'])
                reviews = get_reviews(driver, product['url'], None)

                save_result = save_to_db(cursor, conn, product, detail, reviews)
                if save_result:
                    print(f"      [OK] Saved ID:{product_id}, reviews: {len(reviews)}, rating: {detail.get('rating', 'N/A')}")
                    total_saved += 1
                    brand_saved += 1
                    
                    # 记录已爬取的产品ID
                    if product_id:
                        completed_product_ids.add(product_id)
                        
                    # 实时保存进度
                    progress['total_products'] = total_saved
                    progress['completed_product_ids'] = list(completed_product_ids)
                    save_progress(progress)

                else:
                    print(f"      [FAIL] ID:{product_id}")

                time.sleep(random.uniform(1, 2))

            # 品牌完成后记录
            if brand_saved > 0:
                completed_brands.append(brand['name_cn'])
                progress['completed_brands'] = completed_brands
                progress['total_products'] = total_saved
                progress['completed_product_ids'] = list(completed_product_ids)
                save_progress(progress)
                print(f"\n[完成] {brand['name_cn']} 品牌爬取完成，新增 {brand_saved} 个产品")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        # 异常时保存进度
        progress['total_products'] = total_saved
        progress['completed_product_ids'] = list(completed_product_ids)
        save_progress(progress)
        print("\n[保存] 异常退出，进度已保存")
    finally:
        driver.quit()

    print("\n" + "=" * 60)
    print(f"Done! Total products saved: {total_saved}")
    print(f"Completed brands: {completed_brands}")
    print(f"Completed product IDs: {len(completed_product_ids)}")
    print("=" * 60)

if __name__ == "__main__":
    main()