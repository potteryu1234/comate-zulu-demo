# 华为天猫智能穿戴专区爬虫 - 需求规格文档

## 1. 需求概述

### 1.1 目标
针对华为天猫官方旗舰店智能穿戴专区（https://huaweistore.tmall.com/category-1201482782-1662553168.htm），爬取所有商品的详细信息，包括售价、参数详情、评论关键词及占比、用户评论内容（优先差评）。

### 1.2 数据来源
- **列表页**: https://huaweistore.tmall.com/category-1201482782-1662553168.htm?search=y&catName=智能穿戴
- **商品详情页**: 如 https://detail.tmall.com/item.htm?id=975529162954

---

## 2. 爬取字段定义

### 2.1 商品基础信息（列表页+详情页）
| 字段 | 说明 | 示例 |
|------|------|------|
| product_id | 商品ID | 975529162954 |
| name | 商品名称 | 【国家补贴】HUAWEI WATCH GT 6华为手表智能运动手表 |
| brand | 品牌 | 华为 |
| current_price | 当前售价 | 1187.90 |
| original_price | 原价 | 1488.00 |
| discount | 优惠信息 | 立减300元 |
| sales_count | 销量 | 已售6万+ |
| rating_score | 评分 | 5.0 |
| review_count | 评价数量 | 6000+ |
| url | 商品链接 | https://detail.tmall.com/item.htm?id=... |
| image_url | 主图链接 | https://... |

### 2.2 参数详情（详情页-参数信息Tab）
| 字段 | 说明 | 示例 |
|------|------|------|
| release_date | 上市时间 | 2025-09-24 |
| color | 外观颜色 | 41mm 魅影黑 |
| connection_type | 连接方式 | 蓝牙连接 |
| strap_material | 表带材质 | 氟橡胶/复合编织/复合素皮 |
| os | 操作系统 | 鸿蒙系统 |
| communication | 通讯类型 | 不可插卡 |
| warranty | 保修期 | 1年 |
| dial_shape | 表盘形状 | 圆形 |
| case_material | 表壳材质 | 前壳：不锈钢；底壳：高性能纤维增强复合材料 |
| brand_name | 品牌 | Huawei/华为 |
| model | 型号 | HUAWEI WATCH GT 6 |
| screen_resolution | 屏幕分辨率 | 466x466像素 |
| charging_mode | 充电模式 | 无线充电 |
| health_monitoring | 健康监测功能 | 心率监测 体温监测 生理周期提醒 睡眠监测 血氧监测 |
| screen_type | 屏幕类型 | AMOLED |

### 2.3 评论关键词及占比（详情页-用户评价Tab上方）
| 字段 | 说明 | 示例 |
|------|------|------|
| keyword | 关键词 | 续航能力够用 |
| count | 数量 | 875 |
| percentage | 占比 | 计算得出 |

### 2.4 用户评论（详情页-用户评价Tab）
| 字段 | 说明 | 示例 |
|------|------|------|
| content | 评论内容 | 非常漂亮。华为真的是非常漂亮了... |
| is_negative | 是否为差评 | true/false |

---

## 3. 数据库设计

