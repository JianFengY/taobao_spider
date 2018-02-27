"""
Created on 2018/2/27
@Author: Jeff Yang
"""
import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import pymongo

from taobao_spider.config import *

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)


def search():
    """
    查找商品
    """
    try:
        browser.get('https://www.taobao.com/')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))  # 传入元组
        )  # 查找输入框
        submit = wait.until(  # 搜索按钮
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#J_TSearchForm > div.search-button > button")))
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(  # 总页数
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.total")))
        get_products()  # 获取各个商品
        return total.text
    except TimeoutException:
        return search()


def next_page(page_number):
    """
    翻页
    """
    try:
        input = wait.until(  # 页数输入框
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(EC.element_to_be_clickable(  # 确定页数
            (By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit")))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element(  # 判断当前页数是否为输入的页数
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        get_products()  # 获取各个商品
    except TimeoutException:
        next_page(page_number)


def get_products():
    """
    获取当前页商品
    """
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'image': item.find('.pic .img').attr('src'),
            'price': item.find('.price').text(),
            'deal': item.find('.deal-cnt').text()[:-3],
            'title': item.find('.title').text(),
            'shop': item.find('.shop').text(),
            'location': item.find('.location').text(),
        }
        # print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print("保存到MongoDB成功：", result)
    except Exception:
        print("保存失败：", result)


def main():
    try:
        total = search()
        total = int(re.compile('(\d+)').search(total).group(1))
        print(total)
        for i in range(2, total + 1):
            next_page(i)
    except Exception:
        print("出错啦！")
    finally:
        browser.close()


if __name__ == '__main__':
    main()
