# -*- coding: utf-8 -*-
"""
天猫智能手环爬虫
爬取产品价格、评价等数据
"""
import scrapy
import json
import re
from datetime import datetime
from scrapers.items import WristbandProductItem, WristbandReviewItem


class TmallSpider(scrapy.Spider):
    """天猫爬虫"""
    name = 'tmall'
    allowed_domains = ['tmall.com', 'taobao.com']
    
    # 天猫智能手环搜索页
    start_urls = [
        'https://list.tmall.com/search_product.htm?q=智能手环',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'COOKIES_ENABLED': True,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_pages = 3
        self.max_reviews = 10
    
    def parse(self, response):
        """解析搜索列表页"""
        self.logger.info(f'解析天猫搜索页: {response.url}')
        
        # 提取产品列表
        products = response.css('.product, .item')
        
        for product in products:
            product_url = product.css('a::attr(href)').get('')
            if product_url:
                if not product_url.startswith('http'):
                    product_url = 'https:' + product_url
                
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product_detail,
                    priority=1
                )
        
        # 翻页
        current_page = response.meta.get('page', 1)
        if current_page < self.max_pages:
            next_page = response.css('.ui-page-next::attr(href)').get('')
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
        self.logger.info(f'解析天猫产品: {response.url}')
        
        # 提取产品名称
        name = response.css('.tb-detail-hd h1::text, .itemTitle::text').get('').strip()
        
        # 提取价格
        price_text = response.css('.tm-price::text, .notranslate::text').get('')
        price = self.extract_price(price_text)
        
        # 提取品牌
        brand = response.css('.brand::text, [data-spm="brand"]::text').get('')
        
        # 提取图片
        image_url = response.css('#J_ImgBooth::attr(src), .tb-booth img::attr(src)').get('')
        if image_url and not image_url.startswith('http'):
            image_url = 'https:' + image_url
        
        # 创建产品项
        product_item = WristbandProductItem(
            brand=brand,
            name=name,
            price=price,
            url=response.url,
            image_url=image_url,
            source='tmall',
            crawl_time=datetime.now().isoformat()
        )
        
        yield product_item
    
    def extract_price(self, price_text):
        """提取价格"""
        if not price_text:
            return ''
        
        match = re.search(r'(\d+\.?\d*)', price_text.replace(',', ''))
        if match:
            return match.group(1)
        return ''
