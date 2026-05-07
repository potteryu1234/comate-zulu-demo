# -*- coding: utf-8 -*-
"""
中关村在线智能手环爬虫
爬取产品规格参数、价格、评分等数据
"""
import scrapy
import re
from datetime import datetime
from scrapers.items import WristbandProductItem, WristbandReviewItem


class ZOLSpider(scrapy.Spider):
    """中关村在线爬虫"""
    name = 'zol'
    allowed_domains = ['detail.zol.com.cn']
    
    start_urls = [
        'https://detail.zol.com.cn/gpswatch/',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_pages = 5  # 每个品牌最多爬取页数
        self.max_reviews = 10  # 每个产品最多爬取评论数
    
    def parse(self, response):
        """解析品牌列表页"""
        self.logger.info(f'开始解析品牌列表: {response.url}')
        
        # 提取品牌链接
        brand_links = response.css('.brand-list a, .brand-filter a')
        
        for link in brand_links:
            brand_name = link.css('::text').get('').strip()
            brand_url = link.css('::attr(href)').get('')
            
            if brand_url and brand_name:
                if not brand_url.startswith('http'):
                    brand_url = response.urljoin(brand_url)
                
                yield scrapy.Request(
                    url=brand_url,
                    callback=self.parse_brand_page,
                    meta={'brand': brand_name, 'page': 1},
                    priority=1
                )
    
    def parse_brand_page(self, response):
        """解析品牌产品列表页"""
        brand = response.meta.get('brand', '未知品牌')
        page = response.meta.get('page', 1)
        
        self.logger.info(f'解析品牌 {brand} 第 {page} 页')
        
        # 提取产品列表
        products = response.css('.product-item, .list-item')
        
        for product in products:
            product_url = product.css('a::attr(href)').get('')
            if product_url:
                if not product_url.startswith('http'):
                    product_url = response.urljoin(product_url)
                
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product_detail,
                    meta={'brand': brand, 'url': product_url},
                    priority=2
                )
        
        # 翻页
        if page < self.max_pages:
            next_page = response.css('.next-page::attr(href), .pagination .next::attr(href)').get('')
            if next_page:
                if not next_page.startswith('http'):
                    next_page = response.urljoin(next_page)
                
                yield scrapy.Request(
                    url=next_page,
                    callback=self.parse_brand_page,
                    meta={'brand': brand, 'page': page + 1},
                    priority=1
                )
    
    def parse_product_detail(self, response):
        """解析产品详情页"""
        brand = response.meta.get('brand', '')
        url = response.meta.get('url', response.url)
        
        self.logger.info(f'解析产品详情: {response.url}')
        
        # 提取产品名称
        name = response.css('h1.product-name::text, .product-title h1::text').get('').strip()
        
        # 提取价格
        price_text = response.css('.price-type::text, .price-now::text, .price::text').get('')
        price = self.extract_price(price_text)
        
        # 提取评分
        rating = response.css('.score-num::text, .rating::text').get('')
        
        # 提取产品简介
        intro = response.css('.product-intro::text, .summary::text').get('')
        
        # 提取规格参数
        specs = self.extract_specs(response)
        
        # 提取图片
        image_url = response.css('.product-pic img::attr(src), .gallery img::attr(src)').get('')
        
        # 创建产品项
        product_item = WristbandProductItem(
            brand=brand,
            name=name,
            price=price,
            intro=intro,
            specs=specs,
            url=url,
            image_url=image_url,
            rating=rating,
            source='zol',
            crawl_time=datetime.now().isoformat()
        )
        
        yield product_item
        
        # 提取评论链接
        review_link = response.css('.review-count a::attr(href), .comment-link::attr(href)').get('')
        if review_link:
            if not review_link.startswith('http'):
                review_link = response.urljoin(review_link)
            
            yield scrapy.Request(
                url=review_link,
                callback=self.parse_reviews,
                meta={'product_name': name, 'product_url': url},
                priority=3
            )
    
    def parse_reviews(self, response):
        """解析评论页"""
        product_name = response.meta.get('product_name', '')
        product_url = response.meta.get('product_url', '')
        
        self.logger.info(f'解析评论: {response.url}')
        
        reviews = response.css('.comment-item, .review-item')
        
        for i, review in enumerate(reviews):
            if i >= self.max_reviews:
                break
            
            # 提取评分
            rating = review.css('.star-num::text, .rating::text').get('')
            
            # 提取评论内容
            comment = review.css('.comment-content::text, .review-text::text').get('')
            
            # 提取作者
            author = review.css('.user-name::text, .author::text').get('')
            
            # 提取日期
            date = review.css('.comment-date::text, .date::text').get('')
            
            if comment and len(comment.strip()) > 5:
                review_item = WristbandReviewItem(
                    product_name=product_name,
                    product_url=product_url,
                    rating=rating,
                    comment=comment.strip(),
                    author=author,
                    date=date,
                    source='zol',
                    crawl_time=datetime.now().isoformat()
                )
                
                yield review_item
    
    def extract_price(self, price_text):
        """提取价格数字"""
        if not price_text:
            return ''
        
        # 匹配价格数字
        match = re.search(r'(\d+)', price_text.replace(',', ''))
        if match:
            return match.group(1)
        return ''
    
    def extract_specs(self, response):
        """提取规格参数"""
        specs = []
        
        # 提取参数表格
        spec_rows = response.css('.parameter-table tr, .spec-table tr')
        
        for row in spec_rows:
            key = row.css('th::text, td:first-child::text').get('').strip()
            value = row.css('td:last-child::text, td:nth-child(2)::text').get('').strip()
            
            if key and value:
                specs.append(f'{key}: {value}')
        
        # 提取详细参数
        spec_items = response.css('.spec-item, .param-item')
        for item in spec_items:
            key = item.css('.spec-name::text, .param-name::text').get('').strip()
            value = item.css('.spec-value::text, .param-value::text').get('').strip()
            
            if key and value:
                specs.append(f'{key}: {value}')
        
        return '; '.join(specs) if specs else ''
