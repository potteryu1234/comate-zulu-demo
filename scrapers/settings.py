# -*- coding: utf-8 -*-
"""
Scrapy爬虫配置文件
"""

# 爬虫设置
BOT_NAME = 'wristband_scraper'

SPIDER_MODULES = ['scrapers.spiders']
NEWSPIDER_MODULE = 'scrapers.spiders'

# 遵守robots协议
ROBOTSTXT_OBEY = True

# 并发请求设置
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# 下载延迟（秒）
DOWNLOAD_DELAY = 2
DOWNLOAD_DELAY_RANGE = (1, 3)  # 随机延迟范围

# 请求超时
DOWNLOAD_TIMEOUT = 30

# 重试设置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# 禁用cookies
COOKIES_ENABLED = False

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# 中间件设置
DOWNLOADER_MIDDLEWARES = {
    'scrapers.middlewares.RotateUserAgentMiddleware': 400,
    'scrapers.middlewares.ProxyPoolMiddleware': 420,
    'scrapers.middlewares.RequestDelayMiddleware': 450,
    'scrapers.middlewares.CustomRetryMiddleware': 550,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
}

# 管道设置
ITEM_PIPELINES = {
    'scrapers.pipelines.DataValidationPipeline': 100,
    'scrapers.pipelines.DuplicateFilterPipeline': 200,
    'scrapers.pipelines.DataCleaningPipeline': 300,
    'scrapers.pipelines.DatabasePipeline': 400,
}

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'zol_wristband',
    'charset': 'utf8mb4'
}

# 日志设置
LOG_LEVEL = 'INFO'
LOG_FILE = 'scraper.log'

# 自动限速
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# 内存限制
MEMUSAGE_LIMIT_MB = 512
MEMUSAGE_WARNING_MB = 384

# 代理列表（可选）
PROXY_LIST = [
    # 格式: 'http://user:pass@host:port'
    # 或: 'http://host:port'
]

# 用户代理列表
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
]

# 扩展设置
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,
}

# 数据导出设置
FEEDS = {
    'data/products_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 2,
    },
}

# 请求指纹过滤
DUPEFILTER_CLASS = 'scrapy.dupefilters.RFPDupeFilter'

# 请求队列
SCHEDULER = 'scrapy.core.scheduler.Scheduler'
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'
