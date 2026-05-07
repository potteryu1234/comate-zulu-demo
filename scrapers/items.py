# -*- coding: utf-8 -*-
"""
Scrapy数据项定义
"""
import scrapy


class WristbandProductItem(scrapy.Item):
    """智能手环产品数据项"""
    # 基本信息
    brand = scrapy.Field()          # 品牌
    name = scrapy.Field()           # 产品名称
    price = scrapy.Field()          # 价格
    
    # 产品描述
    intro = scrapy.Field()          # 简介
    keywords = scrapy.Field()       # 关键词
    features = scrapy.Field()       # 功能特点
    specs = scrapy.Field()          # 详细规格
    
    # 媒体信息
    url = scrapy.Field()            # 产品链接
    image_url = scrapy.Field()      # 图片链接
    
    # 评分信息
    rating = scrapy.Field()         # 评分
    review_count = scrapy.Field()   # 评论数量
    
    # 元数据
    source = scrapy.Field()         # 数据来源
    crawl_time = scrapy.Field()     # 爬取时间


class WristbandReviewItem(scrapy.Item):
    """智能手环评论数据项"""
    # 关联产品
    product_name = scrapy.Field()   # 产品名称
    product_url = scrapy.Field()    # 产品链接
    
    # 评论信息
    rating = scrapy.Field()         # 评分/星级
    comment = scrapy.Field()        # 评论内容
    author = scrapy.Field()         # 评论者
    date = scrapy.Field()           # 评论日期
    helpful = scrapy.Field()        # 有用数
    
    # 元数据
    source = scrapy.Field()         # 数据来源
    crawl_time = scrapy.Field()     # 爬取时间


class WristbandSpecItem(scrapy.Item):
    """智能手环规格参数数据项"""
    # 关联产品
    product_name = scrapy.Field()   # 产品名称
    
    # 规格参数
    screen = scrapy.Field()         # 屏幕
    battery = scrapy.Field()        # 电池
    sensors = scrapy.Field()        # 传感器
    connectivity = scrapy.Field()   # 连接方式
    water_resistance = scrapy.Field()  # 防水等级
    compatibility = scrapy.Field()  # 兼容性
    dimensions = scrapy.Field()     # 尺寸重量
    
    # 元数据
    source = scrapy.Field()         # 数据来源
    crawl_time = scrapy.Field()     # 爬取时间


class HuaweiProductItem(scrapy.Item):
    """华为天猫商品数据项"""
    # 基础信息
    product_id = scrapy.Field()     # 商品ID
    name = scrapy.Field()           # 商品名称
    brand = scrapy.Field()          # 品牌
    current_price = scrapy.Field()  # 当前售价
    original_price = scrapy.Field() # 原价
    discount = scrapy.Field()       # 优惠信息
    sales_count = scrapy.Field()    # 销量
    rating_score = scrapy.Field()   # 评分
    review_count = scrapy.Field()   # 评价数量
    url = scrapy.Field()            # 商品链接
    image_url = scrapy.Field()      # 主图链接
    
    # 参数详情（JSON格式存储）
    release_date = scrapy.Field()   # 上市时间
    color = scrapy.Field()          # 外观颜色
    connection_type = scrapy.Field() # 连接方式
    strap_material = scrapy.Field() # 表带材质
    os = scrapy.Field()             # 操作系统
    communication = scrapy.Field()  # 通讯类型
    warranty = scrapy.Field()       # 保修期
    dial_shape = scrapy.Field()     # 表盘形状
    case_material = scrapy.Field()  # 表壳材质
    model = scrapy.Field()          # 型号
    screen_resolution = scrapy.Field() # 屏幕分辨率
    charging_mode = scrapy.Field()  # 充电模式
    health_monitoring = scrapy.Field() # 健康监测功能
    screen_type = scrapy.Field()    # 屏幕类型
    
    source = scrapy.Field()         # 数据来源
    crawl_time = scrapy.Field()     # 爬取时间


class HuaweiReviewKeywordItem(scrapy.Item):
    """华为评论关键词数据项"""
    product_id = scrapy.Field()     # 商品ID
    keyword = scrapy.Field()        # 关键词
    count = scrapy.Field()          # 出现次数
    percentage = scrapy.Field()     # 占比
    crawl_time = scrapy.Field()     # 爬取时间


class HuaweiReviewItem(scrapy.Item):
    """华为用户评论数据项（简化版）"""
    product_id = scrapy.Field()     # 商品ID
    content = scrapy.Field()        # 评论内容
    is_negative = scrapy.Field()    # 是否为差评
    crawl_time = scrapy.Field()     # 爬取时间
