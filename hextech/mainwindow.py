import os
import sys
import json
import logging
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont,QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize,QObject, pyqtSlot
from analysis import TeamAnalysis
from lolhelper import *
from llm_adapter import LLMHandler
from utils import *
class HeroCard(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumWidth(250)

        layout = QVBoxLayout()
        
        # 英雄名称
        self.hero_label = QLabel("英雄名称")
        self.hero_label.setAlignment(Qt.AlignCenter)

        # 推荐理由
        self.reason_label = QLabel("推荐理由：")
        self.reason_label.setWordWrap(True)

        # 游戏思路
        self.strategy_label = QLabel("游戏思路：")
        self.strategy_label.setWordWrap(True)

        self.setMinimumWidth(300)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QGroupBox {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                margin-top: 10px;
                padding: 20px;
                font-family: 'Roboto', sans-serif;
                font-size: 20px;
                font-weight: 500;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                color: #0078D4;
                font-weight: 600;
            }
        """)

        self.hero_label.setStyleSheet("""
            QLabel {
                font-family: 'Roboto', 'Microsoft YaHei UI', sans-serif;
                font-size: 26px;
                font-weight: 600;
                color: #212121;
                margin: 15px 0;
                padding: 12px;
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E0E0E0;
                border-bottom: 3px solid #0078D4;
                letter-spacing: 1px;
                text-align: center;
                background: linear-gradient(to bottom, #FFFFFF, #F5F5F5);
            }
        """)
        
        self.reason_label.setStyleSheet("""
            QLabel {
                font-family: 'Roboto', 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                color: #424242;
                padding: 15px;
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
                line-height: 1.8;
                margin-bottom: 15px;
                border-left: 4px solid #0078D4;
            }
        """)
        
        self.strategy_label.setStyleSheet("""
            QLabel {
                font-family: 'Roboto', 'Microsoft YaHei UI', sans-serif;
                font-size: 16px;
                color: #424242;
                padding: 15px;
                background-color: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
                line-height: 1.8;
                border-left: 4px solid #4CAF50;
            }
        """)
        layout.addWidget(self.hero_label)
        layout.addWidget(self.reason_label)
        layout.addWidget(self.strategy_label)
        self.setLayout(layout)


class BPInfoPanel(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setup_ui()
        
    def setup_ui(self):
        # 使用垂直布局作为主布局
        layout = QVBoxLayout()
        layout.setSpacing(1)  # 减小垂直间距
        # 创建水平布局容器用于英雄列表
        hero_container = QWidget()
        hero_layout = QHBoxLayout(hero_container)
        hero_layout.setSpacing(3)  # 减小英雄标签之间的间距
        hero_layout.setContentsMargins(0, 0, 0, 0)  # 移除容器边距
        
        # 创建5个标签用于显示英雄
        self.hero_labels = []
        for i in range(5):
            label = QLabel()
            label.setFixedSize(100, 40)  # 增加标签大小
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    font-family: 'Roboto', 'Microsoft YaHei UI', sans-serif;
                    font-size: 18px;
                    font-weight: 500;
                    color: #323130;
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                    padding: 6px;
                }
                QLabel:hover {
                    background-color: #F5F5F5;
                    border: 1px solid #CCCCCC;
                }
            """)
            
            self.hero_labels.append(label)
            hero_layout.addWidget(label)

        self.setStyleSheet("""
            QGroupBox {
                font-family: 'Roboto', 'Microsoft YaHei UI';
                font-size: 20px;
                font-weight: 600;
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                margin-top: 2px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px;
                color: #0078D4;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
        """)
        
        layout.addWidget(hero_container)
        self.setLayout(layout)
        
    def update_heroes(self, heroes):
        # 清空所有标签
        for label in self.hero_labels:
            label.clear()
            
        # 更新英雄名称
        for i, hero in enumerate(heroes[:5]):  # 限制最多显示5个英雄
            self.hero_labels[i].setText(hero)


class HeroRecommender(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_info_json = None
        self.position = ""
        self.analysis_tool = TeamAnalysis()
        self.init_ui()
        self.mock_data()
        self.setup_status_bar_styles()
        self.lol_connector = None
        self.llm_handler = None

    def lol_helper_init(self):
        self.lol_connector = LolHelper_init()

    def init_ui(self):
        self.setWindowTitle("HexTech智能BP系统 v3.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主窗口布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 控制面板
        control_layout = QHBoxLayout()
        self.fetch_btn = QPushButton("获取BP数据")
        self.current_pos_label = QLabel("我的位置：")
        self.generate_btn = QPushButton("生成智能推荐")
        self.generate_btn.setLayoutDirection(Qt.RightToLeft)
        icon_path = "./hextech/resource/icons/gene-green.png"
        if os.path.exists(icon_path):
            self.generate_btn.setIcon(QIcon(icon_path))
        else:
            # 如果图标不存在，记录错误信息
            #print(f"警告：图标文件不存在 - {icon_path}")
            self.statusBar().showMessage("警告：图标文件不存在 - " + icon_path, 5000)
            pass
        self.generate_btn.setIcon(QIcon(icon_path))
        self.generate_btn.setIconSize(QSize(36, 36))
        self.current_pos_label.setStyleSheet("""
            QLabel {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 16px;
                margin-left: 40px;  /* 调整数值来控制空白大小 */
                max-height: 36px;   /* 设置最大高度 */
                font-size: 16px;
                font-weight: 600;
            }
        """)
        # 添加选项
        # 创建下拉选择框
        self.current_pos_combo = QComboBox()
        self.current_pos_combo.addItems(["top", "jungle", "mid", "bottom", "utility"])
        self.current_pos_combo.currentIndexChanged.connect(self.on_position_changed)
        self.fetch_btn.clicked.connect(self.get_bp_info_and_display)
        self.generate_btn.clicked.connect(self.generate_recommendations)

         # 设置状态栏样式
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2980b9;
                color: white;
                font-size: 14px;
                padding: 5px;
            }
        """)
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px 24px;
                margin-left: 40px;  /* 调整数值来控制空白大小 */
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        self.generate_btn.setStyleSheet("""
            QPushButton {
            background-color: #2C3E50;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 12px 24px;
            margin-left: 2px;  /* 调整数值来控制空白大小 */
            font-size: 16px;
            font-weight: 600;
            text-align: center;  /* 居中文本 */
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        self.generate_btn.setContentsMargins(30, 0, 6, 0)
        self.current_pos_combo.setStyleSheet("""
            QComboBox {
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', -apple-system;
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: 500;
                background-color: white;
                color: #2c3e50;
                min-width: 100px;
                max-width: 120px;
                letter-spacing: 0.3px;
                text-align: center;
            }
            QComboBox:hover {
                border-color: #0078D4;
                background-color: rgba(0, 120, 212, 0.05);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(./assets/dropdown-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                font-family: 'Segoe UI', 'Inter', 'SF Pro Display', -apple-system;
                border: 1px solid rgba(0, 0, 0, 0.1);
                selection-background-color: rgba(0, 120, 212, 0.1);
                selection-color: #2c3e50;
                background-color: white;
                font-weight: 500;
            }
        """)

        # 设置主窗口背景
        main_widget.setStyleSheet("""
            QWidget {
                background-color: #F3F3F3;
            }
        """)
        
        
        control_layout.addWidget(self.fetch_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.current_pos_label)
        control_layout.addWidget(self.current_pos_combo) 
        control_layout.addStretch()
        control_layout.addWidget(self.generate_btn)
        control_layout.addSpacing(40)  # 增加空白区域
        main_layout.addLayout(control_layout)
        
        # BP信息展示区域
        bp_layout = QGridLayout()
        bp_layout.setVerticalSpacing(0)  # 添加垂直间距设置，使其更紧凑
        bp_layout.setHorizontalSpacing(10)  # 保持水平间距合理
        # bp_layout.setSpacing(5)
        bp_layout.setContentsMargins(10, 0, 10, 0)  # 减小外边距
        
        self.bp_panels = {
            "ally_bans": BPInfoPanel("我方禁用英雄"),
            "ally_picks": BPInfoPanel("我方选择英雄"),
            "enemy_bans": BPInfoPanel("敌方禁用英雄"),
            "enemy_picks": BPInfoPanel("敌方选择英雄")
        }
# 特别调整下排面板的上边距
        self.bp_panels["ally_picks"].setContentsMargins(5, 0, 5, 2)  # 减小上边距
        self.bp_panels["enemy_picks"].setContentsMargins(5, 0, 5, 2)
        bp_layout.addWidget(self.bp_panels["ally_bans"], 0, 0)
        bp_layout.addWidget(self.bp_panels["ally_picks"], 1, 0)
        bp_layout.addWidget(self.bp_panels["enemy_bans"], 0, 1)
        bp_layout.addWidget(self.bp_panels["enemy_picks"], 1, 1)
        
        main_layout.addLayout(bp_layout)
        
        # 推荐区域
        rec_layout = QHBoxLayout()
        self.cards = []
        for i in range(3):
            card = HeroCard(f"推荐方案 {i+1}")
            # 设置大小策略为Expanding，使卡片可以随窗口大小变化
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # 添加卡片到布局，并设置相同的拉伸因子
            self.cards.append(card)
            rec_layout.addWidget(card, 1)
        main_layout.addLayout(rec_layout)
        
        # 状态栏
        self.statusBar().showMessage("就绪，请先启动游戏客户端再启动本工具")

    def on_position_changed(self, index):
        """
        当用户从下拉框选择位置时更新position属性
        """
        self.position = self.current_pos_combo.currentText()
        self.set_status_message(f"已选择位置：{self.position}", "info", 2000)
        # 如果需要，也可以更新分析工具中的位置
        if hasattr(self, 'analysis_tool'):
            self.analysis_tool.set_my_pos(self.position)

    def setup_status_bar_styles(self):
        self.status_styles = {
            'error': """
                QStatusBar {
                    background-color: #d32f2f;
                    color: white;
                    font-size: 14px;
                    padding: 5px;
                }
            """,
            'warning': """
                QStatusBar {
                    background-color: #f57c00;
                    color: white;
                    font-size: 14px;
                    padding: 5px;
                }
            """,
            'success': """
                QStatusBar {
                    background-color: #388e3c;
                    color: white;
                    font-size: 14px;
                    padding: 5px;
                }
            """,
            'info': """
                QStatusBar {
                    background-color: #2980b9;
                    color: white;
                    font-size: 14px;
                    padding: 5px;
                }
            """
        }
    
    def set_status_message(self, message, msg_type='info', duration=0):
        """
        设置状态栏消息
        
        参数:
            message (str): 要显示的消息
            msg_type (str): 消息类型 ('error', 'warning', 'success', 'info')
            duration (int): 消息显示时长(毫秒)，0表示持续显示
        """
        if msg_type in self.status_styles:
            self.statusBar().setStyleSheet(self.status_styles[msg_type])
        self.statusBar().showMessage(message, duration)

    def mock_data(self):
        self.hero_pool = [
            "潮汐海灵", "水晶室女", "撼地者",
            "影魔", "幻影刺客", "痛苦女王",
            "风行者", "军团指挥官", "冥界亚龙"
        ]
        
        # 模拟BP数据
        self.bp_data = {
            "enemy_bans": ["烬", "盲僧", "锤石", "提莫", "飞机"],
            "enemy_picks": ["潮汐海灵", "暗裔剑魔","赵信"],
            "ally_bans": ["石头人", "诺手", "凯特琳","芮尔","岩雀"],
            "ally_picks": {
                "top": "剑圣",
                "jungle": "猴子",
                "mid": "卡特琳娜",
                "bottom": "女警",
                "utility": "锤石"
            }
        }
    def get_bp_data(self):
        self.bp_data = {
            "ally_bans":self.analysis_tool.my_team_bans,
            "ally_picks": self.analysis_tool.my_team_picks,
            "enemy_bans": self.analysis_tool.their_team_bans,
            "enemy_picks": self.analysis_tool.their_team_picks
        }
        #print(self.bp_data)
        # self.bp_data = {
        #     "ally_bans": ["烬", "盲僧", "锤石", "提莫", "飞机"],
        #     "ally_picks": ["潮汐海灵", "暗裔剑魔","赵信"],
        #     "enemy_bans": ["石头人", "诺手", "凯特琳","芮尔","岩雀"],
        #     "enemy_picks": ["剑圣", "猴子","卡特琳娜"]
        # }
    def update_bp_panels(self):
        self.get_bp_data()
        for key, panel in self.bp_panels.items():
            panel.update_heroes(self.bp_data[key])

    def get_my_position(self):
        self.position = self.analysis_tool.get_my_pos()

    def update_my_position(self):
        position = self.analysis_tool.get_my_pos()
    
        # 如果位置为空，则默认为top
        if not position or position not in ["top", "jungle", "mid", "bottom", "utility"]:
            position = "top"
    
        # 在下拉框中选择对应的位置
        index = self.current_pos_combo.findText(position)
        if index >= 0:
            self.current_pos_combo.setCurrentIndex(index)

    def get_last_bp_file(self):
        new_folder_path = create_data_folder("data")
        user_files = [f for f in os.listdir(new_folder_path) if f.startswith("user_info_")]
        bp_files = [f for f in os.listdir(new_folder_path) if f.startswith("bp_info_")]
    
        if not user_files or not bp_files:
            self.set_status_message("未找到保存的数据文件", "error", 3000)
            return
    
        # 按文件名排序（因为包含时间戳），获取最新的文件
        latest_user_file = sorted(user_files)[-1]
        latest_bp_file = sorted(bp_files)[-1]
    
        try:
            # 加载用户信息
            with open(f"{new_folder_path}/{latest_user_file}", "r", encoding="utf-8") as f:
                self.user_info_json = json.load(f)
            
            # 加载BP信息
            with open(f"{new_folder_path}/{latest_bp_file}", "r", encoding="utf-8") as f:
                self.bp_info_json = json.load(f)
        
            self.set_status_message(f"已加载历史数据文件: {latest_user_file}, {latest_bp_file}", "success", 3000)
        except Exception as e:
            self.set_status_message(f"加载历史数据文件失败: {str(e)}", "error", 3000)
            return
        
    def get_bp_info_from_lol_client(self):
        new_folder_path = create_data_folder("data")
        
        if self.lol_connector is None:
            self.set_status_message(f"请先启动英雄联盟客户端", "error", 5000)
            raise Exception("请先启动英雄联盟客户端")
        else:
            try:
                self.user_info_json = self.lol_connector.get("lol-summoner/v1/current-summoner")
                self.bp_info_json = self.lol_connector.get("lol-champ-select/v1/session")
            except Exception as e:
                self.set_status_message(f"客户端数据读取失败: {str(e)}", "error", 5000)
                raise Exception("客户端数据读取失败")

                
            # 生成时间戳作为文件名的一部分
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存用户信息
            with open(f"{new_folder_path}/user_info_{timestamp}.json", "w", encoding="utf-8") as f:
                json.dump(self.user_info_json, f, ensure_ascii=False, indent=4)
                
            # 保存BP信息
            with open(f"{new_folder_path}/bp_info_{timestamp}.json", "w", encoding="utf-8") as f:
                json.dump(self.bp_info_json, f, ensure_ascii=False, indent=4)
                
            self.set_status_message(f"数据已保存到 {new_folder_path} 目录", "success", 3000)

    def get_bp_info_and_display(self):
        # 获取历史数据
        #self.get_last_bp_file()
        # 获取客户端数据
        try:
            self.get_bp_info_from_lol_client()
        except Exception as e:
            self.set_status_message(f"BP数据读取失败: {str(e)}", "error", 5000)
            return
        try:
            self.analysis_tool.update_user_info(self.user_info_json)
            self.analysis_tool.update_team_info(self.bp_info_json)
        except Exception as e:
            self.set_status_message(f"BP数据加载失败: {str(e)}", "error", 5000)
        # 更新我的位置
        self.update_my_position()
        # 更新BP面板
        self.update_bp_panels()

    def generate_recommendations(self):
        
        # 强制处理待处理的事件，立即更新UI
        QApplication.processEvents()
        # 显示正在生成推荐的状态
        self.set_status_message("正在生成推荐中...", "info")
        QApplication.processEvents()
        bp_data = self.analysis_tool.get_bp_data()
        # 与LLM通信
        # 创建LLM处理器
        self.llm_handler = LLMHandler(use_api=False)
        
        # 连接信号到槽函数
        self.llm_handler.finished.connect(self.on_recommendations_ready)
        self.llm_handler.error.connect(self.on_llm_error)
        
        # 启动异步处理
        self.thread = self.llm_handler.process_async(bp_data)

    @pyqtSlot(list)
    def on_recommendations_ready(self, recommendations):
        # 这个函数将在LLM处理完成后被调用
        # recommendations是LLM处理的结果（一个列表）
        
        #print("收到推荐结果:", recommendations)
        
        # 更新UI显示推荐结果
        # 例如，假设你有三个推荐卡片：
        # 更新推荐卡片
        for i in range(len(recommendations)):
            self.cards[i].hero_label.setText(recommendations[i]["hero"])
            self.cards[i].reason_label.setText(f"推荐理由：{recommendations[i]['reason']}")
            self.cards[i].strategy_label.setText(f"游戏思路：\n{recommendations[i]['strategy']}")
            
        self.statusBar().showMessage("推荐已更新 - " + ", ".join([r["hero"] for r in recommendations]))
        
        # 可选：断开信号连接，避免多次连接
        self.llm_handler.finished.disconnect(self.on_recommendations_ready)
        self.llm_handler.error.disconnect(self.on_llm_error)
    
    @pyqtSlot(str)
    def on_llm_error(self, error_message):
        # 这个函数将在LLM处理出错时被调用
        
        #print("处理出错:", error_message)
        
        # 显示错误消息
        # 例如，使用状态栏或对话框显示错误
        self.statusBar().showMessage(f"错误: {error_message}")
        
        # 可选：断开信号连接，避免多次连接
        self.llm_handler.finished.disconnect(self.on_recommendations_ready)
        self.llm_handler.error.disconnect(self.on_llm_error)
        
            
