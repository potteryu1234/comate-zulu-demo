# -*- coding: utf-8 -*-
"""
智能手环选购分析与健康功能评估平台 - Flask Web应用
"""
from flask import Flask, render_template, jsonify, request, session
import pymysql
import json
import re
import math
from snownlp import SnowNLP
import jieba
import jieba.analyse
from collections import Counter
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# MySQL配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'zol_wristband',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# ==================== 健康功能清单 ====================
HEALTH_FEATURES = {
    'heart_rate': ['心率', '心跳', 'Heart Rate', 'HR', '心率监测', '心率检测'],
    'sleep': ['睡眠', 'Sleep', '睡眠质量', '睡眠监测', '深睡', '浅睡', 'REM睡眠', '睡眠追踪'],
    'blood_oxygen': ['血氧', 'SpO2', 'Blood Oxygen', '血氧饱和度', '血氧监测'],
    'stress': ['压力', 'Stress', '压力监测', '压力检测', '压力管理'],
    'body_temp': ['体温', '温度', 'Temperature', '体表温度', '体温监测'],
    'ecg': ['心电图', 'ECG', '心电', '心电监测', '心电检测'],
    'blood_pressure': ['血压', 'Blood Pressure', '血压监测', '血压检测'],
    'blood_sugar': ['血糖', 'Blood Sugar', '血糖监测', '血糖检测'],
    'gps': ['GPS', '定位', '卫星定位', '北斗', 'GLONASS', ' Galileo', '双频GPS'],
    'nfc': ['NFC', '门禁', '公交卡', '支付', '银联', '交通卡'],
    'water_resist': ['防水', 'Water', 'ATM', 'IP68', 'IP67', '5ATM', '10ATM', '游泳'],
    'bluetooth_call': ['蓝牙通话', '通话', 'Call', '蓝牙电话', '语音通话'],
    'sports_mode': ['运动模式', '运动识别', '运动监测', '跑步', '骑行', '游泳模式', '健身'],
    'menstrual': ['生理期', '经期', '女性健康', '月经周期', '排卵'],
    'breathing': ['呼吸', '呼吸训练', '呼吸监测', '呼吸频率', '深呼吸'],
    'fall_detection': ['跌倒检测', '摔倒', '紧急求助', 'SOS', '安全监测'],
    'sleep_apnea': ['睡眠呼吸暂停', '打鼾监测', '呼吸质量', '睡眠呼吸'],
    'vo2max': ['最大摄氧量', 'VO2Max', '有氧能力', '运动能力'],
    'recovery': ['恢复时间', '训练恢复', '身体恢复', 'Recovery'],
    'training_load': ['训练负荷', '运动量', '训练量', '运动强度']
}

# ==================== 数据预处理模块 ====================

def extract_health_features(specs_text):
    """从规格文本中提取健康功能，生成二进制矩阵"""
    if not specs_text:
        return {key: 0 for key in HEALTH_FEATURES.keys()}
    
    specs_lower = specs_text.lower()
    features = {}
    
    for feature_key, keywords in HEALTH_FEATURES.items():
        has_feature = 0
        for keyword in keywords:
            if keyword.lower() in specs_lower or keyword in specs_text:
                has_feature = 1
                break
        features[feature_key] = has_feature
    
    return features

def calculate_battery_score(specs_text):
    """计算续航指数（0-10分）- 增强版"""
    if not specs_text:
        return 5.0
    
    specs_lower = specs_text.lower()
    
    # 提取典型模式/日常使用续航天数
    typical_patterns = [
        r'(?:典型|日常|普通|标准|常规).*?(\d+)\s*天',
        r'续航.*?(\d+)\s*天',
        r'待机.*?(\d+)\s*天',
        r'使用.*?(\d+)\s*天',
    ]
    typical_days = None
    for pattern in typical_patterns:
        match = re.search(pattern, specs_lower)
        if match:
            typical_days = int(match.group(1))
            break
    if typical_days is None:
        typical_days = 7  # 默认值
    
    # 提取GPS模式续航（支持小时和分钟）
    gps_patterns = [
        r'gps.*?(\d+)\s*小时',
        r'定位.*?(\d+)\s*小时',
        r'gps.*?(\d+)\s*h',
    ]
    gps_hours = None
    for pattern in gps_patterns:
        match = re.search(pattern, specs_lower)
        if match:
            gps_hours = int(match.group(1))
            break
    if gps_hours is None:
        gps_hours = 10  # 默认值
    
    # 提取重度使用续航
    heavy_patterns = [
        r'(?:重度|高强度|频繁).*?(\d+)\s*天',
        r'(?:重度|高强度|频繁).*?(\d+)\s*小时',
    ]
    heavy_hours = None
    for pattern in heavy_patterns:
        match = re.search(pattern, specs_lower)
        if match:
            val = int(match.group(1))
            if '小时' in match.group(0) or 'h' in match.group(0).lower():
                heavy_hours = val
            else:
                heavy_hours = val * 24
            break
    
    # 归一化计算
    # 典型模式：最多30天得10分
    typical_score = min(typical_days / 30 * 10, 10)
    
    # GPS模式：最多50小时得10分
    gps_score = min(gps_hours / 50 * 10, 10)
    
    # 重度使用：最多5天(120小时)得10分
    heavy_score = 5.0
    if heavy_hours:
        heavy_score = min(heavy_hours / 120 * 10, 10)
    
    # 加权平均（典型模式0.5，GPS模式0.3，重度使用0.2）
    final_score = typical_score * 0.5 + gps_score * 0.3 + heavy_score * 0.2
    
    return round(final_score, 2)

def clean_text(text):
    """文本清洗：去重、分词、停用词过滤 - 增强版"""
    if not text:
        return ""
    
    # 基础清洗
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
    
    # 去除重复字符
    text = re.sub(r'(.)\1{3,}', r'\1\1', text)
    
    # 分词
    words = jieba.cut(text)
    
    # 扩展停用词表
    stopwords = set([
        '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这',
        '那', '这个', '那个', '之', '与', '及', '等', '或', '但', '而', '因为', '所以', '如果', '虽然', '但是', '而且', '并且', '或者', '还是', '要么',
        '可以', '应该', '需要', '能够', '可能', '已经', '正在', '曾经', '现在', '当时', '后来', '以前', '以后', '之间', '其中', '这里', '那里', '哪里',
        '什么', '怎么', '为什么', '如何', '谁', '哪', '多少', '几', '个', '种', '类', '些', '点', '些', '下', '中', '大', '小', '多', '少', '高', '低',
        '买', '用', '感觉', '觉得', '认为', '觉得', '使用', '东西', '产品', '商品', '手环', '手表', '设备', '商家', '卖家', '快递', '物流', '包装'
    ])
    
    # 过滤停用词、短词和纯数字
    cleaned = []
    for w in words:
        w = w.strip()
        if len(w) > 1 and w not in stopwords and not re.match(r'^\d+$', w):
            cleaned.append(w)
    
    return ' '.join(cleaned)

