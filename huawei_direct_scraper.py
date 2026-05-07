# -*- coding: utf-8 -*-
"""
华为天猫智能穿戴直接爬取脚本
使用Playwright直接访问并提取数据
"""
import asyncio
import re
import json
import pymysql
from datetime import datetime
from playwright.async_api import async_playwright

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'zol_wristband',
    'charset': 'utf8mb4'
}


class HuaweiDirectScraper:
    def __init__(self):
        self.products = []
        self.conn = None
        self.cursor = None
    
    async def init_db(self):
        """初始化数据库连接"""
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        print('数据库连接成功')
    
    async def scrape_list_page(self, page):
        """爬取列表页"""
        url = 'https://huaweistore.tmall.com/category-1201482782-1662553168.htm?search=y&catName=%D6%C7%C4%DC%B4%A9%B4%F7'
        print(f'访问列表页: {url}')
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 获取页面内容
            content = await page.content()
            
            # 提取商品ID
            product_ids = []
            
            # 从链接中提取
            links = re.findall(r'href="(//detail\.tmall\.com/item\.htm[^"]+)"', content)
            for link in links:
                match = re.search(r'id=(\d+)', link)
                if match:
                    pid = match.group(1)
                    if pid not in product_ids:
                        product_ids.append(pid)
            
            # 从脚本中提取
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
            for script in scripts:
                matches = re.findall(r'itemId["\']?\s*[:=]\s*["\']?(\d+)', script)
                for pid in matches:
                    if pid not in product_ids:
                        product_ids.append(pid)
            
            print(f'发现 {len(product_ids)} 个商品ID')
            return product_ids[:8]  # 限制前8个
            
        except Exception as e:
            print(f'列表页爬取失败: {e}')
            return []
    
    async def scrape_product_detail(self, page, product_id):
        """爬取商品详情"""
        url = f'https://detail.tmall.com/item.htm?id={product_id}'
        print(f'\n爬取商品 {product_id}: {url}')
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)
            
            # 获取页面内容
            content = await page.content()
            
            # 提取商品名称
            name_match = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)', content)
            name = name_match.group(1) if name_match else ''
            if not name:
                title_match = re.search(r'<title>(.*?)</title>', content)
                if title_match:
                    name = re.sub(r'\s*-\s*天猫.*$', '', title_match.group(1))
            
            print(f'  名称: {name[:60] if name else "未找到"}')
            
            # 提取价格
            price = None
            price_match = re.search(r'"defaultItemPrice"[:\s]*"([^"]+)"', content)
            if price_match:
                price_str = price_match.group(1)
                match = re.search(r'(\d+\.?\d*)', price_str.replace(',', ''))
                if match:
                    price = float(match.group(1))
            
            print(f'  价格: {price}')
            
            # 提取卖家ID
            seller_id = None
            seller_match = re.search(r'sellerId["\']?\s*[:=]\s*["\']?(\d+)', content)
            if seller_match:
                seller_id = seller_match.group(1)
            
            # 提取销量
            sales_match = re.search(r'(已售[\d万+]+|月销[\d万+]+)', content)
            sales_count = sales_match.group(1) if sales_match else ''
            
            # 提取评分
            rating = None
            rating_match = re.search(r'([\d.]+)\s*分', content)
            if rating_match:
                try:
                    rating = float(rating_match.group(1))
                except:
                    pass
            
            # 提取主图
            image = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)', content)
            image_url = image.group(1) if image else ''
            
            # 提取参数
            specs = self._extract_specs(content)
            
            # 保存商品
            product_data = {
                'product_id': product_id,
                'name': name,
                'brand': '华为',
                'current_price': price,
                'original_price': None,
                'discount': '',
                'sales_count': sales_count,
                'rating_score': rating,
                'review_count': '',
                'url': url,
                'image_url': image_url,
                **specs
            }
            
            self._save_product(product_data)
            
            # 提取评论关键词
            keywords = self._extract_keywords(content)
            for kw in keywords:
                self._save_keyword(product_id, kw)
            
            # 获取评论
            if seller_id:
                await self.scrape_reviews(page, product_id, seller_id)
            
            return True
            
        except Exception as e:
            print(f'  商品爬取失败: {e}')
            return False
    
    def _extract_specs(self, content):
        """提取规格参数"""
        specs = {}
        
        # 从脚本中提取props
        props_match = re.search(r'"props"\s*:\s*(\[.*?\])', content, re.DOTALL)
        if props_match:
            try:
                props = json.loads(props_match.group(1))
                for prop in props:
                    if 'name' in prop and 'value' in prop:
                        specs[prop['name']] = prop['value']
            except:
                pass
        
        field_mapping = {
            '上市时间': 'release_date',
            '外观颜色': 'color',
            '连接方式': 'connection_type',
            '表带材质': 'strap_material',
            '操作系统': 'os',
            '通讯类型': 'communication',
            '保修期': 'warranty',
            '表盘形状': 'dial_shape',
            '表壳材质': 'case_material',
            '型号': 'model',
            '屏幕分辨率': 'screen_resolution',
            '充电模式': 'charging_mode',
            '健康监测功能': 'health_monitoring',
            '屏幕类型': 'screen_type',
        }
        
        result = {}
        for cn_key, field_name in field_mapping.items():
            if cn_key in specs:
                value = specs[cn_key]
                if field_name == 'release_date' and value:
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except:
                        pass
                result[field_name] = value
            else:
                result[field_name] = None
        
        return result
    
    def _extract_keywords(self, content):
        """提取评论关键词"""
        keywords = []
        
        # 从脚本中提取
        tag_match = re.search(r'"tagClouds"\s*:\s*(\[.*?\])', content, re.DOTALL)
        if tag_match:
            try:
                tags = json.loads(tag_match.group(1))
                for tag in tags:
                    if 'tag' in tag and 'count' in tag:
                        keywords.append({'keyword': tag['tag'], 'count': tag['count']})
            except:
                pass
        
        return keywords
    
    async def scrape_reviews(self, page, product_id, seller_id):
        """爬取评论"""
        print(f'  获取评论...')
        
        # 先尝试获取差评
        for rate_type in [3, 2, 1]:  # 3=差评, 2=中评, 1=好评
            if len(self.products) >= 20:  # 限制评论数量
                break
            
            url = f'https://rate.tmall.com/list_detail_rate.htm?itemId={product_id}&sellerId={seller_id}&currentPage=1&pageSize=20'
            if rate_type:
                url += f'&rateType={rate_type}'
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                
                # 解析JSONP
                match = re.search(r'\((.*)\)', content, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    reviews = data.get('rateDetail', {}).get('rateList', [])
                    
                    print(f'    类型{rate_type}: 获取 {len(reviews)} 条评论')
                    
                    for review in reviews[:10]:  # 每类型最多10条
                        content_text = review.get('rateContent', '').strip()
                        if content_text:
                            rating = review.get('rate', 0)
                            is_negative = rating <= 2 or rate_type == 3
                            self._save_review(product_id, content_text, is_negative)
                
            except Exception as e:
                print(f'    评论获取失败: {e}')
    
    def _save_product(self, data):
        """保存商品到数据库"""
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
        
        try:
            self.cursor.execute(sql, (
                data['product_id'], data['name'], data['brand'], data['current_price'],
                data['original_price'], data['discount'], data['sales_count'],
                data['rating_score'], data['review_count'], data['url'], data['image_url'],
                data.get('release_date'), data.get('color'), data.get('connection_type'),
                data.get('strap_material'), data.get('os'), data.get('communication'),
                data.get('warranty'), data.get('dial_shape'), data.get('case_material'),
                data.get('model'), data.get('screen_resolution'), data.get('charging_mode'),
                data.get('health_monitoring'), data.get('screen_type'),
                'tmall_huawei', datetime.now()
            ))
            self.conn.commit()
            print(f'  ✓ 商品已保存')
        except Exception as e:
            print(f'  ✗ 保存失败: {e}')
            self.conn.rollback()
    
    def _save_keyword(self, product_id, keyword_data):
        """保存关键词"""
        sql = """
            INSERT INTO huawei_review_keywords (product_id, keyword, count, crawl_time)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE count = VALUES(count)
        """
        try:
            self.cursor.execute(sql, (product_id, keyword_data['keyword'], keyword_data['count'], datetime.now()))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
    
    def _save_review(self, product_id, content, is_negative):
        """保存评论"""
        sql = """
            INSERT INTO huawei_reviews (product_id, content, is_negative, crawl_time)
            VALUES (%s, %s, %s, %s)
        """
        try:
            self.cursor.execute(sql, (product_id, content, is_negative, datetime.now()))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
    
    async def run(self):
        """运行爬虫"""
        print('=== 华为天猫智能穿戴爬虫 ===\n')
        
        await self.init_db()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # 爬取列表页
            product_ids = await self.scrape_list_page(page)
            
            # 爬取每个商品
            success_count = 0
            for pid in product_ids:
                if await self.scrape_product_detail(page, pid):
                    success_count += 1
                await asyncio.sleep(3)  # 延迟
            
            await browser.close()
            
            print(f'\n=== 爬取完成 ===')
            print(f'成功爬取 {success_count}/{len(product_ids)} 个商品')
        
        self.cursor.close()
        self.conn.close()


if __name__ == '__main__':
    scraper = HuaweiDirectScraper()
    asyncio.run(scraper.run())
