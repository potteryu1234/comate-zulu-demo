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
print('Page title:', soup.title.string if soup.title else 'No title')
print('\n--- Looking for product items ---')

# Try different selectors
selectors = ['.list-item', '.product-item', '.item', '.goods-item', '.pic', '.pic-box', 'li']
for selector in selectors:
    items = soup.select(selector)
    if items:
        print(f'{selector}: found {len(items)} items')
        if len(items) > 0:
            print(f'  First item: {str(items[0])[:500]}')
            print()

# Look for links with index in href
print('\n--- Links with index ---')
for a in soup.find_all('a', href=True):
    href = a.get('href', '')
    if 'index' in href and '.shtml' in href:
        print(f"Link: {href}")
        print(f"Text: {a.get_text(strip=True)[:100]}")
        print()
        break

driver.quit()