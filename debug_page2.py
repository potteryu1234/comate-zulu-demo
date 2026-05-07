# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(service=Service(), options=options)

url = 'https://detail.zol.com.cn/gpswatch/apple/'
print(f"Loading: {url}")
driver.get(url)
time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')

# 查找 .pic 元素
pics = soup.select('.pic')
print(f"\nFound {len(pics)} .pic elements")

if pics:
    for i, pic in enumerate(pics[:2]):
        print(f"\n--- Item {i+1} ---")
        # 查找a标签
        a_tag = pic.find('a', href=True)
        if a_tag:
            href = a_tag.get('href', '')
            print(f"Href: {href}")
            # 检查条件
            has_index = 'index' in href
            has_shtml = '.shtml' in href
            print(f"  Has 'index': {has_index}")
            print(f"  Has '.shtml': {has_shtml}")
            
            img = a_tag.find('img')
            if img:
                alt = img.get('alt', '')
                print(f"  Alt: {alt[:50]}")
        else:
            print("  No a tag found")

# 直接查找所有a标签
print("\n--- All links with index and shtml ---")
count = 0
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    if 'index' in href and '.shtml' in href:
        count += 1
        if count <= 3:
            print(f"Href: {href}")
            img = a.find('img')
            if img:
                print(f"  Alt: {img.get('alt', '')[:50]}")
print(f"Total matching links: {count}")

driver.quit()