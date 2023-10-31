# -*- coding:utf-8 -*-
import json
import requests
import datetime
import re
import os
import sys
import time
import subprocess
import zipfile
import optparse
import json

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import m3u8down


base_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
cache_dir = f'{base_dir}{os.sep}cache'
max_retry = 10


'''
    run cmd
'''
def shell_run_cmd_block(cmd, succ_kw):
    p = subprocess.Popen(cmd,
                     shell=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,
                     )
    
    strs = str(p.communicate()[0]).split()
    for s in strs:
        if succ_kw in s:
            return True, strs
    return False, strs


'''
    获取edge最新版本号，通过遍历安装目录文件夹实现
'''
def get_edge_latest_version(path):
    lastest = ''
    for dirpath, dirnames, filenames in os.walk(path):
        for dirname in dirnames:
            if '.' in dirname:
                lastest = dirname
    return lastest


'''
    获取webdriver版本号
'''
def get_web_driver_version(path):
    p = subprocess.Popen(path,
                     shell=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT,
                     )
    
    strs = str(p.communicate()[0]).split()
    for s in strs:
        if '.' in s:
            return s
    return


'''
    下载指定的webdriver版本, 并解压
'''
def download_lastest_web_driver(ver):
    url = r'https://msedgedriver.azureedge.net/%s/edgedriver_win64.zip' % ver
    path = 'edgedriver_win64.zip'
    try:
        r = requests.get(url)
        with open(path, 'wb') as code:
            code.write(r.content)

        zip_file = zipfile.ZipFile(path)
        zip_list = zip_file.namelist() # 得到压缩包里所有文件

        for f in zip_list:
            zip_file.extract(f, cache_dir) # 循环解压文件到指定目录

        zip_file.close()
        print('download & extract done')
    except Exception as e:
        print(e)
        

'''
    拷贝更行webdriver的exe文件
'''
def copy_file(fromFile, toFile):
    try:
        with open(fromFile, 'rb') as r:
            content = r.read()
            with open(toFile, 'wb') as w:
                w.write(content)
                w.close()
            r.close()
        print('copy file done')
    except Exception as e:
        print(e)


'''
    总体更新逻辑，先下载后覆盖更新exe
'''
def update_ms_web_driver(ver):
    download_lastest_web_driver(ver)
    copy_file(f'{cache_dir}{os.sep}msedgedriver.exe', f'{sys.prefix}{os.sep}MicrosoftWebDriver.exe')


'''
    kill 掉所有依赖的进程
'''
def processCleanup():
    shell_run_cmd_block('taskkill /F /IM /T msedge.exe', '成功')
    shell_run_cmd_block('taskkill /F /IM /T MicrosoftWebDriver.exe', '成功')


'''
    检查是否需要更新，如果更新失败会重复尝试更新n次
'''
def check_web_driver_update():
    processCleanup()

    edge_lastest_ver = get_edge_latest_version(r'C:\Program Files (x86)\Microsoft\Edge\Application')
    print('edge lastest version:', edge_lastest_ver)

    web_driver_ver = get_web_driver_version(r'MicrosoftWebDriver.exe --version')
    print('web driver current version:', web_driver_ver)

    n = 0
    while web_driver_ver != edge_lastest_ver:
        update_ms_web_driver(edge_lastest_ver)
        web_driver_ver = get_web_driver_version(r'MicrosoftWebDriver.exe --version')
        n = n+1
        if n > max_retry:
            print('max retry')
            break


def cookie_to_json(cookie):
    obj = {}
    arr = cookie.split(';')
    for i in arr:
        [k, v] = i.strip().split('=', 1)
        if "expiry" not in k:
            obj[k] = v
    return obj


def create_browser(path):
    # 配置 options
    opt = Options()
    # # 关闭使用 ChromeDriver 打开浏览器时上部提示语 "Chrome正在受到自动软件的控制"
    opt.add_argument("--disable-infobars")
    opt.add_argument("--disable-web-security")
    # 无头浏览器
    #opt.add_argument('--no-sandbox')
    #opt.add_argument('--disable-dev-shm-usage')
    #opt.add_argument('--headless')
    #opt.add_argument('blink-settings=imagesEnabled=false')
    web = webdriver.Edge(options=opt)

    # 配置浏览器
    web.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior',
        'params': {'behavior': 'allow', 'downloadPath': path}}
    web.execute("send_command", params=params)
    return web


def js_get(url, headers={}):
    js = f'let xhr = new XMLHttpRequest(); xhr.open("GET", "{url}"); xhr.send();'
    return js


def js_post(url, data, headers={}):
    js = f'let xhr = new XMLHttpRequest(); xhr.open("GET", "{url}"); xhr.send({json.dumps(data)});'
    return js

'''
    parse_page
    1、打开页面
    2、获取播放按钮并点击
    3、解析得到m3u8地址
    4、下载m3u8并解析
    5、下载m3u8每个分片
    6、将分片合并成mp4
'''
def ph_parse(url, path, size):
    web = create_browser(path)
    web.get(url)
    while 1:
        wait = WebDriverWait(web, 120)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'mgp_readyState')) or 
                   EC.presence_of_element_located((By.CLASS_NAME, 'mgp_playingState')))

        quality = web.execute_script("return document.querySelector('.mgp_quality > li').textContent;")
        print('quality', quality)

        titles = web.execute_script("return document.getElementsByName('twitter:image')[0].content.split('/');")
        print('params', titles)

        play_btn = web.find_element(By.CLASS_NAME, 'mgp_play')
        if play_btn:
            ActionChains(web).move_to_element(play_btn).click().perform()
        wait = WebDriverWait(web, 120)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'mgp_playingState')))

        time.sleep(6)
        pause_btn = web.find_element(By.CLASS_NAME, 'mgp_pause')
        if pause_btn:
            ActionChains(web).move_to_element(pause_btn).click().perform()

        urls = []
        for req in web.execute_script("return window.performance.getEntries();"):
            if '.m3u8' in req['name']:
                urls.append(req['name'])
        if len(urls) == 0:
            print('master.m3u8 url not found')
            web.refresh()
            continue
        print(urls)

        #text = web.page_source
        #soup = BeautifulSoup(text, 'html.parser')
        m3u8_uri = urls[0]
        print('master.m3u9', m3u8_uri)
        #web.get(m3u8_uri)
        m3u8down.down(m3u8_uri, f'{path}{os.sep}{titles[4]}_{titles[5]}_{titles[6]}')
        print(f'{m3u8_uri}, download success')
        web.quit()
        break


def xv_parse(url, path, size):
    web = create_browser(path)
    web.get(url)
    while 1:
        web.quit()
        break


def start(url='', path=base_dir, size=64*1024*1024):
    parser = optparse.OptionParser()
    parser.add_option("-u", "--url", dest="url", default=url, help="page url to be parse")
    parser.add_option("-p", "--path", dest="path", default=path, help="path to save file")
    parser.add_option("-s", "--size", dest="size", default=size, help="download chunked size")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="print running verbose log")
    (options, args) = parser.parse_args()
    
    check_web_driver_update()

    if os.path.exists(options.path) and not os.path.isfile(options.path):
        path = options.path
    if os.path.exists(path):
        os.makedirs(path, 511, True)
    
    if '.pornhub.' in options.url:
        ph_parse(options.url, path, options.size)
    if '.xvideos.' in options.url:
        xv_parse(options.url, path, options.size)


if __name__ == "__main__":
    start()