# -*- coding: utf-8 -*-
"""
调试脚本：检查列表页的产品链接格式
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(), options=options)
    return driver

def test_list_page():
    driver = init_driver()

    try:
        url = 'https://detail.zol.com.cn/gpswatch/apple/'
        print(f"Loading: {url}")
        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 查找所有.pic元素
        pics = soup.select('.pic')
        print(f"\nFound {len(pics)} .pic elements")

        if pics:
            print("\n=== First 5 product links ===")
            for i, pic in enumerate(pics[:5], 1):
                print(f"\n--- Product {i} ---")

                # 获取a标签
                a_tag = pic.find('a', href=True)
                if a_tag:
                    href = a_tag.get('href', '')
                    print(f"Href: {href}")

                    # 检查URL格式
                    if 'index' in href and '.shtml' in href:
                        import re
                        # 尝试不同的正则表达式
                        match1 = re.search(r'/(\d+)/index(\d+)\.shtml', href)
                        match2 = re.search(r'/(\w+)/index(\d+)\.shtml', href)
                        match3 = re.search(r'index(\d+)\.shtml', href)

                        print(f"  Match /category_id/indexID.shtml: {match1.group() if match1 else 'No match'}")
                        print(f"  Match /category_name/indexID.shtml: {match2.group() if match2 else 'No match'}")
                        print(f"  Match indexID.shtml: {match3.group() if match3 else 'No match'}")

                        if match3:
                            product_id = match3.group(1)
                            print(f"  Product ID: {product_id}")

                            # 构造可能的详情页URL
                            url1 = f"https://detail.zol.com.cn/GPSwatch/index{product_id}.shtml"
                            url2 = f"https://detail.zol.com.cn/2142/index{product_id}.shtml"
                            print(f"  Possible URL 1 (GPSwatch): {url1}")
                            print(f"  Possible URL 2 (2142): {url2}")

                # 获取图片
                img = pic.find('img')
                if img:
                    alt = img.get('alt', '')
                    src = img.get('src', '')
                    print(f"  Name: {alt[:60]}")
                    print(f"  Image src: {src[:80]}")
        else:
            print("No .pic elements found!")

            # 尝试查找其他可能的产品链接容器
            print("\n=== Trying to find product links ===")
            for link in soup.find_all('a', href=True)[:10]:
                href = link.get('href', '')
                if 'index' in href and '.shtml' in href:
                    print(f"Found link: {href}")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_list_page()