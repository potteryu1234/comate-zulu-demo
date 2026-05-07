# -*- coding: utf-8 -*-
"""
华为天猫爬虫测试脚本
"""
import requests
import re
import json
from urllib.parse import urlencode


def test_list_page():
    """测试列表页解析"""
    url = 'https://huaweistore.tmall.com/category-1201482782-1662553168.htm?search=y&catName=%D6%C7%C4%DC%B4%A9%B4%F7'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f'列表页状态码: {response.status_code}')
        
        # 提取商品链接
        product_links = re.findall(r'href="(//detail\.tmall\.com/item\.htm[^"]+)"', response.text)
        print(f'发现商品链接数量: {len(product_links)}')
        
        # 提取商品ID
        product_ids = []
        for link in product_links[:5]:  # 只显示前5个
            match = re.search(r'id=(\d+)', link)
            if match:
                product_ids.append(match.group(1))
        
        print(f'商品ID示例: {product_ids[:5]}')
        return product_ids
        
    except Exception as e:
        print(f'请求失败: {e}')
        return []


def test_product_detail(product_id):
    """测试商品详情页"""
    url = f'https://detail.tmall.com/item.htm?id={product_id}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f'\n商品详情页状态码: {response.status_code}')
        
        # 提取商品名称
        name_match = re.search(r'<h1[^>]*>(.*?)</h1>', response.text, re.DOTALL)
        if name_match:
            name = re.sub(r'<[^>]+>', '', name_match.group(1)).strip()
            print(f'商品名称: {name[:100]}...')
        
        # 提取价格
        price_match = re.search(r'"defaultItemPrice":"([^"]+)"', response.text)
        if price_match:
            print(f'价格: {price_match.group(1)}')
        
        # 提取卖家ID
        seller_match = re.search(r'sellerId["\']?\s*:\s*["\']?(\d+)', response.text)
        if seller_match:
            seller_id = seller_match.group(1)
            print(f'卖家ID: {seller_id}')
            return seller_id
            
    except Exception as e:
        print(f'请求失败: {e}')
    
    return None


def test_reviews_api(item_id, seller_id):
    """测试评论API"""
    params = {
        'itemId': item_id,
        'sellerId': seller_id,
        'currentPage': 1,
        'pageSize': 20,
    }
    
    url = f'https://rate.tmall.com/list_detail_rate.htm?{urlencode(params)}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://detail.tmall.com/item.htm?id={item_id}',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f'\n评论API状态码: {response.status_code}')
        
        # 解析JSONP
        match = re.search(r'\((.*)\)', response.text, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            reviews = data.get('rateDetail', {}).get('rateList', [])
            print(f'获取评论数量: {len(reviews)}')
            
            for review in reviews[:3]:
                content = review.get('rateContent', '')
                rating = review.get('rate', 0)
                print(f'评分: {rating}, 评论: {content[:50]}...')
                
    except Exception as e:
        print(f'请求失败: {e}')


if __name__ == '__main__':
    print('=== 测试华为天猫爬虫 ===\n')
    
    # 测试列表页
    print('1. 测试列表页...')
    product_ids = test_list_page()
    
    if product_ids:
        # 测试商品详情
        print('\n2. 测试商品详情页...')
        seller_id = test_product_detail(product_ids[0])
        
        # 测试评论API
        if seller_id:
            print('\n3. 测试评论API...')
            test_reviews_api(product_ids[0], seller_id)
    
    print('\n=== 测试完成 ===')