# ==================== 产品全景画像模块 ====================

def analyze_sentiment(text):
    """使用SnowNLP进行情感分析，返回0-1之间的情感得分"""
    if not text:
        return 0.5
    try:
        s = SnowNLP(text)
        return round(s.sentiments, 3)
    except:
        return 0.5

def analyze_dimension_sentiment(reviews, dimension_keywords):
    """分析特定维度的情感倾向"""
    relevant_texts = []
    for review in reviews:
        comment = review.get('comment', '')
        for keyword in dimension_keywords:
            if keyword in comment:
                relevant_texts.append(comment)
                break
    
    if not relevant_texts:
        return {'sentiment': 0.5, 'count': 0}
    
    sentiments = [analyze_sentiment(text) for text in relevant_texts]
    avg_sentiment = sum(sentiments) / len(sentiments)
    
    return {
        'sentiment': round(avg_sentiment, 3),
        'count': len(relevant_texts)
    }

def extract_keywords(text_list, top_k=20):
    """使用jieba+TF-IDF提取关键词"""
    if not text_list:
        return []
    
    all_text = ' '.join(text_list)
    keywords = jieba.analyse.extract_tags(all_text, topK=top_k, withWeight=True)
    return [{'word': word, 'weight': round(weight, 4)} for word, weight in keywords]

def extract_pros_cons(reviews):
    """提取产品优缺点 - 增强版（基于维度分类）"""
    # 维度关键词定义
    dimension_keywords = {
        'battery': ['续航', '电池', '电量', '充电', '待机', '使用时间'],
        'comfort': ['舒适', '佩戴', '手感', '重量', '轻', '腕带', '表带'],
        'accuracy': ['准确', '精准', '误差', '测量', '数据', '监测精度'],
        'appearance': ['外观', '颜值', '好看', '屏幕', '设计', '颜色', '款式'],
        'function': ['功能', '运动模式', '健康监测', '防水', 'GPS', 'NFC'],
        'price': ['价格', '性价比', '便宜', '贵', '划算', '值得']
    }
    
    # 情感词库
    positive_keywords = [
        '好', '不错', '满意', '喜欢', '推荐', '值', '棒', '优秀', '舒适', '准确', '方便',
        '漂亮', '好看', '精致', '实用', '强大', '灵敏', '清晰', '流畅', '耐用', '稳定',
        '给力', '完美', '惊喜', '超预期', '性价比高', '值得买', '好评', '点赞'
    ]
    negative_keywords = [
        '差', '不好', '失望', '问题', '缺点', '贵', '慢', '卡', '不准', '麻烦', '后悔',
        '糟糕', '垃圾', '鸡肋', '没用', '难看', '粗糙', '失灵', '断连', '耗电快',
        '不值', '坑', '差评', '吐槽', '失望', '退货', '踩雷'
    ]
    
    # 按维度分类优缺点
    dimension_pros_cons = {}
    
    for dim_name, keywords in dimension_keywords.items():
        pros = []
        cons = []
        
        for review in reviews:
            comment = review.get('comment', '')
            sentiment = analyze_sentiment(comment)
            
            # 检查是否与当前维度相关
            is_relevant = any(kw in comment for kw in keywords)
            if not is_relevant:
                continue
            
            # 提取观点句
            sentences = re.split(r'[。！？]', comment)
            for sent in sentences:
                if len(sent) < 5:
                    continue
                
                # 检查句子是否包含维度关键词
                if not any(kw in sent for kw in keywords):
                    continue
                
                # 情感分析
                pos_count = sum(1 for kw in positive_keywords if kw in sent)
                neg_count = sum(1 for kw in negative_keywords if kw in sent)
                
                if pos_count > neg_count and sentiment > 0.55:
                    pros.append(sent.strip())
                elif neg_count > pos_count and sentiment < 0.45:
                    cons.append(sent.strip())
        
        # 统计高频观点
        pros_counter = Counter(pros)
        cons_counter = Counter(cons)
        
        dimension_pros_cons[dim_name] = {
            'pros': [{'text': text, 'count': count} for text, count in pros_counter.most_common(3)],
            'cons': [{'text': text, 'count': count} for text, count in cons_counter.most_common(3)]
        }
    
    # 汇总所有优缺点
    all_pros = []
    all_cons = []
    for dim_data in dimension_pros_cons.values():
        all_pros.extend([p['text'] for p in dim_data['pros']])
        all_cons.extend([c['text'] for c in dim_data['cons']])
    
    all_pros_counter = Counter(all_pros)
    all_cons_counter = Counter(all_cons)
    
    return {
        'by_dimension': dimension_pros_cons,
        'summary': {
            'pros': [{'text': text, 'count': count} for text, count in all_pros_counter.most_common(5)],
            'cons': [{'text': text, 'count': count} for text, count in all_cons_counter.most_common(5)]
        }
    }


def create_product_portrait(product, reviews):
    """创建产品全景画像"""
    # 基础信息
    specs = product.get('specs', '')
    features = extract_health_features(specs)
    
    # 计算综合满意度得分
    if reviews:
        sentiments = [analyze_sentiment(r.get('comment', '')) for r in reviews]
        overall_satisfaction = round(sum(sentiments) / len(sentiments) * 10, 2)
        review_count = len(reviews)
    else:
        overall_satisfaction = 5.0
        review_count = 0
    
    # 四大维度情感分析
    dimension_analysis = {
        'battery': analyze_dimension_sentiment(reviews, ['续航', '电池', '电量', '充电']),
        'comfort': analyze_dimension_sentiment(reviews, ['舒适', '佩戴', '手感', '重量', '轻']),
        'accuracy': analyze_dimension_sentiment(reviews, ['准确', '精准', '误差', '测量']),
        'appearance': analyze_dimension_sentiment(reviews, ['外观', '颜值', '好看', '屏幕'])
    }
    
    # 转换情感得分为0-10分
    for dim in dimension_analysis:
        dimension_analysis[dim]['score'] = round(dimension_analysis[dim]['sentiment'] * 10, 2)
    
    # 提取关键词
    review_texts = [r.get('comment', '') for r in reviews if r.get('comment')]
    keywords = extract_keywords(review_texts, top_k=20)
    
    # 提取优缺点
    pros_cons = extract_pros_cons(reviews)
    
    # 续航指数
    battery_score = calculate_battery_score(specs)
    
    # 健康功能覆盖度
    feature_coverage = round(sum(features.values()) / len(features) * 100, 1)
    
    return {
        'product_id': product.get('id'),
        'product_name': product.get('name'),
        'brand': product.get('brand'),
        'price': product.get('price'),
        'overall_satisfaction': overall_satisfaction,
        'review_count': review_count,
        'dimension_scores': dimension_analysis,
        'keywords': keywords,
        'pros_cons': pros_cons,
        'battery_score': battery_score,
        'feature_coverage': feature_coverage,
        'features': features,
        'feature_count': sum(features.values())
    }

