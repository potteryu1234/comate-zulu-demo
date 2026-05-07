# -*- coding: utf-8 -*-
"""
Scrapy爬虫中间件
包含：User-Agent轮换、代理池、请求频率控制
"""
import random
import time
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.downloadermiddlewares.retry import RetryMiddleware


class RotateUserAgentMiddleware(UserAgentMiddleware):
    """User-Agent轮换中间件"""
    
    def __init__(self, user_agent_list=None):
        self.user_agent_list = user_agent_list or [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
        ]
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            user_agent_list=crawler.settings.get('USER_AGENT_LIST')
        )
    
    def process_request(self, request, spider):
        ua = random.choice(self.user_agent_list)
        request.headers['User-Agent'] = ua
        spider.logger.debug(f'使用User-Agent: {ua[:50]}...')


class ProxyPoolMiddleware:
    """代理池中间件"""
    
    def __init__(self, proxy_list=None):
        self.proxy_list = proxy_list or []
        self.current_proxy = None
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            proxy_list=crawler.settings.get('PROXY_LIST')
        )
    
    def process_request(self, request, spider):
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = proxy
            spider.logger.debug(f'使用代理: {proxy}')
    
    def process_exception(self, request, exception, spider):
        if self.proxy_list:
            # 如果请求失败，更换代理重试
            request.meta['proxy'] = random.choice(self.proxy_list)
            spider.logger.warning(f'代理请求失败，更换代理重试')
            return request


class RequestDelayMiddleware:
    """请求延迟中间件 - 控制请求频率"""
    
    def __init__(self, delay_range=(1, 3)):
        self.delay_range = delay_range
        self.last_request_time = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            delay_range=crawler.settings.get('DOWNLOAD_DELAY_RANGE', (1, 3))
        )
    
    def process_request(self, request, spider):
        # 获取当前爬虫的请求时间记录
        spider_name = spider.name
        current_time = time.time()
        
        if spider_name in self.last_request_time:
            elapsed = current_time - self.last_request_time[spider_name]
            delay = random.uniform(*self.delay_range)
            
            if elapsed < delay:
                sleep_time = delay - elapsed
                spider.logger.debug(f'延迟 {sleep_time:.2f} 秒')
                time.sleep(sleep_time)
        
        self.last_request_time[spider_name] = time.time()
        return None


class CustomRetryMiddleware(RetryMiddleware):
    """自定义重试中间件"""
    
    def process_response(self, request, response, spider):
        # 如果遇到验证码或封禁，记录并跳过
        if response.status == 403:
            spider.logger.error(f'访问被禁止: {request.url}')
            return response
        
        if response.status == 302 or response.status == 301:
            # 重定向可能是封禁
            spider.logger.warning(f'请求被重定向: {request.url}')
        
        return super().process_response(request, response, spider)
