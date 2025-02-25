import ctypes
import io
import json
import os
import sys
import threading
import time
import tkinter as tk
from functools import partial

import _tkinter
import pystray
import requests
from PIL import Image, ImageTk
from utils import tools as ac

def center_window(width: int, height: int):
    """使窗口居中显示"""
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (width / 4))
    y_cordinate = int((screen_height / 2) - (height / 4))
    root.geometry(f"{width}x{height}+{x_cordinate}+{y_cordinate}")


def on_off(frame:tk.Frame=None):
    global thread_check
    ac.Run = not ac.Run
    if frame:
        button = frame.winfo_children()[2]
        if ac.Run:
            button.config(text='停止')
            main()
        else:
            button.config(text='开启')
            if thread_check.is_alive():
                thread_check.join()

def on_start(_):
    thread_listen = threading.Thread(target=status_listen)
    thread_listen.daemon = True
    thread_listen.start()
    main()

def init_tk():

    global frame_main
    global frame_wait
    global frame_qr
    global frame_config
    global frame_select_class
    global img_qr
    global text_log
    global text_status
    global text_class
    # 初始化Tkinter窗口
    root.title("班级魔方自动签到")
    root.iconphoto(True, tk.PhotoImage(file="assets/icon.png"))
    root.protocol("WM_DELETE_WINDOW", sys.exit)

    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    root.tk.call('tk', 'scaling', scale_factor / 75)

    root.geometry(f"{window_width}x{window_height}")
    root.minsize(width=900, height=450)
    # root.maxsize(width=window_width, height=window_height)
    root.config(bg=main_color)
    # 确保窗口大小是适中的，并居中显示
    center_window(window_width, window_height)

    frame_wait = tk.Frame(root, bg=main_color)
    frame_main = tk.Frame(root, bg=main_color)
    frame_qr = tk.Frame(root, bg=main_color)
    frame_config = tk.Frame(root, padx=20, pady=20, bg=main_color)
    frame_select_class = tk.Frame(root, padx=20, pady=20, bg=main_color)

    # 扫码界面
    frame0 = tk.Frame(frame_qr, bg=main_color)
    text_qr = tk.Label(frame0, text='微信扫描二维码登录', font=(font_style_default, 24), bg=main_color)
    img_qr = tk.Label(frame0, image='', bg=main_color)

    # 主界面
    frame1 = tk.Frame(frame_main, padx=1, pady=1, bg=second_color)
    text_log = tk.Text(frame1, width=25, font=(font_style_default, 10), bg=third_color)
    scrollbar = tk.Scrollbar(frame1, width=0, command=text_log.yview)
    frame2 = tk.Frame(frame_main, bg=main_color)
    frame_class = tk.Frame(frame2, padx=1, pady=1, bg=second_color)
    text_class = tk.Label(frame_class, font=(font_style_default, 10), bg=main_color)
    frame_status = tk.Frame(frame2, padx=1, pady=1, bg=second_color)
    text_status = tk.Label(frame_status, height=3, font=(font_style_default, 20), bg=main_color)
    frame_menu = tk.Frame(frame2, height=10, padx=10, pady=10, bg=main_color)
    button1 = tk.Button(frame_menu, text='切换班级', font=(font_style_default, 15), bg=third_color, command=partial(class_select, True))
    button2 = tk.Button(frame_menu, text='更新配置', font=(font_style_default, 15), bg=third_color, command=config)
    button3 = tk.Button(frame_menu, text='停止', font=(font_style_default, 15), bg=third_color, command=partial(on_off, frame_menu))
    button4 = tk.Button(frame_menu, text='隐藏到托盘', font=(font_style_default, 15), bg=third_color, command=tray_start)

    frame_wait.pack(fill=tk.BOTH, expand=True)
    frame_main.pack(fill=tk.BOTH, expand=True)
    frame_qr.pack(fill=tk.BOTH, expand=True)
    frame_config.pack(fill=tk.BOTH, expand=True)
    frame_select_class.pack(fill=tk.BOTH, expand=True)

    frame_wait.bind('<Visibility>', on_start)

    frame0.pack(expand=True)
    text_qr.pack(fill='x')
    img_qr.pack(fill='x')
    frame1.pack(side=tk.LEFT, fill='y')
    text_log.pack(side=tk.LEFT, fill='y')
    scrollbar.pack(side=tk.RIGHT, fill='y')
    frame2.pack(fill=tk.BOTH)
    frame_class.pack(fill='x', expand=True)
    text_class.pack(side=tk.LEFT, fill='x', expand=True)
    frame_status.pack(fill='x', expand=True)
    text_status.pack(side=tk.LEFT, fill='x', expand=True)
    frame_menu.pack(fill=tk.BOTH, expand=True)
    button1.pack(fill='x', expand=True)
    button2.pack(fill='x', expand=True)
    button3.pack(fill='x', expand=True)
    button4.pack(fill='x', expand=True)

    text_log['yscrollcommand'] = scrollbar.set
    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        try:
            ql.exit()
        except AttributeError:
            pass


