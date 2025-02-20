import os
import shutil


def remove_directories_with_cheats_in_one_level(root_dir):
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


# 使用时请替换下面的路径为你想要开始搜索的根目录
root_directory = '/path/to/start/search'
remove_directories_with_cheats_in_one_level(root_directory)