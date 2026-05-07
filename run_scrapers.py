# -*- coding: utf-8 -*-
"""
爬虫运行脚本
支持运行多个爬虫，统一管理
"""
import os
import sys
import logging
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.spiders.zol_spider import ZOLSpider
from scrapers.spiders.jd_spider import JDSpider
from scrapers.spiders.tmall_spider import TmallSpider
from scrapers.spiders.kuan_spider import KuanSpider
from scrapers.spiders.pconline_spider import PConlineSpider


def setup_logging():
    """设置日志"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def run_single_spider(spider_class, spider_name, logger):
    """运行单个爬虫"""
    logger.info(f'开始运行爬虫: {spider_name}')
    
    try:
        # 获取设置
        settings = get_project_settings()
        settings.set('BOT_NAME', f'wristband_{spider_name}')
        settings.set('LOG_LEVEL', 'INFO')
        
        # 创建爬虫进程
        process = CrawlerProcess(settings)
        process.crawl(spider_class)
        process.start(stop_after_crawl=True)
        
        logger.info(f'爬虫 {spider_name} 运行完成')
        return True
    
    except Exception as e:
        logger.error(f'爬虫 {spider_name} 运行失败: {e}')
        return False


def run_all_spiders():
    """运行所有爬虫"""
    logger = setup_logging()
    
    # 爬虫列表
    spiders = [
        (ZOLSpider, 'zol'),
        (JDSpider, 'jd'),
        (TmallSpider, 'tmall'),
        (KuanSpider, 'kuan'),
        (PConlineSpider, 'pconline'),
    ]
    
    logger.info('=' * 50)
    logger.info('开始运行智能手环数据采集爬虫')
    logger.info('=' * 50)
    
    results = {}
    
    for spider_class, spider_name in spiders:
        success = run_single_spider(spider_class, spider_name, logger)
        results[spider_name] = success
        
        if not success:
            logger.warning(f'爬虫 {spider_name} 运行失败，继续运行其他爬虫')
    
    # 输出总结
    logger.info('=' * 50)
    logger.info('爬虫运行总结:')
    for spider_name, success in results.items():
        status = '成功' if success else '失败'
        logger.info(f'  {spider_name}: {status}')
    logger.info('=' * 50)


def run_specific_spider(spider_name):
    """运行指定爬虫"""
    logger = setup_logging()
    
    spider_map = {
        'zol': ZOLSpider,
        'jd': JDSpider,
        'tmall': TmallSpider,
        'kuan': KuanSpider,
        'pconline': PConlineSpider,
    }
    
    if spider_name not in spider_map:
        logger.error(f'未知爬虫: {spider_name}')
        logger.info(f'可用爬虫: {", ".join(spider_map.keys())}')
        return
    
    spider_class = spider_map[spider_name]
    run_single_spider(spider_class, spider_name, logger)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='智能手环数据采集爬虫')
    parser.add_argument('--spider', '-s', type=str, help='指定爬虫名称 (zol/jd/tmall/kuan/pconline)')
    parser.add_argument('--all', '-a', action='store_true', help='运行所有爬虫')
    
    args = parser.parse_args()
    
    if args.spider:
        run_specific_spider(args.spider)
    elif args.all:
        run_all_spiders()
    else:
        # 默认运行中关村在线爬虫
        run_specific_spider('zol')
