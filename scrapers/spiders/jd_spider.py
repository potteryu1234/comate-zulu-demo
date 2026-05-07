# -*- coding: utf-8 -*-
"""
京东智能手环爬虫
爬取产品价格、评价等数据
"""
import scrapy
import json
import re
from datetime import datetime
from urllib.parse import quote
from scrapers.items import WristbandProductItem, WristbandReviewItem


class JDSpider(scrapy.Spider):
    """京东爬虫"""
    name = 'jd'
    allowed_domains = ['jd.com', '3.cn']
    
    # 京东智能手环搜索页
    start_urls = [
        'https://search.jd.com/Search?keyword=智能手环&enc=utf-8',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'COOKIES_ENABLED': True,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_pages = 3  # 最多爬取页数
        self.max_reviews = 10  # 每个产品最多评论数
    
    def parse(self, response):
        """解析搜索列表页"""
        self.logger.info(f'解析京东搜索页: {response.url}')
        
        # 提取产品列表
        products = response.css('.gl-item')
        
        for product in products:
            # 提取产品ID
            sku_id = product.css('::attr(data-sku)').get('')
            
            # 提取产品链接
            product_url = product.css('.p-name a::attr(href)').get('')
            if product_url and sku_id:
                if not product_url.startswith('http'):
                    product_url = 'https:' + product_url
                
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product_detail,
                    meta={'sku_id': sku_id},
                    priority=1
                )
        
        # 翻页
        current_page = response.meta.get('page', 1)
        if current_page < self.max_pages:
            next_page = response.css('.pn-next::attr(href)').get('')
            if next_page:
                if not next_page.startswith('http'):
                    next_page = 'https:' + next_page
                
                yield scrapy.Request(
                    url=next_page,
                    callback=self.parse,
                    meta={'page': current_page + 1},
                    priority=0
                )
    
    def parse_product_detail(self, response):
        """解析产品详情页"""
        sku_id = response.meta.get('sku_id', '')
        
        self.logger.info(f'解析京东产品: {response.url}')
        
        # 提取产品名称
        name = response.css('.sku-name::text, .product-intro h1::text').get('').strip()
        
        # 提取价格（京东价格通常通过API获取）
        price = ''
        price_text = response.css('.price::text, .p-price .price::text').get('')
        if price_text:
            price = self.extract_price(price_text)
        
        # 提取品牌
        brand = response.css('#parameter-brand td::text, .brand::text').get('')
        
        # 提取评分
        rating = response.css('.comment-score .score-num::text, .percent::text').get('')
        
        # 提取产品图片
        image_url = response.css('#spec-img::attr(src), .jqzoom img::attr(src)').get('')
        if image_url and not image_url.startswith('http'):
            image_url = 'https:' + image_url
        
        # 提取规格参数
        specs = self.extract_specs(response)
        
        # 创建产品项
        product_item = WristbandProductItem(
            brand=brand,
            name=name,
            price=price,
            specs=specs,
            url=response.url,
            image_url=image_url,
            rating=rating,
            source='jd',
            crawl_time=datetime.now().isoformat()
        )
        
        yield product_item
        
        # 获取评论
        if sku_id:
            review_url = f'https://club.jd.com/comment/productPageComments.action?productId={sku_id}&score=0&sortType=5&page=0&pageSize=10'
            yield scrapy.Request(
                url=review_url,
                callback=self.parse_reviews_api,
                meta={'product_name': name, 'product_url': response.url, 'sku_id': sku_id, 'page': 0},
                priority=2
            )
    
    def parse_reviews_api(self, response):
        """解析评论API响应"""
        product_name = response.meta.get('product_name', '')
        product_url = response.meta.get('product_url', '')
        sku_id = response.meta.get('sku_id', '')
        page = response.meta.get('page', 0)
        
        try:
            data = json.loads(response.text)
            comments = data.get('comments', [])
            
            for comment in comments:
                content = comment.get('content', '')
                rating = comment.get('score', '')
                author = comment.get('nickname', '')
                date = comment.get('creationTime', '')
                helpful = comment.get('usefulVoteCount', 0)
                
                if content and len(content.strip()) > 5:
                    review_item = WristbandReviewItem(
                        product_name=product_name,
                        product_url=product_url,
                        rating=str(rating),
                        comment=content.strip(),
                        author=author,
                        date=date,
                        helpful=str(helpful),
                        source='jd',
                        crawl_time=datetime.now().isoformat()
                    )
                    
                    yield review_item
            
            # 翻页获取更多评论
            if page < 2 and len(comments) > 0:  # 最多获取3页评论
                next_page = page + 1
                review_url = f'https://club.jd.com/comment/productPageComments.action?productId={sku_id}&score=0&sortType=5&page={next_page}&pageSize=10'
                yield scrapy.Request(
                    url=review_url,
                    callback=self.parse_reviews_api,
                    meta={'product_name': product_name, 'product_url': product_url, 'sku_id': sku_id, 'page': next_page},
                    priority=2
                )
        
        except json.JSONDecodeError:
            self.logger.error(f'评论JSON解析失败: {response.url}')
    
    def extract_price(self, price_text):
        """提取价格"""
        if not price_text:
            return ''
        
        match = re.search(r'(\d+\.?\d*)', price_text.replace(',', ''))
        if match:
            return match.group(1)
        return ''
    
    def extract_specs(self, response):
        """提取规格参数"""
        specs = []
        
        # 提取参数列表
        param_items = response.css('.parameter2 li, .Ptable-item')
        
        for item in param_items:
            text = item.css('::text').get('').strip()
            if text and ':' in text:
                specs.append(text)
        
        return '; '.join(specs) if specs else ''
