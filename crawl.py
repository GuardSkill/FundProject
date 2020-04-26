# coding:utf-8
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import random
from pymongo import MongoClient
import datetime
import argparse
from lxml import etree

client = MongoClient('localhost', 27017)
fund_db = client['fund_db']
fund_data = fund_db['fund_data']
fund_no_data = fund_db['fund_no_data']

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
}

def get_info_DB(url):
    print(url)
    opt = webdriver.ChromeOptions()
    opt.add_argument('--disable-gpu')
    opt.set_headless()
    driver = webdriver.Chrome(options=opt)
    driver.maximize_window()
    driver.get(url)
    driver.implicitly_wait(5)
    day = datetime.date.today()
    today = '%s' % day

    with open('jijin1.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    time.sleep(1)
    file = open('jijin1.html', 'r', encoding='utf-8')
    soup = BeautifulSoup(file, 'lxml')

    try:
        fund = soup.select('#bodydiv > div > div > div.basic-new > div.bs_jz > div.col-left > h4 > a')[0].get_text()
        scale = soup.select('#bodydiv > div > div.r_cont > div.basic-new > div.bs_gl > p > label > span')[2].get_text().strip().split()[0]
        table = soup.select('#cctable > div > div > table')
        trs = table[0].select('tbody > tr')
        for tr in trs:
            code = tr.select('td > a')[0].get_text()
            name = tr.select('td > a')[1].get_text()
            price = tr.select('td > span')[0].get_text()
            try:
                round(float(price), 2)
            except ValueError:
                price = 0
            num = tr.select('td.tor')[3].get_text()
            market = float(num.replace(',', '')) * float(price)

            data = {
                'crawl_date': today,
                'code': code,
                'fund': fund.split(' (')[0],
                'scale': scale,
                'name': name,
                'price': round(float(price), 2),
                'num': round(float(num.replace(',', '')), 2),
                'market_value': round(market, 2),
                'fund_url': url
            }
            fund_data.insert(data)
    except IndexError:
        info = {
            'url': url
        }
        fund_no_data.insert(info)


def get_info_print(url):
    print('scpape in url:'+url)
    opt = webdriver.ChromeOptions()
    # opt.add_argument('--disable-gpu')
    opt.set_headless()
    driver = webdriver.Chrome(options=opt)
    driver.maximize_window()
    driver.get(url)
    driver.implicitly_wait(5)
    # driver.find_element_by_id('su').click()            onclick="LoadMore(this,3,LoadStockPos)
    # a=driver.find_element_by_css_selector(".tfoot>font>a")
    try:
        button=driver.find_element_by_css_selector("a[onclick*=LoadMore")
        button.click()

    except:
        None
    day = datetime.date.today()
    today = '%s' % day
    # driver.implicitly_wait(5)
    time.sleep(0.5)
    #
    with open('jijin1.html', 'w', encoding='utf-8') as f:
        f.write(driver.page_source)


    # file = open('jijin1.html', 'r', encoding='utf-8')
    # res = requests.get(url)
    # html = res.text
    # with open('jijin1.html', 'w', encoding='utf-8') as f:
    #     f.write(html)
    html = open('jijin1.html', 'r', encoding='utf-8')
    soup = BeautifulSoup(html, 'lxml')

    try:
        fund = soup.select('#bodydiv > div > div > div.basic-new > div.bs_jz > div.col-left > h4 > a')[0].get_text()
        scale = soup.select('#bodydiv > div > div.r_cont > div.basic-new > div.bs_gl > p > label > span')[2].get_text().strip().split()[0]
        table = soup.select('#cctable > div > div > table')
        trs = table[0].select('tbody > tr')
        weighted_PER=0.0
        total_ratio=0.0
        for tr in trs:
            link=tr.select('td > a')[0]['href']
            link="http:"+link
            # subhtml = requests.get(link, headers=headers).text
            driver.get(link)
            driver.implicitly_wait(2)
            # driver.find_element_by_id('#gt6')

            subsoup = BeautifulSoup(driver.page_source, 'lxml')
            # subtable =subsoup.select('.yfw > tbody > tr > #gt6')
            PER=subsoup.select('#gt6')[0].get_text()
            code = tr.select('td > a')[0].get_text()
            name = tr.select('td > a')[1].get_text()
            price = tr.select('td > span')[0].get_text()
            ratio=tr.select('td')[6].get_text()
            try:
                round(float(price), 2)
            except ValueError:
                price = 0
            num = tr.select('td.tor')[3].get_text()
            market = float(num.replace(',', '')) * float(price)

            data = {
                'crawl_date': today,
                'code': code,
                'fund': fund.split(' (')[0],
                'scale': scale,
                'name': name,
                'price': round(float(price), 2),
                'num': round(float(num.replace(',', '')), 2),
                'market_value': round(market, 2),
                'fund_url': url,
                'PER(Active)':PER,
                'ratio':ratio
            }
            ratio=float(ratio.strip("%"))/100
            PER=float(PER)
            weighted_PER=weighted_PER+PER*ratio
            total_ratio = total_ratio+ratio
            # fund_data.insert(data)
            print(data)
        weighted_PER=weighted_PER/total_ratio
        fund_name=fund.split(' (')[0]
        print("基金名：%s"%fund_name,"代号：%s"%code,"持股占总资产的百分比： %.2f%%  "%(total_ratio*100),"加权动态市盈率 %.2f " % weighted_PER)
    except IndexError:
        info = {
            'url': url
        }
        # fund_no_data.insert(info)
    driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--code', type=str, default=None,
                        help='The code of fund')
    parser.add_argument('--output', type=str, default='./output', help='path to the output directory')
    args = parser.parse_args()
    if args.code is not None:  # scrap one fund
        url='http://fundf10.eastmoney.com/ccmx_%s.html' % args.code
        get_info_print(url)

    else :                 # scrap all funds
        with open('fund_url.txt', 'r') as f:
            i = 0
            for url in f.readlines():
                get_info_DB(url)
                time.sleep(random.randint(0, 2))
                i = i + 1
            print('run times:', i)
