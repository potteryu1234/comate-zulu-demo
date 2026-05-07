# 华为天猫智能穿戴专区爬虫 - 任务计划

- [x] Task 1: 创建数据库初始化脚本
    - 1.1: 创建 init_huawei_db.py 脚本
    - 1.2: 创建 huawei_products 表
    - 1.3: 创建 huawei_review_keywords 表
    - 1.4: 创建 huawei_reviews 表
    - 1.5: 运行脚本初始化数据库

- [x] Task 2: 扩展数据项定义 (items.py)
    - 2.1: 添加 HuaweiProductItem 类
    - 2.2: 添加 HuaweiReviewKeywordItem 类
    - 2.3: 添加 HuaweiReviewItem 类

- [x] Task 3: 扩展数据管道 (pipelines.py)
    - 3.1: 添加华为产品存储方法 _save_huawei_product
    - 3.2: 添加评论关键词存储方法 _save_review_keywords
    - 3.3: 添加评论存储方法 _save_huawei_review
    - 3.4: 在 process_item 中添加类型判断逻辑

- [x] Task 4: 创建华为天猫爬虫
    - 4.1: 创建 huawei_tmall_spider.py 文件
    - 4.2: 实现 parse_list_page 方法解析商品列表
    - 4.3: 实现 parse_product_detail 方法提取基础信息
    - 4.4: 实现 parse_specs 方法提取参数详情
    - 4.5: 实现 parse_review_keywords 方法提取评论关键词
    - 4.6: 实现 parse_reviews 方法提取用户评论（优先差评）

- [x] Task 5: 创建爬虫运行脚本
    - 5.1: 创建 run_huawei_scraper.py 脚本
    - 5.2: 配置爬虫参数（延迟、并发等）
    - 5.3: 添加命令行参数支持

- [x] Task 6: 测试与验证
    - 6.1: 测试数据库连接
    - 6.2: 测试单商品爬取
    - 6.3: 验证数据完整性
    - 6.4: 运行完整爬虫