# ==================== 智能决策支持引擎 ====================

# 预设场景权重配置
SCENARIO_WEIGHTS = {
    'health_focus': {
        'name': '健康预警关注',
        'weights': {
            'health_breadth': 35,    # 健康功能广度
            'data_accuracy': 30,     # 数据精准度
            'battery_life': 15,      # 续航能力
            'comfort': 10,           # 佩戴舒适度
            'brand_reputation': 5,   # 品牌口碑
            'price_performance': 5   # 性价比
        }
    },
    'battery_focus': {
        'name': '长续航刚需',
        'weights': {
            'health_breadth': 10,
            'data_accuracy': 10,
            'battery_life': 40,
            'comfort': 15,
            'brand_reputation': 10,
            'price_performance': 15
        }
    },
    'balanced': {
        'name': '均衡之选',
        'weights': {
            'health_breadth': 20,
            'data_accuracy': 20,
            'battery_life': 20,
            'comfort': 15,
            'brand_reputation': 15,
            'price_performance': 10
        }
    },
    'budget': {
        'name': '性价比优先',
        'weights': {
            'health_breadth': 15,
            'data_accuracy': 15,
            'battery_life': 20,
            'comfort': 10,
            'brand_reputation': 10,
            'price_performance': 30
        }
    }
}

def calculate_product_score(product, reviews, weights):
    """基于权重计算产品综合得分"""
    # 解析价格
    price_str = product.get('price', '0')
    price = float(re.sub(r'[^\d.]', '', price_str)) if price_str else 0
    
    # 健康功能广度得分
    specs = product.get('specs', '')
    features = extract_health_features(specs)
    health_breadth_score = sum(features.values()) / len(features) * 10
    
    # 数据精准度得分（基于评论情感）
    if reviews:
        sentiments = [analyze_sentiment(r.get('comment', '')) for r in reviews]
        data_accuracy_score = sum(sentiments) / len(sentiments) * 10
    else:
        data_accuracy_score = 5.0
    
    # 续航能力得分
    battery_score = calculate_battery_score(specs)
    
    # 舒适度得分
    comfort_analysis = analyze_dimension_sentiment(reviews, ['舒适', '佩戴', '手感', '重量', '轻'])
    comfort_score = comfort_analysis['sentiment'] * 10
    
    # 品牌口碑得分
    brand_analysis = analyze_dimension_sentiment(reviews, ['品牌', '质量', '服务', '售后'])
    brand_score = brand_analysis['sentiment'] * 10
    
    # 性价比得分（功能数/价格，归一化）
    if price > 0:
        price_performance = min(sum(features.values()) / (price / 1000) * 2, 10)
    else:
        price_performance = 5.0
    
    # 加权计算
    total_score = (
        health_breadth_score * weights['health_breadth'] / 100 +
        data_accuracy_score * weights['data_accuracy'] / 100 +
        battery_score * weights['battery_life'] / 100 +
        comfort_score * weights['comfort'] / 100 +
        brand_score * weights['brand_reputation'] / 100 +
        price_performance * weights['price_performance'] / 100
    )
    
    return {
        'total_score': round(total_score, 2),
        'details': {
            'health_breadth': round(health_breadth_score, 2),
            'data_accuracy': round(data_accuracy_score, 2),
            'battery_life': round(battery_score, 2),
            'comfort': round(comfort_score, 2),
            'brand_reputation': round(brand_score, 2),
            'price_performance': round(price_performance, 2)
        },
        'features': features
    }

# ==================== 协同过滤推荐引擎 ====================