def load_qr(url_img):
    global img_qr
    img = Image.open(io.BytesIO(requests.get(url_img).content))
    src_img_qr = ImageTk.PhotoImage(img)
    try:
        img_qr.config(image=src_img_qr)
        img_qr.image = src_img_qr
    except RuntimeError:
        pass


def load_class_online(cookie, option):
    ac.class_name = option['name']
    ac.class_id = option['id']
    ql.save_class_info(cookie)
    main()


def select_class(cookie):
    class_options = ql.get_classes()
    load_frame(frame_select_class)
    for frame in frame_select_class.winfo_children():
        frame.pack_forget()
    frame_big = tk.Frame(frame_select_class, bg=main_color)
    frame_big.pack(fill=tk.BOTH)
    for option in class_options:
        button = tk.Button(frame_big, width=30, font=(font_style_default, 15), text=option["name"],
                           command=partial(load_class_online, cookie, option), bg=third_color)
        button.pack()


def login_success(url: str, reset: bool):
    cookie = ql.get_cookie_string(url)
    if reset:
        ql.replace_cookies(cookie)
        main()
    else:
        select_class(cookie)


def is_logged(reset: bool) -> bool:
    for _ in range(20):
        log_check = ql.get_log_status()
        if log_check['status']:
            login_success(log_check['url'], reset)
            return True
        time.sleep(1)
    return False


def qr_login(reset: bool = False):
    global ql
    load_frame(frame_qr)

    url_img_last = ''
    ql = ac.QR()
    ql.start()
    while True:
        ql.load_qr()
        url_img = ql.get_url_img()
        if reset and url_img != url_img_last:
            url_img_last = url_img
            ql.send_long_message(url_img)
        load_qr(url_img)
        if is_logged(reset):
            break
    ql.exit()


def load_frame(frame: tk.Frame):
    for _frame in root.winfo_children():
        if frame == _frame:
            _frame.pack(fill=tk.BOTH, expand=True)
        else:
            _frame.pack_forget()


def load_class_local(name: str):
    ac.Run = False
    thread_check.join()
    ac.class_name = name
    with open('classes/default.txt', 'w+') as de_file:
        de_file.write(ac.class_name)
    main()


