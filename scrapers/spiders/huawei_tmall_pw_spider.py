# -*- coding: utf-8 -*-
"""
华为天猫智能穿戴专区爬虫 - Playwright版本
使用scrapy-playwright处理动态页面
"""
import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urlencode
from scrapers.items import HuaweiProductItem, HuaweiReviewKeywordItem, HuaweiReviewItem
from scrapy_playwright.page import PageMethod


class HuaweiTmallPWSpider(scrapy.Spider):
    """华为天猫智能穿戴爬虫 - Playwright版"""
    name = 'huawei_tmall_pw'
    allowed_domains = ['tmall.com', 'taobao.com']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'timeout': 60000,
        },
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 60000,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_reviews = int(getattr(self, 'max_reviews', 50))
        self.processed_products = set()
        self.target_url = 'https://huaweistore.tmall.com/category-1201482782-1662553168.htm?search=y&catName=%D6%C7%C4%DC%B4%A9%B4%F7'
    
    def start_requests(self):
        """开始请求"""
        yield scrapy.Request(
            url=self.target_url,
            callback=self.parse_list_page,
            meta={
                'playwright': True,
                'playwright_page_methods': [
                    PageMethod('wait_for_timeout', 5000),  # 等待5秒让页面加载
                ]
            }
        )
    
    def parse_list_page(self, response):
        """解析商品列表页"""
        self.logger.info(f'解析列表页: {response.url}')
        
        # 提取商品链接
        product_links = response.css('a[href*="item.htm"]::attr(href)').getall()
        self.logger.info(f'找到 {len(product_links)} 个链接')
        
        product_ids = []
        for link in product_links:
            if 'id=' in link:
                match = re.search(r'id=(\d+)', link)
                if match:
                    pid = match.group(1)
                    if pid not in product_ids:
                        product_ids.append(pid)
        
        self.logger.info(f'发现 {len(product_ids)} 个商品ID')
        
        # 限制前5个商品用于测试
        for product_id in product_ids[:5]:
            if product_id in self.processed_products:
                continue
            self.processed_products.add(product_id)
            
            detail_url = f'https://detail.tmall.com/item.htm?id={product_id}'
            self.logger.info(f'准备爬取商品: {product_id}')
            
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_product_detail,
                meta={
                    'product_id': product_id,
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_timeout', 8000),  # 等待8秒
                        PageMethod('wait_for_load_state', 'networkidle'),
                    ]
                }
            )
    
    def parse_product_detail(self, response):
        """解析商品详情页"""
        product_id = response.meta.get('product_id', '')
        self.logger.info(f'解析商品详情: {product_id}')
        
        # 提取基础信息
        name = self._extract_name(response)
        current_price = self._extract_price(response)
        original_price = self._extract_original_price(response)
        discount = self._extract_discount(response)
        sales_count = self._extract_sales(response)
        rating_score = self._extract_rating(response)
        review_count = self._extract_review_count(response)
        image_url = self._extract_image(response)
        
        self.logger.info(f'商品: {name[:50] if name else "未找到"}, 价格: {current_price}')
        
        # 创建商品项
        product_item = HuaweiProductItem(
            product_id=product_id,
            name=name,
            brand='华为',
            current_price=current_price,
            original_price=original_price,
            discount=discount,
            sales_count=sales_count,
            rating_score=rating_score,
            review_count=review_count,
            url=response.url,
            image_url=image_url,
            source='tmall_huawei',
            crawl_time=datetime.now()
        )
        
        # 提取参数信息
        self._extract_specs(response, product_item)
        
        yield product_item
        
        # 提取评论关键词
        keywords_yielded = yield from self._extract_review_keywords(response, product_id)
        self.logger.info(f'提取到 {keywords_yielded} 个关键词')
        
        # 提取评论
        reviews_yielded = yield from self._extract_reviews(response, product_id)
        self.logger.info(f'提取到 {reviews_yielded} 条评论')
        
        # 尝试获取评论API
        seller_id = self._extract_seller_id(response)
        if seller_id:
            self.logger.info(f'找到卖家ID: {seller_id}')
            api_url = self._build_review_api_url(product_id, seller_id, 1)
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_reviews_api,
                meta={'product_id': product_id, 'seller_id': seller_id, 'page': 1, 'collected': reviews_yielded}
            )
    
    def _extract_name(self, response):
        """提取商品名称"""
        # 从meta标签提取
        name = response.css('meta[property="og:title"]::attr(content)').get('')
        if name:
            return name.strip()
        
        # 从页面标题提取
        name = response.css('title::text').get('')
        if name:
            name = re.sub(r'\s*-\s*天猫.*$', '', name)
            return name.strip()
        
        # 从h1提取
        selectors = [
            'h1[data-spm="1000987"]::text',
            '.tb-detail-hd h1::text',
            'h1::text'
        ]
        for selector in selectors:
            name = response.css(selector).get('').strip()
            if name:
                return name
        return ''
    
    def _extract_price(self, response):
        """提取当前价格"""
        # 从脚本中提取
        scripts = response.css('script::text').getall()
        for script in scripts:
            match = re.search(r'"defaultItemPrice"[:\s]*"([^"]+)"', script)
            if match:
                return self._parse_price(match.group(1))
            match = re.search(r'"price"[:\s]*"([^"]+)"', script)
            if match:
                return self._parse_price(match.group(1))
        
        price_text = response.css('.tm-price::text, .notranslate::text, .tb-rmb-num::text').get('')
        return self._parse_price(price_text)
    
    def _extract_original_price(self, response):
        """提取原价"""
        price_text = response.css('.tm-price.tm-price-ori::text, .ori-price::text').get('')
        return self._parse_price(price_text)
    
    def _parse_price(self, price_text):
        """解析价格文本"""
        if not price_text:
            return None
        match = re.search(r'(\d+\.?\d*)', str(price_text).replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except:
                return None
        return None
    
    def _extract_discount(self, response):
        """提取优惠信息"""
        discount = response.css('.tm-promo-price span::text, .discount::text').get('')
        return discount.strip() if discount else ''
    
    def _extract_sales(self, response):
        """提取销量"""
        sales = response.css('.sell-count::text, .sale-num::text').get('')
        return sales.strip() if sales else ''
    
    def _extract_rating(self, response):
        """提取评分"""
        rating_text = response.css('.rate-score::text, .score::text').get('')
        if rating_text:
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        return None
    
    def _extract_review_count(self, response):
        """提取评价数量"""
        count = response.css('.rate-count::text, .J_ReviewsCount::text').get('')
        return count.strip() if count else ''
    
    def _extract_image(self, response):
        """提取主图"""
        img = response.css('meta[property="og:image"]::attr(content)').get('')
        if img:
            return img
        
        img = response.css('#J_ImgBooth::attr(src), .tb-booth img::attr(src)').get('')
        if img and not img.startswith('http'):
            img = 'https:' + img
        return img
    
    def _extract_specs(self, response, product_item):
        """提取参数信息"""
        scripts = response.css('script::text').getall()
        specs = {}
        
        for script in scripts:
            match = re.search(r'"props"\s*:\s*(\[.*?\])', script, re.DOTALL)
            if match:
                try:
                    props = json.loads(match.group(1))
                    for prop in props:
                        if 'name' in prop and 'value' in prop:
                            specs[prop['name']] = prop['value']
                except:
                    pass
        
        spec_rows = response.css('#J_AttrList tr, .tm-tableAttr tr, .basicInfo tr')
        for row in spec_rows:
            cells = row.css('td, th')
            if len(cells) >= 2:
                key = cells[0].css('::text').get('').strip()
                value = cells[1].css('::text').get('').strip()
                if key and value:
                    specs[key] = value
        
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
            '品牌': 'brand_name',
            '型号': 'model',
            '屏幕分辨率': 'screen_resolution',
            '充电模式': 'charging_mode',
            '健康监测功能': 'health_monitoring',
            '屏幕类型': 'screen_type',
        }
        
        for cn_key, field_name in field_mapping.items():
            if cn_key in specs:
                value = specs[cn_key]
                if field_name == 'release_date' and value:
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except:
                        pass
                setattr(product_item, field_name, value)
    
    def _extract_review_keywords(self, response, product_id):
        """提取评论关键词及数量"""
        scripts = response.css('script::text').getall()
        keywords_data = []
        count = 0
        
        for script in scripts:
            match = re.search(r'"tagClouds"\s*:\s*(\[.*?\])', script, re.DOTALL)
            if match:
                try:
                    tags = json.loads(match.group(1))
                    for tag in tags:
                        if 'tag' in tag and 'count' in tag:
                            keywords_data.append({
                                'keyword': tag['tag'],
                                'count': tag['count']
                            })
                except:
                    pass
        
        if not keywords_data:
            keyword_items = response.css('.rate-tag-inner span, .rate-tag-box span, .tag-cloud span')
            for item in keyword_items:
                text = item.css('::text').get('')
                if text:
                    match = re.match(r'(.+?)\s*(\d+)', text)
                    if match:
                        keywords_data.append({
                            'keyword': match.group(1).strip(),
                            'count': int(match.group(2))
                        })
        
        for kw_data in keywords_data:
            yield HuaweiReviewKeywordItem(
                product_id=product_id,
                keyword=kw_data['keyword'],
                count=kw_data['count'],
                percentage=None,
                crawl_time=datetime.now()
            )
            count += 1
        
        return count
    
    def _extract_reviews(self, response, product_id):
        """提取用户评论"""
        scripts = response.css('script::text').getall()
        reviews_data = []
        count = 0
        
        for script in scripts:
            match = re.search(r'"rateList"\s*:\s*(\[.*?\])', script, re.DOTALL)
            if match:
                try:
                    reviews = json.loads(match.group(1))
                    for review in reviews:
                        content = review.get('rateContent', '')
                        if content:
                            rating = review.get('rate', 0)
                            is_negative = rating <= 2
                            reviews_data.append({
                                'content': content.strip(),
                                'is_negative': is_negative
                            })
                except:
                    pass
        
        if not reviews_data:
            review_elements = response.css('.rate-item, .tm-rate-item')
            for review in review_elements:
                content = review.css('.rate-content::text, .tm-rate-content::text').get('')
                if content:
                    content = content.strip()
                    negative_words = ['差', '不好', '失望', '问题', '坏', '慢', '卡', '发热', '耗电', '垃圾', '坑']
                    is_negative = any(word in content for word in negative_words)
                    reviews_data.append({
                        'content': content,
                        'is_negative': is_negative
                    })
        
        reviews_data = reviews_data[:self.max_reviews]
        
        for review_data in reviews_data:
            yield HuaweiReviewItem(
                product_id=product_id,
                content=review_data['content'],
                is_negative=review_data['is_negative'],
                crawl_time=datetime.now()
            )
            count += 1
        
        return count
    
    def _extract_seller_id(self, response):
        """提取卖家ID"""
        scripts = response.css('script::text').getall()
        for script in scripts:
            match = re.search(r'sellerId["\']?\s*[:=]\s*["\']?(\d+)', script)
            if match:
                return match.group(1)
        return None
    
    def _build_review_api_url(self, item_id, seller_id, page=1):
        """构建评论API URL"""
        params = {
            'itemId': item_id,
            'sellerId': seller_id,
            'currentPage': page,
            'pageSize': 20,
        }
        return f'https://rate.tmall.com/list_detail_rate.htm?{urlencode(params)}'
    
    def parse_reviews_api(self, response):
        """解析评论API响应"""
        product_id = response.meta['product_id']
        seller_id = response.meta['seller_id']
        page = response.meta.get('page', 1)
        collected = response.meta.get('collected', 0)
        
        try:
            text = response.text
            match = re.search(r'\((.*)\)', text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                
                reviews = data.get('rateDetail', {}).get('rateList', [])
                for review in reviews:
                    content = review.get('rateContent', '')
                    if content:
                        rating = review.get('rate', 0)
                        is_negative = rating <= 2
                        
                        yield HuaweiReviewItem(
                            product_id=product_id,
                            content=content.strip(),
                            is_negative=is_negative,
                            crawl_time=datetime.now()
                        )
                        collected += 1
                        
                        if collected >= self.max_reviews:
                            return
                
                total_page = data.get('rateDetail', {}).get('paginator', {}).get('lastPage', 1)
                if page < min(total_page, 3) and collected < self.max_reviews:
                    next_page = page + 1
                    api_url = self._build_review_api_url(product_id, seller_id, next_page)
                    yield scrapy.Request(
                        url=api_url,
                        callback=self.parse_reviews_api,
                        meta={'product_id': product_id, 'seller_id': seller_id, 'page': next_page, 'collected': collected}
                    )
                    
        except Exception as e:
            self.logger.error(f'解析评论API失败: {e}')