def get_user_behavior_matrix(session_id=None):
    """获取用户-产品行为矩阵"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    if session_id:
        # 获取当前用户行为
        cursor.execute("""
            SELECT session_id, wristband_id, SUM(score) as total_score
            FROM user_behaviors
            WHERE session_id = %s
            GROUP BY session_id, wristband_id
        """, (session_id,))
        current_user = cursor.fetchall()
        
        # 获取其他用户行为（用于找相似用户）
        cursor.execute("""
            SELECT session_id, wristband_id, SUM(score) as total_score
            FROM user_behaviors
            WHERE session_id != %s
            GROUP BY session_id, wristband_id
        """, (session_id,))
        other_users = cursor.fetchall()
    else:
        # 无session时使用所有用户数据
        cursor.execute("""
            SELECT session_id, wristband_id, SUM(score) as total_score
            FROM user_behaviors
            GROUP BY session_id, wristband_id
        """)
        current_user = []
        other_users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return current_user, other_users

def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    if not vec1 or not vec2:
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def collaborative_filtering_recommend(session_id, top_n=10):
    """
    基于用户的协同过滤推荐 - 增强版
    
    改进点：
    1. 使用皮尔逊相关系数替代余弦相似度
    2. 添加相似度阈值过滤
    3. 实现基于物品的协同过滤作为备选
    4. 添加多样性控制
    
    步骤：
    1. 构建用户-产品评分矩阵
    2. 计算当前用户与所有其他用户的相似度（皮尔逊相关系数）
    3. 找到最相似的K个用户（相似度 > 阈值）
    4. 根据相似用户的喜好推荐产品
    5. 控制推荐结果的多样性
    """
    current_user_behaviors, other_users = get_user_behavior_matrix(session_id)
    
    # 如果行为数据太少，回退到加权推荐
    if len(other_users) < 5 or len(current_user_behaviors) < 2:
        return None, "行为数据不足，使用加权推荐"
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取所有产品
    cursor.execute("SELECT id, name, brand, price, image_url FROM wristbands")
    all_products = cursor.fetchall()
    product_ids = [p['id'] for p in all_products]
    
    # 获取产品品牌信息（用于多样性控制）
    product_brands = {p['id']: p.get('brand', '未知') for p in all_products}
    
    cursor.close()
    conn.close()
    
    # 构建用户行为字典 {session_id: {product_id: score}}
    user_profiles = {}
    
    # 添加当前用户
    user_profiles['current'] = {b['wristband_id']: float(b['total_score']) for b in current_user_behaviors}
    
    # 添加其他用户
    for behavior in other_users:
        sid = behavior['session_id']
        if sid not in user_profiles:
            user_profiles[sid] = {}
        user_profiles[sid][behavior['wristband_id']] = float(behavior['total_score'])
    
    # 计算当前用户与其他用户的相似度（使用皮尔逊相关系数）
    current_profile = user_profiles['current']
    similarities = []
    
    for sid, profile in user_profiles.items():
        if sid == 'current':
            continue
        
        # 找到共同评分的产品
        common_products = set(current_profile.keys()) & set(profile.keys())
        if len(common_products) < 2:
            continue
        
        # 构建共同评分向量
        current_ratings = [current_profile[pid] for pid in common_products]
        other_ratings = [profile[pid] for pid in common_products]
        
        # 计算皮尔逊相关系数
        sim = pearson_correlation(current_ratings, other_ratings)
        
        # 相似度阈值过滤（只保留正相关）
        if sim > 0.1:
            similarities.append((sid, sim, profile))
    
    # 按相似度排序，取Top K相似用户
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_k_similar_users = similarities[:15]  # 取前15个相似用户
    
    if not top_k_similar_users:
        return None, "未找到相似用户，使用加权推荐"
    
    # 根据相似用户预测评分
    product_scores = {}
    for pid in product_ids:
        if pid in current_profile:
            continue  # 已评分的跳过
        
        weighted_sum = 0
        sim_sum = 0
        
        for sid, sim, profile in top_k_similar_users:
            if pid in profile:
                weighted_sum += sim * profile[pid]
                sim_sum += abs(sim)
        
        if sim_sum > 0:
            product_scores[pid] = weighted_sum / sim_sum
    
    # 按预测评分排序
    sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)
    
    # 多样性控制：限制同一品牌的产品数量
    brand_count = {}
    diverse_recommendations = []
    
    for pid, score in sorted_products:
        brand = product_brands.get(pid, '未知')
        brand_count[brand] = brand_count.get(brand, 0) + 1
        
        # 每个品牌最多推荐3个产品
        if brand_count[brand] <= 3:
            diverse_recommendations.append((pid, score))
        
        if len(diverse_recommendations) >= top_n * 2:  # 多取一些用于后续排序
            break
    
    # 构建推荐结果
    recommendations = []
    for pid, score in diverse_recommendations[:top_n]:
        product = next((p for p in all_products if p['id'] == pid), None)
        if product:
            product['cf_score'] = round(score, 2)
            recommendations.append(product)
    
    return recommendations, None


def pearson_correlation(x, y):
    """计算皮尔逊相关系数"""
    n = len(x)
    if n == 0:
        return 0.0
    
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi ** 2 for xi in x)
    sum_y2 = sum(yi ** 2 for yi in y)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def hybrid_recommend(session_id, weights, top_n=20):
    """
    混合推荐：协同过滤 + 加权评分
    
    融合策略：
    - 如果行为数据充足：CF权重40%，加权评分权重60%
    - 如果行为数据不足：完全使用加权评分
    """
    cf_recommendations, cf_message = collaborative_filtering_recommend(session_id, top_n)
    
    # 获取加权评分结果
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM wristbands")
    products = cursor.fetchall()
    
    results = []
    for product in products:
        cursor.execute("SELECT * FROM reviews WHERE wristband_id = %s", (product['id'],))
        reviews = cursor.fetchall()
        score_data = calculate_product_score(product, reviews, weights)
        results.append({
            'id': product['id'],
            'brand': product.get('brand', ''),
            'name': product.get('name', ''),
            'price': product.get('price', ''),
            'score': score_data['total_score'],
            'score_details': score_data['details'],
            'features': score_data['features']
        })
    
    cursor.close()
    conn.close()
    
    # 按加权评分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 如果有CF结果，进行混合
    if cf_recommendations and cf_message is None:
        # 建立加权结果的映射
        score_map = {r['id']: r['score'] for r in results}
        max_weighted_score = max(score_map.values()) if score_map else 1
        
        # 混合评分
        hybrid_results = []
        for r in results:
            cf_score = 0
            for cf_rec in cf_recommendations:
                if cf_rec['id'] == r['id']:
                    # CF分数归一化到0-10范围
                    max_cf = max([c['cf_score'] for c in cf_recommendations]) if cf_recommendations else 1
                    cf_score = (cf_rec['cf_score'] / max_cf * 10) if max_cf > 0 else 0
                    break
            
            # 混合评分：加权60% + CF40%
            hybrid_score = r['score'] * 0.6 + cf_score * 0.4
            r['hybrid_score'] = round(hybrid_score, 2)
            r['cf_score'] = round(cf_score, 2)
            hybrid_results.append(r)
        
        hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return hybrid_results[:top_n], {'cf_used': True, 'cf_weight': 0.4, 'weighted_weight': 0.6}
    
    # 无CF数据，返回纯加权结果
    for r in results:
        r['hybrid_score'] = r['score']
        r['cf_score'] = None
    
    return results[:top_n], {'cf_used': False, 'message': cf_message}

# ==================== 路由定义 ====================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    """获取所有产品列表"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT * FROM wristbands ORDER BY id DESC LIMIT 100")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(products)