### 3.1 商品表 (huawei_products)
```sql
CREATE TABLE huawei_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL COMMENT '天猫商品ID',
    name VARCHAR(500) NOT NULL COMMENT '商品名称',
    brand VARCHAR(100) COMMENT '品牌',
    current_price DECIMAL(10,2) COMMENT '当前售价',
    original_price DECIMAL(10,2) COMMENT '原价',
    discount VARCHAR(200) COMMENT '优惠信息',
    sales_count VARCHAR(50) COMMENT '销量文本',
    rating_score DECIMAL(2,1) COMMENT '评分',
    review_count VARCHAR(50) COMMENT '评价数量文本',
    url VARCHAR(500) COMMENT '商品链接',
    image_url VARCHAR(500) COMMENT '主图链接',
    
    -- 参数详情
    release_date DATE COMMENT '上市时间',
    color VARCHAR(200) COMMENT '外观颜色',
    connection_type VARCHAR(100) COMMENT '连接方式',
    strap_material VARCHAR(200) COMMENT '表带材质',
    os VARCHAR(100) COMMENT '操作系统',
    communication VARCHAR(100) COMMENT '通讯类型',
    warranty VARCHAR(50) COMMENT '保修期',
    dial_shape VARCHAR(50) COMMENT '表盘形状',
    case_material VARCHAR(300) COMMENT '表壳材质',
    model VARCHAR(100) COMMENT '型号',
    screen_resolution VARCHAR(100) COMMENT '屏幕分辨率',
    charging_mode VARCHAR(100) COMMENT '充电模式',
    health_monitoring TEXT COMMENT '健康监测功能',
    screen_type VARCHAR(100) COMMENT '屏幕类型',
    
    source VARCHAR(50) DEFAULT 'tmall_huawei' COMMENT '数据来源',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '爬取时间',
    INDEX idx_product_id (product_id),
    INDEX idx_model (model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3.2 评论关键词表 (huawei_review_keywords)
```sql
CREATE TABLE huawei_review_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL COMMENT '商品ID',
    keyword VARCHAR(200) NOT NULL COMMENT '关键词',
    count INT DEFAULT 0 COMMENT '出现次数',
    percentage DECIMAL(5,2) COMMENT '占比(%)',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES huawei_products(product_id) ON DELETE CASCADE,
    INDEX idx_product_keyword (product_id, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3.3 用户评论表 (huawei_reviews)
```sql
CREATE TABLE huawei_reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL COMMENT '商品ID',
    content TEXT COMMENT '评论内容',
    is_negative BOOLEAN DEFAULT FALSE COMMENT '是否为差评（优先爬取）',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES huawei_products(product_id) ON DELETE CASCADE,
    INDEX idx_product_id (product_id),
    INDEX idx_is_negative (is_negative)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 4. 爬虫架构设计

### 4.1 爬虫组件
```
HuaweiTmallSpider (主爬虫)
├── parse_list_page()      # 解析商品列表页
├── parse_product_detail() # 解析商品详情页
├── parse_specs()          # 解析参数信息
├── parse_review_keywords() # 解析评论关键词
└── parse_reviews()        # 解析用户评论
```

### 4.2 数据项定义 (items.py 新增)
```python
class HuaweiProductItem(scrapy.Item):
    # 基础信息
    product_id = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    current_price = scrapy.Field()
    original_price = scrapy.Field()
    discount = scrapy.Field()
    sales_count = scrapy.Field()
    rating_score = scrapy.Field()
    review_count = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    
    # 参数详情
    specs = scrapy.Field()  # 存储为JSON格式
    
    source = scrapy.Field()
    crawl_time = scrapy.Field()

class HuaweiReviewKeywordItem(scrapy.Item):
    product_id = scrapy.Field()
    keyword = scrapy.Field()
    count = scrapy.Field()
    percentage = scrapy.Field()
    crawl_time = scrapy.Field()

class HuaweiReviewItem(scrapy.Item):
    product_id = scrapy.Field()
    content = scrapy.Field()      # 评论内容（核心字段）
    is_negative = scrapy.Field()  # 是否为差评（用于优先爬取差评）
    crawl_time = scrapy.Field()
```

### 4.3 管道处理 (pipelines.py 新增)
```python
class HuaweiDataPipeline:
    """华为数据专用存储管道"""
    def _save_huawei_product(self, adapter, spider)
    def _save_review_keywords(self, adapter, spider)
    def _save_huawei_review(self, adapter, spider)
```

---

## 5. 爬取策略

### 5.1 列表页爬取
- 从智能穿戴专区列表页开始
- 提取所有商品链接
- 支持翻页（如有）
- 限制：爬取全部商品

### 5.2 详情页爬取
- 访问每个商品详情页
- 提取基础信息（价格、销量、评分等）
- 点击/访问"参数信息"Tab获取完整规格
- 提取评论关键词及数量
- 访问"用户评价"Tab获取评论

### 5.3 评论爬取策略
- 优先爬取差评（按时间倒序）
- 每个商品至少爬取50条评论
- 差评优先：先爬取1-3星评价
- 如差评不足，补充好评
- 限制：每个商品最多200条评论

### 5.4 反爬策略
- 使用Selenium/Playwright处理动态加载
- 随机延迟 3-8秒
- User-Agent轮换
- Cookie保持会话
- 失败重试3次

---

## 6. 技术实现要点

### 6.1 动态内容处理
天猫页面大量使用JavaScript渲染，需要：
- 使用Playwright或Selenium处理
- 等待关键元素加载完成
- 处理Ajax请求获取评论数据

### 6.2 关键选择器
```python
# 商品列表页
product_links = "div[data-category='auctions'] a[href*='item.htm']"

# 商品详情
name = "h1[data-spm='1000987']"  # 或 .tb-detail-hd h1
price = ".tm-price, .notranslate, .tb-rmb-num"
sales = ".sell-count"
rating = ".rate-score"

# 参数信息
spec_rows = "#J_AttrList tr"  # 或 .tm-tableAttr tr

# 评论关键词
keywords = ".rate-tag-inner span"

# 评论列表
reviews = ".rate-item"
review_content = ".rate-content"
review_author = ".rate-user-info"
```

### 6.3 API接口分析
天猫评论通常通过API获取：
```
https://rate.tmall.com/list_detail_rate.htm?itemId={id}&sellerId={sid}&currentPage={page}
```

---

## 7. 异常处理

### 7.1 常见异常
- 页面加载超时 → 重试3次后跳过
- 元素未找到 → 记录日志，尝试备用选择器
- 验证码/登录拦截 → 暂停爬虫，人工处理
- 反爬限制 → 增加延迟，更换IP

### 7.2 数据完整性检查
- 必填字段缺失 → 标记为不完整数据
- 价格格式异常 → 尝试多种解析方式
- 评论为空 → 跳过该条评论

---

## 8. 预期输出

### 8.1 数据量预估
- 商品数量：约20-50款智能穿戴产品
- 每个商品评论：50-200条
- 评论关键词：每个商品5-10个

### 8.2 数据用途
- 竞品分析
- 价格监控
- 用户反馈分析（特别是差评分析）
- 产品改进建议

---

## 9. 文件结构

```
scrapers/
├── spiders/
│   ├── __init__.py
│   └── huawei_tmall_spider.py    # 新增：华为天猫爬虫
├── items.py                       # 新增：华为数据项
├── pipelines.py                   # 新增：华为数据管道
└── settings.py                    # 修改：添加新爬虫配置

init_huawei_db.py                  # 新增：数据库初始化脚本
run_huawei_scraper.py              # 新增：爬虫运行脚本
```

---

## 10. 注意事项

1. **遵守robots.txt** - 天猫有严格的爬虫限制
2. **控制爬取频率** - 避免对服务器造成压力
3. **数据隐私** - 仅爬取公开信息，不获取用户隐私
4. **法律合规** - 仅用于学习和研究目的
5. **动态适配** - 天猫页面结构可能变化，需要维护选择器
