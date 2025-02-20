import os
import shutil


def remove_empty_dirs(directory):
    """递归删除给定目录下的所有空目录"""
    if not os.path.isdir(directory):
        return
    # 遍历目录
    for entry in os.scandir(directory):
        if entry.is_dir():
            # 递归删除子目录中的空目录
            remove_empty_dirs(entry.path)
            # 如果子目录变为空，则删除它
            if not os.listdir(entry.path):
                os.rmdir(entry.path)


def remove_directories_with_cheats_and_clean(root_dir):
    # 获取指定目录下的一级子目录和文件列表
    items = os.listdir(root_dir)

    for item in items:
        full_path = os.path.join(root_dir, item)
        # 检查是否为目录且不是'.'或'..'这样的特殊目录
        if os.path.isdir(full_path) and item not in ['.', '..']:
            # 检查当前目录下是否有名为'cheats'的子目录
            if 'cheats' in os.listdir(full_path):
                try:
                    # 删除包含'cheats'的目录
                    shutil.rmtree(full_path)
                    print(f"Deleted: {full_path}")
                except Exception as e:
                    print(f"Error deleting {full_path}: {e}")

    # 在删除指定内容后，清理所有遗留的空目录
    remove_empty_dirs(root_dir)


# 使用时请替换下面的路径为你想要开始搜索的根目录
root_directory = '/path/to/start/search'
remove_directories_with_cheats_and_clean(root_directory)