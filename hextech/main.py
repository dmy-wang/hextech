import os
import sys
from lolhelper import *
from mainwindow import HeroRecommender
from PyQt5.QtWidgets import QApplication

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

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


