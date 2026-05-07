# -*- coding: utf-8 -*-
"""
使用Playwright测试华为天猫页面
"""
import asyncio
import re
import json
from playwright.async_api import async_playwright


async def test_list_page():
    """测试列表页"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            url = 'https://huaweistore.tmall.com/category-1201482782-1662553168.htm?search=y&catName=%D6%C7%C4%DC%B4%A9%B4%F7'
            print(f'访问列表页: {url}')
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # 等待商品加载
            await page.wait_for_timeout(3000)
            
            # 提取商品链接
            links = await page.eval_on_selector_all(
                "a[href*='item.htm']",
                "elements => elements.map(e => e.href)"
            )
            
            product_ids = []
            for link in links:
                match = re.search(r'id=(\d+)', link)
                if match:
                    product_id = match.group(1)
                    if product_id not in product_ids:
                        product_ids.append(product_id)
            
            print(f'发现商品数量: {len(product_ids)}')
            print(f'商品ID示例: {product_ids[:5]}')
            
            return product_ids
            
        except Exception as e:
            print(f'错误: {e}')
            return []
        finally:
            await browser.close()


async def test_product_detail(product_id):
    """测试商品详情页"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            url = f'https://detail.tmall.com/item.htm?id={product_id}'
            print(f'\n访问商品详情页: {url}')
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # 等待页面加载
            await page.wait_for_timeout(5000)
            
            # 提取商品名称
            name_selectors = [
                'h1[data-spm="1000987"]',
                '.tb-detail-hd h1',
                'h1'
            ]
            name = ''
            for selector in name_selectors:
                try:
                    name = await page.text_content(selector, timeout=2000)
                    if name and name.strip():
                        name = name.strip()
                        break
                except:
                    continue
            
            print(f'商品名称: {name[:100]}...' if name else '未找到商品名称')
            
            # 提取价格
            price_selectors = [
                '.tm-price',
                '.notranslate',
                '[class*="price"]'
            ]
            price = ''
            for selector in price_selectors:
                try:
                    price_text = await page.text_content(selector, timeout=2000)
                    if price_text:
                        match = re.search(r'(\d+\.?\d*)', price_text.replace(',', ''))
                        if match:
                            price = match.group(1)
                            break
                except:
                    continue
            
            print(f'价格: {price}')
            
            # 提取评论关键词
            keywords = await page.eval_on_selector_all(
                ".rate-tag-inner span, .rate-tag-box span",
                "elements => elements.map(e => e.textContent.trim())"
            )
            
            if keywords:
                print(f'\n评论关键词 ({len(keywords)}个):')
                for kw in keywords[:5]:
                    print(f'  - {kw}')
            
            # 提取卖家ID
            content = await page.content()
            seller_match = re.search(r'sellerId["\']?\s*:\s*["\']?(\d+)', content)
            seller_id = seller_match.group(1) if seller_match else None
            
            if seller_id:
                print(f'\n卖家ID: {seller_id}')
            
            return seller_id
            
        except Exception as e:
            print(f'错误: {e}')
            return None
        finally:
            await browser.close()


async def main():
    print('=== 使用Playwright测试华为天猫爬虫 ===\n')
    
    # 测试列表页
    print('1. 测试列表页...')
    product_ids = await test_list_page()
    
    if product_ids:
        # 测试商品详情
        print('\n2. 测试商品详情页...')
        seller_id = await test_product_detail(product_ids[0])
    
    print('\n=== 测试完成 ===')


if __name__ == '__main__':
    asyncio.run(main())
