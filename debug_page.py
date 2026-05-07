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

driver.get('https://detail.zol.com.cn/gpswatch/apple/')
time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')

# 查找所有class包含pic的元素
pics = soup.find_all(class_='pic')
print(f"Found {len(pics)} elements with class 'pic'")

for i, pic in enumerate(pics[:3]):
    print(f"\n--- Item {i+1} ---")
    print(f"HTML: {str(pic)[:500]}")
    
    # 查找链接
    link = pic.find('a', href=True)
    if link:
        print(f"Link href: {link.get('href')}")
        img = link.find('img')
        if img:
            print(f"Img alt: {img.get('alt')}")
    
    # 查找父元素
    parent = pic.find_parent()
    if parent:
        print(f"Parent tag: {parent.name}, classes: {parent.get('class')}")
        # 查找价格
        price = parent.find(class_=lambda x: x and 'price' in str(x).lower())
        if price:
            print(f"Price: {price.get_text(strip=True)}")

driver.quit()