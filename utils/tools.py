import json
import os
import random
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.edge.webdriver import WebDriver


class QR:
    def __init__(self):
        self._browser = None
        self.base_url = 'https://k8n.cn'
        self.login_qr_path = f'{self.base_url}/weixin/qrlogin/student'
        self.check_login_path = f'{self.base_url}/weixin/qrlogin/student?op=checklogin'
        self.class_info_path = 'classes/{}/'

    @staticmethod
    def _setup_webdriver() -> WebDriver:
        service = webdriver.EdgeService(executable_path='driver/edge.exe')
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        return webdriver.Edge(options=options, service=service)

    def start(self):
        self._browser = self._setup_webdriver()

    def exit(self):
        self._browser.quit()

    def load_qr(self):
        self._browser.get(self.login_qr_path)

    def get_url_img(self) -> str:
        soup = BeautifulSoup(self._browser.page_source, "html.parser")
        img_tag = soup.find('div', id='qrcode').find('img')
        url_img = img_tag['src']
        return url_img

    def get_log_status(self) -> dict:
        self._browser.get(self.check_login_path)
        content_response = json.loads(BeautifulSoup(self._browser.page_source, "html.parser").find('pre').text)
        return content_response

    def get_cookie_string(self, url: str) -> str:
        self._browser.get('https://k8n.cn' + url)
        cookies = self._browser.get_cookies()
        return ';'.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies if cookie['name']])

    @staticmethod
    def send_long_message(long_str: str, chunk_size: int=90):
        for i in range(0, len(long_str), chunk_size):
            send_message(long_str[i:i + chunk_size], "登录链接，需要拼接")

    def replace_cookies(self, cookie: str):
        class_dir = self.class_info_path.format(class_name)
        headers.update({'Cookie': cookie})
        with open(os.path.join(class_dir, 'cookie.txt'), 'w') as co_file:
            co_file.write(cookie)

    def save_class_info(self, cookie: str):
        class_dir = self.class_info_path.format(class_name)
        os.makedirs(class_dir, exist_ok=True)

        with open(os.path.join(class_dir, 'class_id.txt'), 'w') as id_file:
            id_file.write(class_id)

        with open(os.path.join(class_dir, 'cookie.txt'), 'w') as co_file:
            co_file.write(cookie)

        with open('classes/default.txt', 'w') as de_file:
            de_file.write(class_name)

    def get_classes(self):
        response_classes = self._browser.page_source
        soup = BeautifulSoup(response_classes, "html.parser")
        classes_elements = soup.find_all('div', {'class': 'card mb-3 course'})

        class_options = [{"name": elem.find('p').text.replace(elem.find('span').text, ''), "id": elem["course_id"]}
                         for elem in classes_elements]
        return class_options

# 检查是否已经签到
def is_checked(content: str, p_id: str) -> bool:
    soup = BeautifulSoup(content, "html.parser")
    div = soup.find("div", id='punchcard_' + p_id)
    if div.find('span', {'class': 'layui-badge layui-bg-green'}):
        return True
    else:
        return False


def send_message(content: str, title: str = ''):

    pushplus = configs['pushplus']
    if pushplus != '':
        purl = 'https://www.pushplus.plus/send?token=' + pushplus + '&title=' + title + '[自动签到]&content=' + content
        requests.get(purl)


def get_status() -> str:
    return status_check


def set_status(status: str):
    global status_check
    status_check = status

def data_write():
    global class_id
    path_dir_class = 'classes/' + class_name + '/'
    with open(path_dir_class + 'cookie.txt', 'r') as co_file:
        headers.update({'Cookie': co_file.read()})
    with open(path_dir_class + 'class_id.txt', 'r') as id_file:
        class_id = id_file.read()