def config():

    def update_config():
        on_off()
        i = 0
        for k, v in json_data.items():
            config_get = wid_configs[i].get()
            if '时长' in k:
                config_get = int(config_get)
            json_data[k] = config_get
            i += 1
        # 写入用户更新后的配置
        with open(config_path, 'w') as file:
            file.write(json.dumps(json_data, ensure_ascii=False, indent=4))
        frame_big.pack_forget()
        on_off()
        main()

    config_path = f'classes/{ac.class_name}/data.json'

    # 读取配置文件
    with open(config_path, 'r') as file_configs:
        json_data = json.load(file_configs)

    load_frame(frame_config)
    wid_configs = []
    for frame in frame_config.winfo_children():
        frame.pack_forget()
    frame_big = tk.Frame(frame_config, bg=main_color)
    frame_big.pack()
    for key, value in json_data.items():
        frame = tk.Frame(frame_big, bg=main_color)
        text = tk.Label(frame, text=key, width=15, font=(font_style_default, 15), bg=main_color)
        entry = tk.Entry(frame, width=35, font=(font_style_default, 15), bg=main_color)

        entry.insert(tk.INSERT, value)

        frame.pack()
        text.pack(side=tk.LEFT)
        entry.pack(padx=10, side=tk.LEFT)

        wid_configs.append(entry)
    margin = tk.Label(frame_big, height=3, bg=main_color)
    margin.pack()
    button = tk.Button(frame_big, text='保存', font=(font_style_default, 15), width=40,
                       command=update_config, fg=main_color, bg=second_color)
    button2 = tk.Button(frame_big, text='返回', font=(font_style_default, 15), width=40,
                       command=partial(load_frame, frame_main), fg=main_color, bg=second_color)
    button.pack()
    button2.pack()


def log(content: str):
    log_file = 'classes/' + ac.class_name + '/logs/' + str(time.strftime('%Y-%m-%d.txt', time.localtime()))
    with open(log_file, 'a') as file_log:
        file_log.write(str(time.strftime('[%H:%M:%S]', time.localtime())) + content + '\n')
    with open(log_file, 'r') as file_log:
        text_log.config(state=tk.NORMAL)
        text_log.delete(1.0, tk.END)
        text_log.insert(tk.INSERT, file_log.read())
        text_log.config(state=tk.DISABLED)
        text_log.see(tk.END)


def log_send(content: str):
    log(content)
    ac.send_message(content)

def tray_start():
    global tray_icon

    root.withdraw()
    tray_icon = pystray.Icon("app_name", Image.open("assets/icon.png"), "班级魔方自动签到",
                         (pystray.MenuItem("显示", tray_stop),))
    tray_icon.run()

def tray_stop():
    tray_icon.stop()
    root.deiconify()

def status_listen():
    try:
        while True:
            status = ac.get_status()
            if status == '准备检索':
                if ac.success != 0:
                    log_send('签到成功 : ' + str(ac.success) + '个')
                if ac.warning != 0:
                    log_send('被标记未签 : ' + str(ac.warning) + '个')
                if ac.wrong != 0:
                    log_send('可能存在错误 : ' + str(ac.wrong) + '个')
                if ac.fail != 0:
                    log_send('请求失败 : ' + str(ac.fail) + '个')
                ac.set_status('继续')
            elif status == '检索中':
                text_status.config(text=str(time.strftime('[%H:%M:%S]', time.localtime())) + ' 寻找签到中...')
            elif status == '暂停':
                text_status.config(text='[剩余' + ac.left_time(ac.configs['签到启动时间'] + ':00') + ']')
            elif status == '准备签到':
                log_send('找到签到 : ' + str(len(ac.matches)) + '个')
                ac.set_status('继续')
            elif status == '签到中':
                text_status.config(text='等待' + '%d' % ac.time_wait_random + '秒...')
            elif status == '错误':
                log_send('登录已过期')
                qr_login(True)
                log_send('重新登录成功')
                ac.set_status('继续')
            elif status == '关闭':
                    text_status.config(text='检索已关闭')
            time.sleep(0.2)
    except RuntimeError:
        pass
    except _tkinter.TclError:
        pass


def login_thread():
    thread_qr_login = threading.Thread(target=qr_login)
    thread_qr_login.daemon = True
    thread_qr_login.start()

