import io
import json
import os
import threading
import time
from pathlib import Path

import requests
from PIL import Image
from pyzbar.pyzbar import decode
from qrcode.main import QRCode

import AutoCheck as ac


def select_class(ql: ac.QR):
    class_options = ql.get_classes()
    for idx, option in enumerate(class_options, start=1):
        print(f'[{idx}] {option["name"]}')

    selected_index = int(input('选择一个班级\n>')) - 1
    return class_options[selected_index]["name"], class_options[selected_index]["id"]


def login_success(ql: ac.QR, url: str, reset: bool):
    cookie = ql.get_cookie_string(url)
    ui_refresh()
    if reset:
        ql.replace_cookies(cookie)
    else:
        ac.class_name, ac.class_id = select_class(ql)
        ql.save_class_info(cookie)


def is_logged(ql: ac.QR, reset: bool) -> bool:
    for _ in range(20):
        log_check = ql.get_log_status()
        if log_check['status']:
            login_success(ql, log_check['url'], reset)
            return True
        print('\r等待登录中...', end='', flush=True)
        time.sleep(1)
    return False


def qr_login(reset: bool = False):
    global page
    page = -1
    url_img_last = ''

    ql = ac.QR()
    ql.start()
    while True:
        ql.load_qr()

        ui_refresh()
        print('微信扫描二维码登录')

        url_img = ql.get_url_img()
        if reset and url_img != url_img_last:
            url_img_last = url_img
            ql.send_long_message(url_img)
        print_qr(url_img)
        if is_logged(ql, reset):
            break
    page = 1
    ql.exit()


def extract_barcode_url(url_img: str):
    response = requests.get(url_img)
    barcode_url = ''
    barcodes = decode(Image.open(io.BytesIO(response.content)))
    for barcode in barcodes:
        barcode_url = barcode.data.decode("utf-8")
    return barcode_url


def print_qr(url_img: str):
    barcode_url = extract_barcode_url(url_img)
    qr = QRCode()
    qr.add_data(barcode_url)
    qr.print_ascii(invert=True)


# 记录输出
def page_out(p: int, content: str = ''):
    # 写入页面记录文件
    with open('classes/' + ac.class_name + '/pages/' + str(p), 'a+') as page_file:
        page_file.write(str(content) + '\n')
        if p == page:  # 在当前页面则直接刷新页面
            print(content)
            # ui_refresh()


# 输出并写日志
def print_log(content: str = '', color: str = ''):
    log_file = 'classes/' + ac.class_name + '/logs/' + str(time.strftime('%Y-%m-%d.txt', time.localtime()))
    with open(log_file, 'a+') as log:
        page_out(1, color + content + '\033[0m')
        log.write(str(time.strftime('[%H:%M:%S]', time.localtime())) + content + '\n')


# 输出写日志并且发送给用户
def print_log_send(content: str = '', color: str = ''):
    print_log(content, color)
    ac.send_message(content)


# 定义ui_refresh函数，用于刷新用户界面
def ui_refresh():
    global Refreshing
    if not Refreshing:
        # 将Refreshing状态设置为True，表示开始刷新
        Refreshing = True
        # 清屏操作，以便于更新显示内容
        os.system('cls')
        # 构建页面文件的完整路径
        page_path = 'classes/' + ac.class_name + '/pages/' + str(page)
        # 使用with语句打开指定页面文件，以读取模式(r)
        try:
            with open(page_path, 'r') as page_file:
                # 读取页面文件内容
                print(page_file.read())
        except FileNotFoundError:
            pass
        # 刷新完成后，将Refreshing状态重置为False
        Refreshing = False


def status_format() -> str:
    status = ac.get_status()
    if status == '检索中':
        status = '\033[36m' + status + '\033[0m'
    elif status == '签到中':
        status = '\033[32m' + status + '\033[0m'
    elif status == '暂停':
        status = '\033[33m' + status + '\033[0m'
    elif status == '错误' or status == '关闭':
        status = '\033[31m' + status + '\033[0m'
    return status