# 检索主体
def job():

    global time_wait_random
    global matches
    global success
    global warning
    global wrong
    global fail

    time_wait = configs['签到等待时长']
    time_search = configs['检索间隔时长']
    time_shut = configs['签到关闭时间']

    while Run:
        url_punchs = 'https://k8n.cn/student/course/' + class_id + '/punchs'
        response_url_punchs = requests.get(url_punchs, headers=headers)
        if '抱歉，出错了' in response_url_punchs.text:
            set_status('错误')
            while get_status() != '继续' and Run:
                time.sleep(0.1)
            continue

        pattern = re.compile(r'punchcard_(\d+)')
        matches = pattern.findall(response_url_punchs.text)

        matches_checked = []
        for match in matches:
            if is_checked(response_url_punchs.text, match):
                matches_checked.append(match)
        matches = list(set(matches) - set(matches_checked))

        if matches:
            set_status('准备签到')

            time_wait_random = time_wait + random.randint(-5, 5)

            while get_status() != '继续' and Run:
                time.sleep(0.1)

            while time_wait_random > 0 and Run:

                set_status('签到中')
                time_wait_random = time_wait_random - 0.1
                time.sleep(0.1)

            success = 0
            warning = 0
            wrong = 0
            fail = 0
            for match in matches:
                if not Run:
                    break
                url_punch = 'https://k8n.cn/student/punchs/course/' + class_id + '/' + match
                response_url_punch = requests.get(url_punch, headers=headers)

                pattern = re.compile(r'var gpsranges = (.+)')
                try:
                    values_position = \
                        pattern.search(response_url_punch.text).group(1)[1:-2].replace('"', '').split('],[')[0][
                        1:].split(
                            ',')
                    if values_position[0] == 'l':
                        values_position = [41.677602, -101.752238, 100]  # 普通位置签到，定位到美国
                except AttributeError:
                    values_position = [0, 0, 0]  # 非位置签到，随便上传

                payload = {
                    'id': match,
                    'lat': values_position[0],
                    'lng': values_position[1],
                    'acc': values_position[2],
                    'res': '',  # 拍照签到
                    'gps_addr': ''  # 未知，抓取时该函数为空
                }

                response_url_punch_post = requests.post(url_punch, headers=headers, data=payload)

                if response_url_punch_post.status_code == 200:

                    soup_response = BeautifulSoup(response_url_punch_post.text, 'html.parser')
                    title = soup_response.find('div', id='title')

                    if title.text == '签到成功':
                        success += 1
                    elif title.text == '我已签到过啦':
                        warning += 1
                    else:
                        wrong += 1
                else:
                    fail += 1

            set_status('准备检索')
            while get_status() == '继续' and Run:
                time.sleep(0.1)

        else:
            st = time_search

            while 0 < st and Run:
                set_status('检索中')
                st -= 0.1
                time.sleep(0.1)

                if str(time.strftime('%H:%M', time.localtime())) == time_shut:
                    task()
                    return


# 判断是否在时间段
def is_between(time1: str, time2: str) -> bool:
    # 当前时间
    now = datetime.now()
    # 解析输入的时间字符串为datetime对象
    dt1 = parser.parse(time1).replace(year=now.year, month=now.month, day=now.day)
    dt2 = parser.parse(time2).replace(year=now.year, month=now.month, day=now.day)
    # 处理跨天的情况
    if dt1 > dt2:  # time1 在 time2 之后，说明跨过了午夜
        dt2 += timedelta(days=1)
    # 检查当前时间是否在time1和time2之间
    return dt1 <= now <= dt2


# 定义一个函数left_time，输入是一个字符串格式的时间t，返回值是一个字符串，表示从现在到t时间的剩余时间
def left_time(t: str) -> str:
    # 将输入的时间字符串转换为datetime对象
    target_time = datetime.strptime(t, '%H:%M:%S')  # 假设t是"HH:MM:SS"格式
    # 获取当前时间
    now = datetime.now().replace(microsecond=0)
    # 计算目标时间和当前时间的差值
    time_diff = target_time - now
    # 如果时间差为负，意味着目标时间已在过去，我们从明天的同一时间开始计算
    if time_diff.total_seconds() < 0:
        time_diff += timedelta(days=1)

    # 格式化剩余时间，确保小时、分钟和秒都是两位数
    return f"{time_diff.seconds // 3600:02d}:{(time_diff.seconds % 3600) // 60:02d}:{time_diff.seconds % 60:02d}"


# 调控定时任务
def task():

    time_start = configs['签到启动时间']
    time_shut = configs['签到关闭时间']

    if time_start != '':

        while not is_between(time_start, time_shut) and Run:

            set_status('暂停')
            time.sleep(0.1)

        job()
    else:
        job()
    set_status('关闭')


class_name = ''
class_id = ''
status_check = ''
time_wait_random = 0
success = 0
warning = 0
wrong = 0
fail = 0
headers = {}
configs = {}
matches = []
Run = False
Refreshing = False