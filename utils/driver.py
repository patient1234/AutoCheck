import re
import winreg
import requests
import zipfile
import os
import subprocess


def _get_edge_version() -> str:
    """ 从注册表中获取Edge浏览器的版本号 """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge\BLBeacon")
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
        return version
    except Exception:
        return ""


def _get_edgedriver_version() -> str:
    """ 获取Edge驱动器版本号 """
    # 指定msedgedriver的路径
    msedgedriver_path = os.path.abspath("driver/edge.exe")
    try:
        # 尝试获取版本信息
        ver = subprocess.run([msedgedriver_path, '--version'], capture_output=True, text=True)
        if ver.returncode == 0:
            # 形如：Microsoft Edge WebDriver 120.0.2210.91 (f469d579f138ffc82b54354de66117c1cb1bb923)
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ver.stdout.strip())
            if match:
                version = match.group(1)
                return version
            else:
                return ""
        else:
            print("获取版本时出错:", ver.stderr.strip())
            return ""
    except Exception as e:
        print("出现错误:", str(e))
        return ""


def _download_edgedriver(version: str):
    """ 下载对应版本的msedgedriver """
    # 检查操作系统位数
    architecture = _check_system_bit()
    if architecture == 64:
        # 下载win64位的压缩包
        url = f'https://msedgedriver.azureedge.net/{version}/edgedriver_win64.zip'
    else:
        # 下载win32位的压缩包
        url = f'https://msedgedriver.azureedge.net/{version}/edgedriver_win32.zip'
    print('驱动器压缩包下载地址：')
    print(url)
    response = requests.get(url)
    print('开始获取驱动器压缩包')
    # 保存并解压驱动
    zip_path = f"edgedriver_win{architecture}.zip"
    with open(zip_path, 'wb') as f:
        f.write(response.content)
    print('驱动器压缩包已下载')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extract("msedgedriver.exe", "driver")
    os.remove(zip_path)
    os.rename("driver/msedgedriver.exe", "driver/edge.exe")
    print('文件已解压，压缩包已删除')
    return os.path.abspath("driver/edge.exe")


def _check_system_bit() -> int:
    """ 检查操作系统位数 """
    if 'PROGRAMFILES(X86)' in os.environ:
        print("你的电脑为 64-bit 操作系统")
        return 64
    else:
        print("你的电脑为 32-bit 操作系统")
        return 32


def _version_comparison(edge_v: str, driver_v: str) -> bool:
    """ 比较浏览器和驱动的版本号 """
    if edge_v == driver_v:
        return True
    else:
        return False


def detect():
    edge_version = _get_edge_version()
    print("Edge浏览器版本号:", edge_version)

    driver_version = _get_edgedriver_version()
    print("msedgedriver版本号:", driver_version)

    if driver_version and edge_version:
        result = _version_comparison(edge_version, driver_version)
        if result:
            print('浏览器和驱动的版本一致')
        else:
            print(f'浏览器版本{edge_version} 和 驱动器版本{driver_version} 不一致')
            print('开始下载浏览器驱动，请稍候')
            driver_path = _download_edgedriver(edge_version)
            print(f'驱动已下载，保存在 {driver_path}')
        return True
    elif not edge_version:
        print('未获取到Edge浏览器的版本信息')
        return False
    else:
        print('未获取到驱动版本信息')
        # 4.下载驱动器
        print('开始下载浏览器驱动，请稍候')
        driver_path = _download_edgedriver(edge_version)
        print(f'驱动已下载，保存在 {driver_path}')
        return True