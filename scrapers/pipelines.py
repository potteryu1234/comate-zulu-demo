# -*- coding: utf-8 -*-
"""
Scrapy数据管道
包含：数据清洗、去重、标准化、存储
"""
import re
import pymysql
from datetime import datetime
from itemadapter import ItemAdapter


class DataCleaningPipeline:
    """数据清洗管道"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 清洗价格字段
        if adapter.get('price'):
            price_str = str(adapter['price'])
            # 提取数字
            price_match = re.search(r'[\d,]+\.?\d*', price_str)
            if price_match:
                adapter['price'] = price_match.group().replace(',', '')
        
        # 清洗产品名称
        if adapter.get('name'):
            # 去除多余空格
            adapter['name'] = re.sub(r'\s+', ' ', adapter['name']).strip()
        
        # 清洗规格参数
        if adapter.get('specs'):
            # 去除HTML标签
            specs = re.sub(r'<[^\u003e]+>', ' ', adapter['specs'])
            # 去除多余空格
            specs = re.sub(r'\s+', ' ', specs).strip()
            adapter['specs'] = specs
        
        # 清洗评论内容
        if adapter.get('comment'):
            # 去除特殊字符
            comment = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、：；""''（）【】]', ' ', adapter['comment'])
            adapter['comment'] = re.sub(r'\s+', ' ', comment).strip()
        
        return item


class DuplicateFilterPipeline:
    """去重管道"""
    
    def __init__(self):
        self.seen_products = set()
        self.seen_reviews = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 产品去重（基于URL或名称+品牌）
        if adapter.get('url'):
            item_id = adapter['url']
            if item_id in self.seen_products:
                spider.logger.debug(f'重复产品已过滤: {adapter.get("name", "")}')
                return None
            self.seen_products.add(item_id)
        
        # 评论去重（基于评论内容哈希）
        if adapter.get('comment'):
            comment_hash = hash(adapter['comment'])
            if comment_hash in self.seen_reviews:
                spider.logger.debug('重复评论已过滤')
                return None
            self.seen_reviews.add(comment_hash)
        
        return item


class DatabasePipeline:
    """数据库存储管道"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.cursor = None
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_config=crawler.settings.get('DB_CONFIG')
        )
    
    def open_spider(self, spider):
        """爬虫启动时连接数据库"""
        try:
            self.conn = pymysql.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            spider.logger.info('数据库连接成功')
        except Exception as e:
            spider.logger.error(f'数据库连接失败: {e}')
    
    def close_spider(self, spider):
        """爬虫关闭时断开连接"""
        if self.conn:
            self.conn.close()
            spider.logger.info('数据库连接已关闭')
    
    def process_item(self, item, spider):
        """处理并存储数据"""
        if not self.conn:
            spider.logger.error('数据库未连接')
            return item
        
        adapter = ItemAdapter(item)
        
        try:
            # 存储产品信息
            if adapter.get('name') and not adapter.get('comment'):
                self._save_product(adapter, spider)
            
            # 存储评论信息
            if adapter.get('comment'):
                self._save_review(adapter, spider)
            
            # 存储华为商品信息
            if adapter.get('product_id') and adapter.get('name') and not adapter.get('keyword') and not adapter.get('content'):
                self._save_huawei_product(adapter, spider)
            
            # 存储华为评论关键词
            if adapter.get('keyword'):
                self._save_review_keywords(adapter, spider)
            
            # 存储华为评论
            if adapter.get('content') and adapter.get('product_id'):
                self._save_huawei_review(adapter, spider)
            
            self.conn.commit()
        except Exception as e:
            spider.logger.error(f'数据存储失败: {e}')
            self.conn.rollback()
        
        return item
    
    def _save_product(self, adapter, spider):
        """保存产品信息"""
        sql = """
            INSERT INTO wristbands (brand, name, price, intro, keywords, features, specs, url, image_url, rating)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            price = VALUES(price),
            specs = VALUES(specs),
            image_url = VALUES(image_url),
            rating = VALUES(rating)
        """
        self.cursor.execute(sql, (
            adapter.get('brand', ''),
            adapter.get('name', ''),
            adapter.get('price', ''),
            adapter.get('intro', ''),
            adapter.get('keywords', ''),
            adapter.get('features', ''),
            adapter.get('specs', ''),
            adapter.get('url', ''),
            adapter.get('image_url', ''),
            adapter.get('rating', '')
        ))
    
    def _save_review(self, adapter, spider):
        """保存评论信息"""
        # 先查找产品ID
        product_name = adapter.get('product_name', '')
        if not product_name:
            return
        
        self.cursor.execute(
            "SELECT id FROM wristbands WHERE name LIKE %s LIMIT 1",
            (f'%{product_name}%',)
        )
        result = self.cursor.fetchone()
        
        if result:
            wristband_id = result[0]
            sql = """
                INSERT INTO reviews (wristband_id, rating, comment)
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(sql, (
                wristband_id,
                adapter.get('rating', ''),
                adapter.get('comment', '')
            ))
    
    def _save_huawei_product(self, adapter, spider):
        """保存华为商品信息"""
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
                original_price = VALUES(original_price),
                discount = VALUES(discount),
                sales_count = VALUES(sales_count),
                rating_score = VALUES(rating_score),
                review_count = VALUES(review_count),
                image_url = VALUES(image_url),
                crawl_time = VALUES(crawl_time)
        """
        self.cursor.execute(sql, (
            adapter.get('product_id', ''),
            adapter.get('name', ''),
            adapter.get('brand', ''),
            adapter.get('current_price', None),
            adapter.get('original_price', None),
            adapter.get('discount', ''),
            adapter.get('sales_count', ''),
            adapter.get('rating_score', None),
            adapter.get('review_count', ''),
            adapter.get('url', ''),
            adapter.get('image_url', ''),
            adapter.get('release_date', None),
            adapter.get('color', ''),
            adapter.get('connection_type', ''),
            adapter.get('strap_material', ''),
            adapter.get('os', ''),
            adapter.get('communication', ''),
            adapter.get('warranty', ''),
            adapter.get('dial_shape', ''),
            adapter.get('case_material', ''),
            adapter.get('model', ''),
            adapter.get('screen_resolution', ''),
            adapter.get('charging_mode', ''),
            adapter.get('health_monitoring', ''),
            adapter.get('screen_type', ''),
            adapter.get('source', 'tmall_huawei'),
            adapter.get('crawl_time', datetime.now())
        ))
    
    def _save_review_keywords(self, adapter, spider):
        """保存评论关键词"""
        sql = """
            INSERT INTO huawei_review_keywords (product_id, keyword, count, percentage, crawl_time)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                count = VALUES(count),
                percentage = VALUES(percentage),
                crawl_time = VALUES(crawl_time)
        """
        self.cursor.execute(sql, (
            adapter.get('product_id', ''),
            adapter.get('keyword', ''),
            adapter.get('count', 0),
            adapter.get('percentage', None),
            adapter.get('crawl_time', datetime.now())
        ))
    
    def _save_huawei_review(self, adapter, spider):
        """保存华为评论"""
        sql = """
            INSERT INTO huawei_reviews (product_id, content, is_negative, crawl_time)
            VALUES (%s, %s, %s, %s)
        """
        self.cursor.execute(sql, (
            adapter.get('product_id', ''),
            adapter.get('content', ''),
            adapter.get('is_negative', False),
            adapter.get('crawl_time', datetime.now())
        ))


class DataValidationPipeline:
    """数据验证管道"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 验证必填字段
        if not adapter.get('name'):
            spider.logger.warning('产品名称缺失，跳过')
            return None
        
        # 验证价格格式
        if adapter.get('price'):
            try:
                price = float(adapter['price'])
                if price < 0 or price > 100000:
                    spider.logger.warning(f'价格异常: {price}')
                    adapter['price'] = ''
            except:
                adapter['price'] = ''
        
        # 验证评论长度
        if adapter.get('comment') and len(adapter['comment']) < 5:
            spider.logger.debug('评论过短，跳过')
            return None
        
        return item