def status_listen():
    wc = ['-', '\\', '|', '/']
    i = 0
    while True:
        status = ac.get_status()
        if status == '准备检索':
            if ac.success != 0:
                print_log_send('签到成功 : ' + str(ac.success) + '个', '\033[32m')
            if ac.warning != 0:
                print_log_send('被标记未签 : ' + str(ac.warning) + '个', '\033[33m')
            if ac.wrong != 0:
                print_log_send('可能存在错误 : ' + str(ac.wrong) + '个', '\033[33m')
            if ac.fail != 0:
                print_log_send('请求失败 : ' + str(ac.fail) + '个', '\033[31m')
            ac.set_status('继续')
        elif status == '检索中':
            if page == 1 and not Refreshing:
                print('\r' + str(time.strftime('\033[32m[%H:%M:%S]\033[0m',
                                               time.localtime())) + ' \033[36m寻找签到中' + '\033[33m' + wc[
                          int(i) % 4] + '\033[0m ', end='', flush=True)
        elif status == '暂停':
            if page == 1 and not Refreshing:
                print(
                    '\r\033[32m[剩余' + ac.left_time(ac.configs['签到启动时间'] + ':00') + ']\033[0m',
                    end='', flush=True)
        elif status == '准备签到':
            print_log_send('找到签到 : ' + str(len(ac.matches)) + '个', '\033[36m')
            ac.set_status('继续')
        elif status == '签到中':
            if page == 1 and not Refreshing:
                print('\r\033[36m等待' + '%03d' % ac.time_wait_random + '秒...\033[0m', end='', flush=True)
        elif status == '错误':
            print_log_send('登录已过期，请重新登录')
            qr_login(True)
            print_log_send('重新登录成功')
            ui_refresh()
            ac.set_status('继续')
        i += 1
        time.sleep(0.2)


def config(reset: bool = False) -> dict:
    config_path = f'classes/{ac.class_name}/data.json'

    # 初始化默认配置
    default_data = {
        '检索间隔时长': 123,
        '签到等待时长': 123,
        '签到启动时间': '123',
        '签到关闭时间': '123',
        'pushplus': '123'
    }

    # 如果配置文件不存在，则创建并写入默认配置
    if not os.path.exists(config_path):
        with open(config_path, 'w') as file_configs:
            file_configs.write(json.dumps(default_data, ensure_ascii=False, indent=4))

    # 读取配置文件
    with open(config_path, 'r') as file_configs:
        json_data = json.load(file_configs)

    if reset:
        while True:
            i = 0
            print('\n选择要修改的项,q退出')
            for key, default_value in default_data.items():
                print('[' + str(i + 1) + ']' + key)
                i += 1
            select = input('>')
            if select == 'q':
                break
            select = int(select)
            i = 1
            for key, default_value in default_data.items():
                if json_data[key] == default_value:
                    value = '未设置'
                elif json_data[key] == '':
                    value = '空'
                else:
                    value = json_data[key]
                if select == i:
                    json_data[key] = input('输入修改后的值\n[' + value + ']>')
                    break
                i += 1
    else:
        # 用户输入更新配置
        for key, default_value in default_data.items():
            if json_data[key] == default_value:
                prompt = f'\n请输入{key.replace("_", " ").capitalize()}'
                if key.endswith('时间'):
                    prompt += ', 格式为00:00,或留空'
                elif key == 'pushplus':
                    prompt += '推送密钥,或留空'
                json_data[key] = input(prompt + '\n>')
                if key.endswith('时长'):
                    json_data[key] = int(json_data[key])

    # 写入用户更新后的配置
    with open(config_path, 'w') as file_configs:
        file_configs.write(json.dumps(json_data, ensure_ascii=False, indent=4))

    return json_data


