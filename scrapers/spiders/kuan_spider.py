# -*- coding: utf-8 -*-
"""
酷安智能手环评测爬虫
爬取用户评测、评分等数据
"""
import scrapy
import re
from datetime import datetime
from scrapers.items import WristbandProductItem, WristbandReviewItem


class KuanSpider(scrapy.Spider):
    """酷安爬虫"""
    name = 'kuan'
    allowed_domains = ['coolapk.com']
    
    # 酷安智能手环搜索
    start_urls = [
        'https://www.coolapk.com/search?q=智能手环',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_pages = 3
        self.max_reviews = 15
    
    def parse(self, response):
        """解析搜索列表页"""
        self.logger.info(f'解析酷安搜索页: {response.url}')
        
        # 提取产品/评测列表
        items = response.css('.app-item, .feed-item')
        
        for item in items:
            item_url = item.css('a::attr(href)').get('')
            if item_url:
                if not item_url.startswith('http'):
                    item_url = 'https://www.coolapk.com' + item_url
                
                yield scrapy.Request(
                    url=item_url,
                    callback=self.parse_detail,
                    priority=1
                )
        
        # 翻页
        current_page = response.meta.get('page', 1)
        if current_page < self.max_pages:
            next_page = response.css('.pagination .next::attr(href)').get('')
            if next_page:
                if not next_page.startswith('http'):
                    next_page = 'https://www.coolapk.com' + next_page
                
                yield scrapy.Request(
                    url=next_page,
                    callback=self.parse,
                    meta={'page': current_page + 1},
                    priority=0
                )
    
    def parse_detail(self, response):
        """解析详情页（可能是产品或评测）"""
        self.logger.info(f'解析酷安详情: {response.url}')
        
        # 判断是产品页还是评测页
        is_review = 'feed' in response.url or 'article' in response.url
        
        if is_review:
            yield from self.parse_review_page(response)
        else:
            yield from self.parse_product_page(response)
    
    def parse_product_page(self, response):
        """解析产品页"""
        # 提取产品名称
        name = response.css('h1::text, .app-title::text').get('').strip()
        
        # 提取评分
        rating = response.css('.rating-num::text, .score::text').get('')
        
        # 提取简介
        intro = response.css('.app-desc::text, .description::text').get('')
        
        # 提取图片
        image_url = response.css('.app-icon::attr(src), .logo::attr(src)').get('')
        
        product_item = WristbandProductItem(
            name=name,
            intro=intro,
            url=response.url,
            image_url=image_url,
            rating=rating,
            source='kuan',
            crawl_time=datetime.now().isoformat()
        )
        
        yield product_item
    
    def parse_review_page(self, response):
        """解析评测页"""
        # 提取产品名称
        product_name = response.css('.feed-title::text, h1::text').get('')
        if product_name:
            product_name = product_name.strip()
        
        # 提取评测内容
        content = response.css('.message-content::text, .content::text').get('')
        
        # 提取评分
        rating = response.css('.rating::text, .score::text').get('')
        
        # 提取作者
        author = response.css('.username::text, .author::text').get('')
        
        # 提取日期
        date = response.css('.date::text, .time::text').get('')
        
        if content and len(content.strip()) > 10:
            review_item = WristbandReviewItem(
                product_name=product_name,
                product_url=response.url,
                rating=rating,
                comment=content.strip(),
                author=author,
                date=date,
                source='kuan',
                crawl_time=datetime.now().isoformat()
            )
            
            yield review_item