@app.route('/api/product/<int:product_id>')
def get_product_detail(product_id):
    """获取产品详情"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取产品信息
    cursor.execute("SELECT * FROM wristbands WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # 获取评论
    cursor.execute("SELECT * FROM reviews WHERE wristband_id = %s", (product_id,))
    reviews = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 分析数据
    features = extract_health_features(product.get('specs', ''))
    battery_score = calculate_battery_score(product.get('specs', ''))
    
    # 情感分析
    dimension_analysis = {
        'battery': analyze_dimension_sentiment(reviews, ['续航', '电池', '电量', '充电']),
        'comfort': analyze_dimension_sentiment(reviews, ['舒适', '佩戴', '手感', '重量']),
        'accuracy': analyze_dimension_sentiment(reviews, ['准确', '精准', '误差', '测量']),
        'appearance': analyze_dimension_sentiment(reviews, ['外观', '颜值', '好看', '屏幕'])
    }
    
    # 关键词提取
    review_texts = [r.get('comment', '') for r in reviews if r.get('comment')]
    keywords = extract_keywords(review_texts, top_k=15)
    
    # 优缺点
    pros_cons = extract_pros_cons(reviews)
    
    return jsonify({
        'product': product,
        'reviews_count': len(reviews),
        'features': features,
        'battery_score': battery_score,
        'dimension_analysis': dimension_analysis,
        'keywords': keywords,
        'pros_cons': pros_cons
    })

@app.route('/api/product/<int:product_id>/portrait')
def get_product_portrait(product_id):
    """获取产品全景画像"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取产品信息
    cursor.execute("SELECT * FROM wristbands WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # 获取评论
    cursor.execute("SELECT * FROM reviews WHERE wristband_id = %s", (product_id,))
    reviews = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 创建产品全景画像
    portrait = create_product_portrait(product, reviews)
    
    return jsonify(portrait)

@app.route('/api/market/overview')
def get_market_overview():
    """市场格局概览数据 - 增强版（支持箱线图和堆叠柱状图）"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取所有产品数据
    cursor.execute("SELECT brand, price, specs FROM wristbands WHERE price IS NOT NULL")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 品牌价格分布（用于箱线图）
    brand_prices = {}
    for p in products:
        brand = p.get('brand', '未知')
        price_str = p.get('price', '0')
        try:
            price = float(re.sub(r'[^\d.]', '', price_str))
            if price <= 0:
                continue
            if brand not in brand_prices:
                brand_prices[brand] = []
            brand_prices[brand].append(price)
        except:
            continue
    
    # 计算箱线图数据（min, Q1, median, Q3, max）
    brand_boxplot_data = []
    brand_names = []
    for brand, prices in sorted(brand_prices.items(), key=lambda x: len(x[1]), reverse=True)[:10]:  # 取前10品牌
        if len(prices) >= 3:
            prices_sorted = sorted(prices)
            n = len(prices_sorted)
            
            min_val = prices_sorted[0]
            max_val = prices_sorted[-1]
            median = prices_sorted[n // 2]
            q1 = prices_sorted[n // 4]
            q3 = prices_sorted[3 * n // 4]
            
            brand_names.append(brand)
            brand_boxplot_data.append({
                'brand': brand,
                'box_data': [min_val, q1, median, q3, max_val],
                'count': n,
                'avg': round(sum(prices) / len(prices), 2)
            })
    
    # 价格段位定义
    price_ranges = [
        {'label': '0-500元', 'min': 0, 'max': 500},
        {'label': '500-1000元', 'min': 500, 'max': 1000},
        {'label': '1000-2000元', 'min': 1000, 'max': 2000},
        {'label': '2000元以上', 'min': 2000, 'max': float('inf')}
    ]
    
    # 计算各价格段位的功能渗透率
    feature_penetration = {}
    for feature_key in HEALTH_FEATURES.keys():
        feature_penetration[feature_key] = {r['label']: {'total': 0, 'has_feature': 0} for r in price_ranges}
    
    for p in products:
        price_str = p.get('price', '0')
        specs = p.get('specs', '')
        try:
            price = float(re.sub(r'[^\d.]', '', price_str))
            if price <= 0:
                continue
            
            # 确定价格段位
            price_range_label = None
            for r in price_ranges:
                if r['min'] <= price < r['max']:
                    price_range_label = r['label']
                    break
            
            if price_range_label:
                features = extract_health_features(specs)
                for feature_key, has_feature in features.items():
                    feature_penetration[feature_key][price_range_label]['total'] += 1
                    if has_feature:
                        feature_penetration[feature_key][price_range_label]['has_feature'] += 1
        except:
            continue
    
    # 计算渗透率百分比
    penetration_data = []
    feature_labels = {
        'heart_rate': '心率监测', 'sleep': '睡眠监测', 'blood_oxygen': '血氧检测',
        'stress': '压力监测', 'body_temp': '体温监测', 'ecg': '心电图',
        'blood_pressure': '血压监测', 'blood_sugar': '血糖监测', 'gps': 'GPS定位',
        'nfc': 'NFC支付', 'water_resist': '防水', 'bluetooth_call': '蓝牙通话',
        'sports_mode': '运动模式', 'menstrual': '女性健康', 'breathing': '呼吸训练'
    }
    
    for feature_key, data in feature_penetration.items():
        penetration_rates = []
        for r in price_ranges:
            label = r['label']
            total = data[label]['total']
            has = data[label]['has_feature']
            rate = round(has / total * 100, 1) if total > 0 else 0
            penetration_rates.append(rate)
        
        if feature_key in feature_labels:
            penetration_data.append({
                'feature_key': feature_key,
                'feature_name': feature_labels.get(feature_key, feature_key),
                'penetration_rates': penetration_rates
            })
    
    return jsonify({
        'brand_boxplot': {
            'brands': brand_names,
            'data': brand_boxplot_data
        },
        'feature_penetration': {
            'price_ranges': [r['label'] for r in price_ranges],
            'features': penetration_data
        },
        'summary': {
            'total_products': len(products),
            'brand_count': len(brand_prices)
        }
    })

@app.route('/api/scenarios')
def get_scenarios():
    """获取预设场景配置"""
    return jsonify(SCENARIO_WEIGHTS)

@app.route('/api/recommend', methods=['POST'])
def recommend():
    """智能推荐接口 - 混合推荐（协同过滤 + 加权评分）"""
    data = request.json
    scenario = data.get('scenario', 'balanced')
    custom_weights = data.get('weights', None)
    session_id = request.headers.get('X-Session-ID', request.cookies.get('session_id'))
    
    # 获取权重配置
    if custom_weights:
        weights = custom_weights
    elif scenario in SCENARIO_WEIGHTS:
        weights = SCENARIO_WEIGHTS[scenario]['weights']
    else:
        weights = SCENARIO_WEIGHTS['balanced']['weights']
    
    # 混合推荐
    results, meta = hybrid_recommend(session_id, weights, top_n=20)
    
    return jsonify({
        'weights': weights,
        'recommendations': results,
        'meta': meta
    })

@app.route('/api/behavior', methods=['POST'])
def record_behavior():
    """记录用户行为（用于协同过滤）"""
    data = request.json
    wristband_id = data.get('wristband_id')
    behavior_type = data.get('behavior_type', 'view')  # view, compare, favorite, score
    score = data.get('score', 1)
    session_id = data.get('session_id') or request.headers.get('X-Session-ID')
    
    if not wristband_id or not session_id:
        return jsonify({'error': '缺少必要参数'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO user_behaviors (session_id, wristband_id, behavior_type, score)
        VALUES (%s, %s, %s, %s)
    """, (session_id, wristband_id, behavior_type, score))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '行为已记录'})

