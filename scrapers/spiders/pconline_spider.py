# -*- coding: utf-8 -*-
"""
太平洋电脑网智能手环爬虫
爬取产品规格参数、评测等数据
"""
import scrapy
import re
from datetime import datetime
from scrapers.items import WristbandProductItem, WristbandReviewItem


class PConlineSpider(scrapy.Spider):
    """太平洋电脑网爬虫"""
    name = 'pconline'
    allowed_domains = ['pconline.com.cn']
    
    # 太平洋电脑网智能手环频道
    start_urls = [
        'https://product.pconline.com.cn/wearable_devices/',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_pages = 5
        self.max_reviews = 10
    
    def parse(self, response):
        """解析产品列表页"""
        self.logger.info(f'解析太平洋电脑网列表页: {response.url}')
        
        # 提取产品列表
        products = response.css('.item, .product-item')
        
        for product in products:
            product_url = product.css('a::attr(href)').get('')
            if product_url:
                if not product_url.startswith('http'):
                    product_url = response.urljoin(product_url)
                
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product_detail,
                    priority=1
                )
        
        # 翻页
        current_page = response.meta.get('page', 1)
        if current_page < self.max_pages:
            next_page = response.css('.next::attr(href)').get('')
            if next_page:
                if not next_page.startswith('http'):
                    next_page = response.urljoin(next_page)
                
                yield scrapy.Request(
                    url=next_page,
                    callback=self.parse,
                    meta={'page': current_page + 1},
                    priority=0
                )
    
    def parse_product_detail(self, response):
        """解析产品详情页"""
        self.logger.info(f'解析太平洋电脑网产品详情: {response.url}')
        
        # 提取产品名称
        name = response.css('h1::text, .product-name::text').get('').strip()
        
        # 提取品牌
        brand = response.css('.brand::text, .brand-name::text').get('')
        
        # 提取价格
        price_text = response.css('.price::text, .price-num::text').get('')
        price = self.extract_price(price_text)
        
        # 提取评分
        rating = response.css('.score::text, .rating::text').get('')
        
        # 提取图片
        image_url = response.css('.product-img img::attr(src)').get('')
        
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
            source='pconline',
            crawl_time=datetime.now().isoformat()
        )
        
        yield product_item
        
        # 提取评测链接
        review_link = response.css('.review-link::attr(href), .comment-link::attr(href)').get('')
        if review_link:
            if not review_link.startswith('http'):
                review_link = response.urljoin(review_link)
            
            yield scrapy.Request(
                url=review_link,
                callback=self.parse_reviews,
                meta={'product_name': name},
                priority=2
            )
    
    def parse_reviews(self, response):
        """解析评测/评论页"""
        product_name = response.meta.get('product_name', '')
        
        self.logger.info(f'解析太平洋电脑网评测: {response.url}')
        
        reviews = response.css('.review-item, .comment-item')
        
        for i, review in enumerate(reviews):
            if i >= self.max_reviews:
                break
            
            # 提取标题
            title = review.css('.review-title::text, .title::text').get('')
            
            # 提取内容
            content = review.css('.review-content::text, .content::text').get('')
            
            # 提取评分
            rating = review.css('.score::text, .rating::text').get('')
            
            # 提取作者
            author = review.css('.author::text, .username::text').get('')
            
            # 提取日期
            date = review.css('.date::text, .time::text').get('')
            
            # 合并标题和内容
            full_content = ''
            if title:
                full_content += title.strip() + ' '
            if content:
                full_content += content.strip()
            
            if full_content and len(full_content) > 5:
                review_item = WristbandReviewItem(
                    product_name=product_name,
                    product_url=response.url,
                    rating=rating,
                    comment=full_content,
                    author=author,
                    date=date,
                    source='pconline',
                    crawl_time=datetime.now().isoformat()
                )
                
                yield review_item
    
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
        
        # 提取参数表格
        spec_rows = response.css('.spec-table tr, .parameter-table tr')
        
        for row in spec_rows:
            key = row.css('th::text, td:first-child::text').get('').strip()
            value = row.css('td:last-child::text').get('').strip()
            
            if key and value:
                specs.append(f'{key}: {value}')
        
        return '; '.join(specs) if specs else ''