def class_select(change: bool=False):
    load_frame(frame_select_class)
    for frame in frame_select_class.winfo_children():
        frame.pack_forget()
    frame_big = tk.Frame(frame_select_class, bg=main_color)
    frame_big.pack(fill=tk.BOTH)
    _classes = os.scandir('classes')
    for _class in _classes:
        if _class.is_dir():
            selection = tk.Button(frame_big, text=_class.name, font=(font_style_default, 15), width=40,
                                  command=partial(load_class_local, _class.name), bg=third_color)
            selection.pack()

    margin = tk.Label(frame_big, height=3, bg=main_color)
    margin.pack()
    button_new = tk.Button(frame_big, text='创建新班级', font=(font_style_default, 15), width=40, command=login_thread,
                           fg=main_color, bg=second_color)
    button_new.pack()
    if change:
        button_new = tk.Button(frame_big, text='返回', font=(font_style_default, 15), width=40, command=partial(load_frame, frame_main),
                               fg=main_color, bg=second_color)
        button_new.pack()

def main():
    global thread_check
    ac.set_status('关闭')
    ac.Run = True
    ac.headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; AKT-AK47 Build/USER-AK47; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/116.0.0.0 Mobile Safari/537.36 XWEB/1160065 MMWEBSDK/20231202 MMWEBID/1136 MicroMessenger/8.0.47.2560(0x28002F35) WeChat/arm64 Weixin NetType/4G Language/zh_CN ABI/arm64',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/tpg,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'X-Requested-With': 'com.tencent.mm',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh-SG;q=0.9,zh;q=0.8,en-SG;q=0.7,en-US;q=0.6,en;q=0.5'
    }

    if not os.path.exists('classes'):
        login_thread()
        return
    if os.path.exists('classes/default.txt'):
        with open('classes/default.txt', 'r') as de_file:
            ac.class_name = de_file.read()
    else:
        class_select()
        return
    text_class.config(text=ac.class_name)

    ac.data_write()

    path_dir_class = 'classes/' + ac.class_name + '/'
    if not os.path.exists(path_dir_class + 'logs'):
        os.makedirs(path_dir_class + 'logs')

    config_path = f'classes/{ac.class_name}/data.json'
    # 如果配置文件不存在，则创建并写入默认配置
    if not os.path.exists(config_path):
        # 初始化默认配置
        default_data = {
            '检索间隔时长': 60,
            '签到等待时长': 150,
            '签到启动时间': '',
            '签到关闭时间': '',
            'pushplus': ''
        }
        with open(config_path, 'w') as file_configs:
            file_configs.write(json.dumps(default_data, ensure_ascii=False, indent=4))
        config()
        return
    else:
        with open(config_path, 'r') as file_configs:
            ac.configs = json.load(file_configs)

    thread_check = threading.Thread(target=ac.task)

    thread_check.daemon = True

    thread_check.start()

    while ac.get_status() == '关闭':
        continue

    load_frame(frame_main)
    log('检索启动')


root = tk.Tk()

# 创建系统托盘图标
tray_icon = pystray.Icon("app_name", Image.open("assets/icon.png"), "班级魔方自动签到",
                         (pystray.MenuItem("显示", tray_stop),))

frame_wait = tk.Frame()
frame_qr = tk.Frame()
frame_select_class = tk.Frame()
frame_config = tk.Frame()
frame_main = tk.Frame()

img_qr = tk.Label()
text_status = tk.Label()
text_log = tk.Text()
text_class = tk.Label()

font_styles = ['0微软雅黑', '1包图小白体', '2楷体', '3今昔豪龙',
               '4禹卫书法行书简体', '5Yozai Font', '6何某手寫',
               '7贤二体', '8经典繁毛楷']
font_style_default = font_styles[2][1:]

main_color = 'white'
second_color = 'gray'
third_color = 'lightgray'

# 设置窗口大小
window_width = 1200
window_height = 750

thread_check = threading.Thread()
ql = ac.QR()

init_tk()