@app.route('/api/similar-products/<int:product_id>')
def get_similar_products(product_id):
    """获取相似产品（基于功能相似度）"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取目标产品
    cursor.execute("SELECT * FROM wristbands WHERE id = %s", (product_id,))
    target = cursor.fetchone()
    
    if not target:
        return jsonify({'error': '产品不存在'}), 404
    
    # 获取所有产品
    cursor.execute("SELECT * FROM wristbands WHERE id != %s", (product_id,))
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # 计算功能相似度
    target_features = extract_health_features(target.get('specs', ''))
    target_battery = calculate_battery_score(target.get('specs', ''))
    target_price = float(re.sub(r'[^\d.]', '', target.get('price', '0'))) if target.get('price') else 0
    
    similarities = []
    for p in products:
        p_features = extract_health_features(p.get('specs', ''))
        p_battery = calculate_battery_score(p.get('specs', ''))
        p_price = float(re.sub(r'[^\d.]', '', p.get('price', '0'))) if p.get('price') else 0
        
        # Jaccard相似度（功能）
        common_features = sum(1 for k in target_features if target_features[k] == p_features[k] == 1)
        total_features = sum(1 for k in target_features if target_features[k] == 1 or p_features[k] == 1)
        feature_sim = common_features / total_features if total_features > 0 else 0
        
        # 续航相似度
        battery_sim = 1 - abs(target_battery - p_battery) / 10
        
        # 价格相似度
        if target_price > 0 and p_price > 0:
            price_sim = 1 - abs(target_price - p_price) / max(target_price, p_price)
        else:
            price_sim = 0.5
        
        # 综合相似度
        overall_sim = feature_sim * 0.5 + battery_sim * 0.3 + price_sim * 0.2
        
        similarities.append({
            'id': p['id'],
            'name': p['name'],
            'brand': p.get('brand', ''),
            'price': p.get('price', ''),
            'similarity': round(overall_sim, 3)
        })
    
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return jsonify(similarities[:10])

@app.route('/api/compare', methods=['POST'])
def compare_products():
    """产品对比接口"""
    data = request.json
    product_ids = data.get('product_ids', [])
    
    if len(product_ids) < 2:
        return jsonify({'error': '至少需要选择2个产品进行对比'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    products_data = []
    for pid in product_ids[:4]:  # 最多对比4个产品
        cursor.execute("SELECT * FROM wristbands WHERE id = %s", (pid,))
        product = cursor.fetchone()
        
        if product:
            cursor.execute("SELECT * FROM reviews WHERE wristband_id = %s", (pid,))
            reviews = cursor.fetchall()
            
            features = extract_health_features(product.get('specs', ''))
            battery_score = calculate_battery_score(product.get('specs', ''))
            
            # 计算满意度
            if reviews:
                sentiments = [analyze_sentiment(r.get('comment', '')) for r in reviews]
                satisfaction = round(sum(sentiments) / len(sentiments) * 100, 1)
            else:
                satisfaction = 50.0
            
            # 计算详细评分
            score_data = calculate_product_score(product, reviews, {
                'health_breadth': 20, 'data_accuracy': 20, 'battery_life': 20,
                'comfort': 15, 'brand_reputation': 15, 'price_performance': 10
            })
            
            products_data.append({
                'id': product['id'],
                'brand': product.get('brand', ''),
                'name': product.get('name', ''),
                'price': product.get('price', ''),
                'features': features,
                'battery_score': battery_score,
                'satisfaction': satisfaction,
                'reviews_count': len(reviews),
                'score_details': score_data['details'],
                'total_score': score_data['total_score']
            })
    
    cursor.close()
    conn.close()
    
    return jsonify(products_data)

# ==================== 用户系统模块 ====================

@app.route('/api/user/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    nickname = data.get('nickname', username)
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, password, email, nickname) VALUES (%s, %s, %s, %s)",
            (username, password, email, nickname)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': {'id': user_id, 'username': username, 'nickname': nickname}
        })
    except pymysql.err.IntegrityError:
        return jsonify({'error': '用户名已存在'}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/user/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute(
        "SELECT id, username, nickname, email FROM users WHERE username = %s AND password = %s",
        (username, password)
    )
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        cursor.execute("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))
        conn.commit()
        
        return jsonify({
            'success': True,
            'user': user
        })
    else:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    cursor.close()
    conn.close()

@app.route('/api/user/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({'success': True, 'message': '登出成功'})

@app.route('/api/user/current')
def get_current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'user': {
                'id': session['user_id'],
                'username': session['username']
            }
        })
    return jsonify({'logged_in': False})

# ==================== 用户行为记录模块 ====================

@app.route('/api/user/behavior', methods=['POST'])
def record_user_behavior():
    """记录用户行为"""
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    data = request.json
    product_id = data.get('product_id')
    behavior_type = data.get('behavior_type')  # view, favorite, compare, search
    behavior_value = data.get('behavior_value', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO user_behaviors (user_id, product_id, behavior_type, behavior_value) VALUES (%s, %s, %s, %s)",
        (session['user_id'], product_id, behavior_type, behavior_value)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/user/favorites')
def get_favorites():
    """获取用户收藏"""
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT w.*, ub.created_at as favorited_at 
        FROM wristbands w
        JOIN user_behaviors ub ON w.id = ub.product_id
        WHERE ub.user_id = %s AND ub.behavior_type = 'favorite'
        ORDER BY ub.created_at DESC
    """, (session['user_id'],))
    
    favorites = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(favorites)

@app.route('/api/user/history')
def get_history():
    """获取用户浏览历史"""
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT w.*, ub.behavior_type, ub.created_at
        FROM wristbands w
        JOIN user_behaviors ub ON w.id = ub.product_id
        WHERE ub.user_id = %s
        ORDER BY ub.created_at DESC
        LIMIT 50
    """, (session['user_id'],))
    
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(history)

# ==================== 协同过滤推荐模块 ====================

def get_user_behavior_matrix():
    """获取用户-产品行为矩阵"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取所有用户行为（包括浏览、收藏、评分）
    cursor.execute("""
        SELECT user_id, product_id, 
               CASE behavior_type
                   WHEN 'favorite' THEN 5
                   WHEN 'compare' THEN 3
                   WHEN 'view' THEN 1
                   ELSE 1
               END as weight
        FROM user_behaviors
        UNION ALL
        SELECT user_id, product_id, rating as weight
        FROM user_ratings
    """)
    
    behaviors = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # 构建用户-产品矩阵
    user_product_matrix = {}
    for b in behaviors:
        user_id = b['user_id']
        product_id = b['product_id']
        weight = float(b['weight'])
        
        if user_id not in user_product_matrix:
            user_product_matrix[user_id] = {}
        
        if product_id in user_product_matrix[user_id]:
            user_product_matrix[user_id][product_id] += weight
        else:
            user_product_matrix[user_id][product_id] = weight
    
    return user_product_matrix

