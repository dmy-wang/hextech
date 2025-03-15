import os

def create_data_folder(folder_name="data"):
    """创建数据文件夹并返回路径"""
    # 获取当前Python文件所在的目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建新文件夹的完整路径
    new_folder_path = os.path.join(current_dir, folder_name)

    # 检查文件夹是否已存在，如果不存在则创建
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)
        
    return new_folder_path