def main():
    global page
    page = 0
    ac.set_status('关闭')
    ac.Run = True
    ac.headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; AKT-AK47 Build/USER-AK47; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160065 MMWEBSDK/20231202 MMWEBID/1136 MicroMessenger/8.0.47.2560(0x28002F35) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'X-Requested-With': 'com.tencent.mm',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh-SG;q=0.9,zh;q=0.8,en-SG;q=0.7,en-US;q=0.6,en;q=0.5'
    }

    ui_refresh()

    if not os.path.exists('classes'):
        qr_login()
        ui_refresh()

    if os.path.exists('classes/default.txt'):
        with open('classes/default.txt', 'r') as de_file:
            ac.class_name = de_file.read()
    else:
        i = 0
        _classes = os.scandir('classes')
        classes = []
        for _class in _classes:
            if _class.is_dir():
                print('[' + str(i + 1) + ']' + _class.name)
                classes.append(_class.name)
                i += 1
        i = input('选择并确认一个默认班级,新建输入n\n>')
        if i == 'n':
            qr_login()
            ui_refresh()
        else:
            ac.class_name = classes[int(i) - 1]
        with open('classes/default.txt', 'w+') as de_file:
            de_file.write(ac.class_name)

    ac.data_write()

    path_dir_class = 'classes/' + ac.class_name + '/'
    if not os.path.exists(path_dir_class + 'logs'):
        os.makedirs(path_dir_class + 'logs')

    if not os.path.exists(path_dir_class + 'pages'):
        os.makedirs(path_dir_class + 'pages')
        Path(path_dir_class + "pages/0").touch()
        Path(path_dir_class + "pages/1").touch()

    ac.configs = config()

    page_out(0, '\033[32m[已读取配置]\033[0m')
    page_out(1, '\033[32m[已读取配置]\033[0m')

    thread_check = threading.Thread(target=ac.task)
    thread_listen = threading.Thread(target=status_listen)

    thread_check.daemon = True
    thread_listen.daemon = True

    thread_check.start()
    thread_listen.start()

    print('等待服务开启')

    while ac.get_status() == '关闭':
        continue

    page_out(0, '检索已开启')

    menu = '\n[' + ac.class_name + '][' + status_format() + ']\n[1]进入检索界面\n[2]更新配置\n[3]清理页面缓存\n[4]配置文件\n[5]切换班级\n[6]关闭/开启\n>'

    try:
        while True:

            ui_refresh()

            select = input(menu)
            if select == '0' and page != 0:
                page = 0
                page_out(0, '已返回主界面')
                menu = '\n[' + ac.class_name + '][' + status_format() + ']\n[1]进入检索界面\n[2]更新配置\n[3]清理页面缓存\n[4]配置文件\n[5]切换班级\n[6]关闭/开启\n>'
            elif select == '1' and page != 1:
                page = 1
                page_out(0, '已进入检索界面')
                menu = '\n[' + ac.class_name + '][' + status_format() + ']\n[0]返回主界面\n[2]更新配置\n[6]关闭/开启\n>'
            elif select == '2':
                ac.Run = False
                print('等待检索关闭')
                thread_check.join()
                ac.configs = config()
                thread_check = threading.Thread(target=ac.task)
                thread_check.daemon = True
                ac.Run = True
                thread_check.start()
                print('等待检索开启')
                while ac.get_status() == '关闭':
                    continue
                page_out(0, '已更新配置')
            elif select == '3' and page == 0:
                page_select = str(eval(input('\n清理哪个页面?\n[1]主界面\n[2]检索界面\n>')) - 1)
                if page_select != '' and os.path.exists('classes/' + ac.class_name + '/pages/' + page_select):
                    os.remove('classes/' + ac.class_name + '/pages/' + page_select)
                    page_out(int(page_select), '已清理该界面')
            elif select == '4' and page == 0:
                ac.configs = config(True)
                page_out(0, '已配置完成，请更新')
            elif select == '5' and page == 0:
                os.remove('classes/default.txt')
                ac.Run = False
                thread_check.join()
                main()
            elif select == '6':
                ac.Run = not ac.Run
                if ac.Run:
                    on_off = '开启'
                    thread_check = threading.Thread(target=ac.task)
                    thread_check.daemon = True
                    thread_check.start()
                    print('等待检索开启')
                    while ac.get_status() == '关闭':
                        continue
                else:
                    on_off = '关闭'
                    print('等待检索关闭')
                    thread_check.join()
                page_out(0, '检索已' + on_off)

            if page == 0:
                menu = '\n[' + ac.class_name + '][' + status_format() + ']\n[1]进入检索界面\n[2]更新配置\n[3]清理页面缓存\n[4]配置文件\n[5]切换班级\n[6]关闭/开启\n>'
            elif page == 1:
                menu = '\n[' + ac.class_name + '][' + status_format() + ']\n[0]返回主界面\n[2]更新配置\n[6]关闭/开启\n>'
    except KeyboardInterrupt:
        page_out(0, '检索已关闭')
        print('\n系统已退出')


Refreshing = False
page = 0
main()
