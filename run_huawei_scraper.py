# -*- coding: utf-8 -*-
"""
华为天猫智能穿戴专区爬虫运行脚本
"""
import os
import sys
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.spiders.huawei_tmall_spider import HuaweiTmallSpider


def main():
    parser = argparse.ArgumentParser(description='华为天猫智能穿戴专区爬虫')
    parser.add_argument('--delay', type=int, default=5, help='下载延迟(秒)')
    parser.add_argument('--max-reviews', type=int, default=50, help='每个商品最大评论数')
    parser.add_argument('--output', type=str, default='data/huawei_products.json', help='输出文件')
    parser.add_argument('--no-pipeline', action='store_true', help='不使用数据库存储')
    
    args = parser.parse_args()
    
    # 获取项目设置
    settings = get_project_settings()
    
    # 覆盖设置
    settings.set('DOWNLOAD_DELAY', args.delay)
    settings.set('CONCURRENT_REQUESTS_PER_DOMAIN', 1)
    settings.set('COOKIES_ENABLED', True)
    settings.set('RETRY_TIMES', 3)
    settings.set('RETRY_HTTP_CODES', [500, 502, 503, 504, 408, 429, 403])
    settings.set('LOG_LEVEL', 'INFO')
    settings.set('LOG_FILE', 'huawei_scraper.log')
    
    # 数据导出设置
    settings.set('FEEDS', {
        args.output: {
            'format': 'json',
            'encoding': 'utf8',
            'store_empty': False,
            'indent': 2,
        }
    })
    
    # 管道设置
    if args.no_pipeline:
        settings.set('ITEM_PIPELINES', {})
    else:
        settings.set('ITEM_PIPELINES', {
            'scrapers.pipelines.DataValidationPipeline': 100,
            'scrapers.pipelines.DuplicateFilterPipeline': 200,
            'scrapers.pipelines.DataCleaningPipeline': 300,
            'scrapers.pipelines.DatabasePipeline': 400,
        })
    
    # 创建爬虫进程
    process = CrawlerProcess(settings)
    
    # 启动爬虫
    print(f'启动华为天猫爬虫...')
    print(f'下载延迟: {args.delay}秒')
    print(f'最大评论数: {args.max_reviews}')
    print(f'输出文件: {args.output}')
    
    process.crawl(HuaweiTmallSpider, max_reviews=args.max_reviews)
    process.start()
    
    print('爬虫执行完成')


if __name__ == '__main__':
    main()