def calculate_user_similarity(user_matrix, target_user_id):
    """计算用户相似度（余弦相似度）"""
    if target_user_id not in user_matrix:
        return {}
    
    target_vector = user_matrix[target_user_id]
    similarities = {}
    
    for user_id, user_vector in user_matrix.items():
        if user_id == target_user_id:
            continue
        
        # 找到共同交互的产品
        common_products = set(target_vector.keys()) & set(user_vector.keys())
        
        if not common_products:
            continue
        
        # 计算余弦相似度
        dot_product = sum(target_vector[p] * user_vector[p] for p in common_products)
        
        target_norm = math.sqrt(sum(v**2 for v in target_vector.values()))
        user_norm = math.sqrt(sum(v**2 for v in user_vector.values()))
        
        if target_norm == 0 or user_norm == 0:
            continue
        
        similarity = dot_product / (target_norm * user_norm)
        
        if similarity > 0:
            similarities[user_id] = similarity
    
    return similarities

def collaborative_filtering_recommend(target_user_id, n_recommendations=10):
    """基于用户的协同过滤推荐"""
    user_matrix = get_user_behavior_matrix()
    
    if target_user_id not in user_matrix:
        return []
    
    # 计算相似用户
    similarities = calculate_user_similarity(user_matrix, target_user_id)
    
    if not similarities:
        return []
    
    # 获取相似度最高的K个用户
    k = min(5, len(similarities))
    similar_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:k]
    
    # 收集推荐候选
    target_products = set(user_matrix[target_user_id].keys())
    recommendations = {}
    
    for similar_user_id, similarity in similar_users:
        for product_id, weight in user_matrix[similar_user_id].items():
            if product_id in target_products:
                continue
            
            if product_id not in recommendations:
                recommendations[product_id] = 0
            
            recommendations[product_id] += similarity * weight
    
    # 排序并返回前N个
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    
    return [product_id for product_id, score in sorted_recommendations[:n_recommendations]]

@app.route('/api/recommend/collaborative')
def get_collaborative_recommendations():
    """获取协同过滤推荐"""
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    user_id = session['user_id']
    recommended_ids = collaborative_filtering_recommend(user_id, n_recommendations=10)
    
    if not recommended_ids:
        return jsonify({
            'message': '基于您的浏览历史推荐（协同过滤数据不足）',
            'recommendations': [],
            'fallback': True
        })
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 获取推荐产品详情
    format_ids = ','.join(['%s'] * len(recommended_ids))
    cursor.execute(f"""
        SELECT w.*, 
               (SELECT COUNT(*) FROM reviews WHERE wristband_id = w.id) as review_count
        FROM wristbands w
        WHERE w.id IN ({format_ids})
    """, tuple(recommended_ids))
    
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # 按推荐顺序排序
    product_dict = {p['id']: p for p in products}
    sorted_products = [product_dict[pid] for pid in recommended_ids if pid in product_dict]
    
    return jsonify({
        'message': '基于相似用户的协同过滤推荐',
        'recommendations': sorted_products,
        'fallback': False
    })

