import os
import sys
import shutil
from lolhelper import *
from mainwindow import HeroRecommender
from PyQt5.QtWidgets import QApplication

def cleanup_data_folder():
    """清空data文件夹中的所有文件"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"清理文件时出错: {e}")
                
def main():
    # 初始化Hextech窗口
    app = QApplication(sys.argv)
    window = HeroRecommender()
    window.show()
    if checkProcessAlive("LeagueClient"):
        try:
            window.lol_helper_init()
        except RuntimeError as e:
            window.set_status_message(str(e), 'error', 5000)
        except ValueError as e:
            window.set_status_message(str(e), 'error', 5000)
        except Exception as e:
            window.set_status_message("程序初始化失败，请检查日志获取详细信息", 'error', 5000)
    else:
        #print("未检测到游戏进程，请先运行游戏")
        window.set_status_message("未检测到游戏进程，请先运行游戏", 'error', 5000)
    
    # 注册程序退出时的清理函数
    app.aboutToQuit.connect(cleanup_data_folder)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