@app.route('/api/recommend/hybrid')
def get_hybrid_recommendations():
    """混合推荐（加权评分 + 协同过滤）"""
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    user_id = session['user_id']
    
    # 获取用户偏好权重
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT * FROM user_preferences 
        WHERE user_id = %s AND is_default = TRUE
        LIMIT 1
    """, (user_id,))
    
    pref = cursor.fetchone()
    
    if pref:
        weights = {
            'health_breadth': pref['health_breadth'],
            'data_accuracy': pref['data_accuracy'],
            'battery_life': pref['battery_life'],
            'comfort': pref['comfort'],
            'brand_reputation': pref['brand_reputation'],
            'price_performance': pref['price_performance']
        }
    else:
        weights = SCENARIO_WEIGHTS['balanced']['weights']
    
    # 获取协同过滤推荐
    cf_ids = collaborative_filtering_recommend(user_id, n_recommendations=20)
    
    # 获取所有产品并计算加权评分
    cursor.execute("SELECT * FROM wristbands")
    products = cursor.fetchall()
    
    results = []
    cf_set = set(cf_ids)
    
    for product in products:
        cursor.execute("SELECT * FROM reviews WHERE wristband_id = %s", (product['id'],))
        reviews = cursor.fetchall()
        
        score_data = calculate_product_score(product, reviews, weights)
        
        # 协同过滤加成
        cf_bonus = 0.5 if product['id'] in cf_set else 0
        final_score = score_data['total_score'] + cf_bonus
        
        results.append({
            'id': product['id'],
            'brand': product.get('brand', ''),
            'name': product.get('name', ''),
            'price': product.get('price', ''),
            'score': round(final_score, 2),
            'cf_recommended': product['id'] in cf_set,
            'score_details': score_data['details'],
            'features': score_data['features']
        })
    
    cursor.close()
    conn.close()
    
    # 按得分排序
    results.sort(key=lambda x: (x['cf_recommended'], x['score']), reverse=True)
    
    return jsonify({
        'weights': weights,
        'cf_influence': '协同过滤产品获得额外加分',
        'recommendations': results[:20]
    })

# ==================== 用户偏好设置 ====================

@app.route('/api/user/preference', methods=['GET', 'POST'])
def user_preference():
    """获取或保存用户偏好"""
    if 'user_id' not in session:
        return jsonify({'error': '请先登录'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'GET':
        cursor.execute("""
            SELECT * FROM user_preferences WHERE user_id = %s
        """, (user_id,))
        prefs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(prefs)
    
    else:  # POST
        data = request.json
        pref_name = data.get('name', '默认偏好')
        
        cursor.execute("""
            INSERT INTO user_preferences 
            (user_id, preference_name, health_breadth, data_accuracy, battery_life, 
             comfort, brand_reputation, price_performance, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            health_breadth = VALUES(health_breadth),
            data_accuracy = VALUES(data_accuracy),
            battery_life = VALUES(battery_life),
            comfort = VALUES(comfort),
            brand_reputation = VALUES(brand_reputation),
            price_performance = VALUES(price_performance),
            is_default = VALUES(is_default)
        """, (
            user_id, pref_name,
            data.get('health_breadth', 20),
            data.get('data_accuracy', 20),
            data.get('battery_life', 20),
            data.get('comfort', 15),
            data.get('brand_reputation', 15),
            data.get('price_performance', 10),
            data.get('is_default', False)
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '偏好设置已保存'})

# ==================== 产品搜索功能 ====================

@app.route('/api/search')
def search_products():
    """产品搜索接口"""
    keyword = request.args.get('keyword', '').strip()
    brand = request.args.get('brand', '').strip()
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    features = request.args.getlist('features')  # 健康功能筛选
    sort_by = request.args.get('sort', 'relevance')  # relevance, price_asc, price_desc, rating
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 构建查询条件
    conditions = ["1=1"]
    params = []
    
    if keyword:
        conditions.append("(name LIKE %s OR intro LIKE %s OR keywords LIKE %s)")
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword])
    
    if brand:
        conditions.append("brand = %s")
        params.append(brand)
    
    if min_price:
        conditions.append("CAST(REPLACE(REPLACE(price, '￥', ''), ',', '') AS DECIMAL) >= %s")
        params.append(float(min_price))
    
    if max_price:
        conditions.append("CAST(REPLACE(REPLACE(price, '￥', ''), ',', '') AS DECIMAL) <= %s")
        params.append(float(max_price))
    
    # 构建排序
    order_clause = "ORDER BY "
    if sort_by == 'price_asc':
        order_clause += "CAST(REPLACE(REPLACE(price, '￥', ''), ',', '') AS DECIMAL) ASC"
    elif sort_by == 'price_desc':
        order_clause += "CAST(REPLACE(REPLACE(price, '￥', ''), ',', '') AS DECIMAL) DESC"
    elif sort_by == 'rating':
        order_clause += "id DESC"  # 临时用id代替
    else:
        order_clause += "id DESC"
    
    # 执行查询
    query = f"SELECT * FROM wristbands WHERE {' AND '.join(conditions)} {order_clause} LIMIT 100"
    cursor.execute(query, params)
    products = cursor.fetchall()
    
    # 健康功能筛选（在Python中处理）
    if features and products:
        filtered_products = []
        for p in products:
            specs = p.get('specs', '')
            product_features = extract_health_features(specs)
            
            # 检查是否包含所有选中的功能
            has_all_features = all(product_features.get(f, 0) == 1 for f in features)
            if has_all_features:
                filtered_products.append(p)
        products = filtered_products
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'keyword': keyword,
        'total': len(products),
        'products': products
    })

@app.route('/api/brands')
def get_brands():
    """获取所有品牌列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT brand FROM wristbands WHERE brand IS NOT NULL AND brand != '' ORDER BY brand")
    brands = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return jsonify(brands)

# ==================== 参数排列对比功能 ====================

@app.route('/api/compare/advanced', methods=['POST'])
def advanced_compare():
    """高级参数对比 - 支持多产品多维度对比"""
    data = request.json
    product_ids = data.get('product_ids', [])
    compare_dimensions = data.get('dimensions', ['price', 'features', 'battery', 'rating'])
    
    if len(product_ids) < 2:
        return jsonify({'error': '至少需要选择2个产品进行对比'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    products_data = []
    
    for pid in product_ids[:6]:  # 最多对比6个产品
        cursor.execute("SELECT * FROM wristbands WHERE id = %s", (pid,))
        product = cursor.fetchone()
        
        if not product:
            continue
        
        cursor.execute("SELECT * FROM reviews WHERE wristband_id = %s", (pid,))
        reviews = cursor.fetchall()
        
        # 基础信息
        product_info = {
            'id': product['id'],
            'brand': product.get('brand', ''),
            'name': product.get('name', ''),
            'price': product.get('price', ''),
            'intro': product.get('intro', '')
        }
        
        # 根据对比维度添加数据
        if 'features' in compare_dimensions:
            specs = product.get('specs', '')
            product_info['features'] = extract_health_features(specs)
        
        if 'battery' in compare_dimensions:
            specs = product.get('specs', '')
            product_info['battery_score'] = calculate_battery_score(specs)
        
        if 'rating' in compare_dimensions:
            if reviews:
                sentiments = [analyze_sentiment(r.get('comment', '')) for r in reviews]
                product_info['satisfaction'] = round(sum(sentiments) / len(sentiments) * 100, 1)
                product_info['reviews_count'] = len(reviews)
            else:
                product_info['satisfaction'] = 50.0
                product_info['reviews_count'] = 0
        
        if 'specs' in compare_dimensions:
            product_info['specs'] = product.get('specs', '')[:500]
        
        products_data.append(product_info)
    
    cursor.close()
    conn.close()
    
    # 生成对比分析
    analysis = generate_comparison_analysis(products_data, compare_dimensions)
    
    return jsonify({
        'products': products_data,
        'dimensions': compare_dimensions,
        'analysis': analysis
    })

def generate_comparison_analysis(products, dimensions):
    """生成对比分析结果"""
    analysis = {
        'best_value': None,  # 性价比最高
        'most_features': None,  # 功能最全
        'best_battery': None,  # 续航最好
        'best_rating': None,  # 评分最高
        'recommendations': []
    }
    
    if not products:
        return analysis
    
    # 解析价格
    def parse_price(price_str):
        if not price_str:
            return float('inf')
        try:
            return float(re.sub(r'[^\d.]', '', str(price_str)))
        except:
            return float('inf')
    
    # 性价比最高（功能数/价格）
    if 'features' in dimensions and 'price' in dimensions:
        best_value_score = 0
        for p in products:
            price = parse_price(p.get('price'))
            if price > 0 and price != float('inf'):
                feature_count = sum(p.get('features', {}).values())
                value_score = feature_count / (price / 1000)
                if value_score > best_value_score:
                    best_value_score = value_score
                    analysis['best_value'] = p['id']
    
    # 功能最全
    if 'features' in dimensions:
        max_features = 0
        for p in products:
            feature_count = sum(p.get('features', {}).values())
            if feature_count > max_features:
                max_features = feature_count
                analysis['most_features'] = p['id']
    
    # 续航最好
    if 'battery' in dimensions:
        best_battery = 0
        for p in products:
            battery = p.get('battery_score', 0)
            if battery > best_battery:
                best_battery = battery
                analysis['best_battery'] = p['id']
    
    # 评分最高
    if 'rating' in dimensions:
        best_rating = 0
        for p in products:
            rating = p.get('satisfaction', 0)
            if rating > best_rating:
                best_rating = rating
                analysis['best_rating'] = p['id']
    
    # 生成推荐理由
    for p in products:
        reasons = []
        if p['id'] == analysis.get('best_value'):
            reasons.append('性价比最高')
        if p['id'] == analysis.get('most_features'):
            reasons.append('功能最全面')
        if p['id'] == analysis.get('best_battery'):
            reasons.append('续航能力最强')
        if p['id'] == analysis.get('best_rating'):
            reasons.append('用户口碑最好')
        
        if reasons:
            analysis['recommendations'].append({
                'product_id': p['id'],
                'product_name': p['name'],
                'reasons': reasons
            })
    
    return analysis

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
