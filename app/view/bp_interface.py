# coding:utf-8
"""
BP 推荐界面
显示英雄禁用/选择推荐和阵容分析
"""
import asyncio
from typing import List, Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap, QPen, QPainterPath
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QGridLayout,
    QSpacerItem, QSizePolicy, QScrollArea, QStackedWidget
)
from qasync import asyncSlot

from app.common.qfluentwidgets import (
    SmoothScrollArea, CardWidget, StrongBodyLabel, BodyLabel,
    TransparentToolButton, FluentIcon, ProgressRing,
    InfoBar, InfoBarPosition, isDarkTheme
)
from app.common.style_sheet import StyleSheet
from app.common.signals import signalBus
from app.common.config import cfg
from app.common.logger import logger
from app.components.champion_icon_widget import RoundIcon
from app.components.seraphine_interface import SeraphineInterface
from app.lol.connector import connector
from app.ai.recommendation import (
    Recommendation, BanRecommendation, PickRecommendation,
    CompositionAnalysis, Position
)
from app.ai.bp_analyzer import BPAnalyzer


TAG = "BPInterface"


class ChampionRecommendationCard(CardWidget):
    """英雄推荐卡片"""

    clicked = pyqtSignal(int)  # champion_id

    def __init__(self, recommendation, parent=None):
        super().__init__(parent)
        self.recommendation = recommendation
        self.champion_id = recommendation.champion_id
        self.champion_name = recommendation.champion_name
        self.priority = recommendation.priority

        self.isHover = False

        self._initUI()
        self.setFixedSize(100, 140)

    def _initUI(self):
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(8, 8, 8, 8)
        self.vBoxLayout.setSpacing(6)

        # 英雄图标
        self.iconWidget = QWidget()
        self.iconWidget.setFixedSize(60, 60)
        self.iconLayout = QHBoxLayout(self.iconWidget)
        self.iconLayout.setContentsMargins(0, 0, 0, 0)

        # 英雄名称
        self.nameLabel = BodyLabel(self.champion_name, self)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self.nameLabel.setStyleSheet("font-weight: bold;")

        # 优先级进度环
        self.priorityRing = ProgressRing(self)
        self.priorityRing.setFixedSize(40, 40)
        self.priorityRing.setValue(int(self.priority))
        self.priorityRing.setStrokeWidth(4)

        # 优先级标签
        self.priorityLabel = BodyLabel(f"{int(self.priority)}%", self)

        # 布局
        self.vBoxLayout.addWidget(self.iconWidget, alignment=Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.nameLabel, alignment=Qt.AlignCenter)
        self.vBoxLayout.addWidget(self.priorityRing, alignment=Qt.AlignCenter)

    async def loadIcon(self):
        """异步加载英雄图标"""
        try:
            icon_path = await connector.getChampionIcon(self.champion_id)
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # 创建圆形图标
                self.iconLabel = RoundIcon(
                    icon=icon_path,
                    diameter=56,
                    borderWidth=2
                )
                self.iconLayout.addWidget(self.iconLabel)
        except Exception as e:
            logger.error(f"Failed to load champion icon: {e}", TAG)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景
        if self.isHover:
            bgColor = QColor(255, 255, 255, 30) if isDarkTheme() else QColor(0, 0, 0, 20)
        else:
            bgColor = QColor(255, 255, 255, 15) if isDarkTheme() else QColor(0, 0, 0, 10)

        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

        # 根据优先级绘制边框
        if self.priority >= 80:
            color = QColor(232, 64, 87)  # 红色 - 强烈推荐
        elif self.priority >= 60:
            color = QColor(0, 147, 255)  # 蓝色 - 推荐
        elif self.priority >= 40:
            color = QColor(0, 187, 163)  # 青色 - 可选
        else:
            color = QColor(154, 164, 175)  # 灰色 - 备选

        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)

    def enterEvent(self, event):
        self.isHover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.isHover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.champion_id)


class BanRecommendationSection(QFrame):
    """Ban 推荐区域"""

    championClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recommendations: List[BanRecommendation] = []

        self._initUI()

    def _initUI(self):
        self.setFixedHeight(200)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 15, 20, 15)
        self.mainLayout.setSpacing(10)

        # 标题
        self.titleLabel = StrongBodyLabel("🚫 禁用推荐", self)
        self.titleLabel.setStyleSheet("font-size: 16px;")

        # 推荐卡片容器
        self.cardsLayout = QHBoxLayout()
        self.cardsLayout.setSpacing(12)
        self.cardsLayout.addStretch()

        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addLayout(self.cardsLayout)

    async def updateRecommendations(self, recommendations: List[BanRecommendation]):
        """更新推荐"""
        self.recommendations = recommendations

        # 清空现有卡片
        self._clearCards()

        # 添加新卡片
        for rec in recommendations[:5]:  # 最多显示5个
            card = ChampionRecommendationCard(rec, self)
            card.clicked.connect(self.championClicked.emit)
            await card.loadIcon()
            self.cardsLayout.addWidget(card)

        self.cardsLayout.addStretch()
        self.update()

    def _clearCards(self):
        while self.cardsLayout.count() > 1:  # 保留最后的 stretch
            item = self.cardsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class PickRecommendationSection(QFrame):
    """Pick 推荐区域"""

    championClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recommendations: List[PickRecommendation] = []
        self.currentPosition: str = ""

        self._initUI()

    def _initUI(self):
        self.setMinimumHeight(250)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 15, 20, 15)
        self.mainLayout.setSpacing(10)

        # 标题行
        self.headerLayout = QHBoxLayout()
        self.titleLabel = StrongBodyLabel("⚔️ 选择推荐", self)
        self.titleLabel.setStyleSheet("font-size: 16px;")

        self.positionLabel = BodyLabel("", self)
        self.positionLabel.setStyleSheet("color: #0093FF; font-size: 14px;")

        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addSpacing(10)
        self.headerLayout.addWidget(self.positionLabel)
        self.headerLayout.addStretch()

        # 推荐卡片容器
        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cardsWidget = QWidget()
        self.cardsLayout = QHBoxLayout(self.cardsWidget)
        self.cardsLayout.setContentsMargins(0, 0, 0, 0)
        self.cardsLayout.setSpacing(12)
        self.cardsLayout.addStretch()

        self.scrollArea.setWidget(self.cardsWidget)
        self.scrollArea.setFixedHeight(160)

        # 推荐理由
        self.reasonLabel = BodyLabel("", self)
        self.reasonLabel.setWordWrap(True)
        self.reasonLabel.setStyleSheet("color: gray; font-size: 12px;")

        self.mainLayout.addLayout(self.headerLayout)
        self.mainLayout.addWidget(self.scrollArea)
        self.mainLayout.addWidget(self.reasonLabel)

    async def updateRecommendations(self, recommendations: List[PickRecommendation], position: str = ""):
        """更新推荐"""
        self.recommendations = recommendations
        self.currentPosition = position

        # 更新位置标签
        if position:
            self.positionLabel.setText(f"位置: {position}")

        # 清空现有卡片
        self._clearCards()

        # 添加新卡片
        for rec in recommendations[:8]:  # 最多显示8个
            card = ChampionRecommendationCard(rec, self)
            card.clicked.connect(self.championClicked.emit)
            await card.loadIcon()
            self.cardsLayout.addWidget(card)

        self.cardsLayout.addStretch()

        # 更新推荐理由
        if recommendations:
            top_rec = recommendations[0]
            reasons = ", ".join([r.value for r in top_rec.reasons]) if top_rec.reasons else "综合推荐"
            self.reasonLabel.setText(f"推荐理由: {reasons}")
        else:
            self.reasonLabel.setText("暂无推荐")

        self.update()

    def _clearCards(self):
        while self.cardsLayout.count() > 1:
            item = self.cardsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class CompositionAnalysisSection(QFrame):
    """阵容分析区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis: Optional[CompositionAnalysis] = None

        self._initUI()

    def _initUI(self):
        self.setMinimumHeight(150)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 15, 20, 15)
        self.mainLayout.setSpacing(10)

        # 标题
        self.titleLabel = StrongBodyLabel("📊 阵容分析", self)
        self.titleLabel.setStyleSheet("font-size: 16px;")

        # 分析内容
        self.contentLayout = QHBoxLayout()

        # 己方阵容
        self.allyLayout = QVBoxLayout()
        self.allyTitleLabel = BodyLabel("己方阵容", self)
        self.allyTitleLabel.setStyleSheet("font-weight: bold; color: #0093FF;")
        self.allyContentLabel = BodyLabel("等待分析...", self)
        self.allyContentLabel.setWordWrap(True)
        self.allyLayout.addWidget(self.allyTitleLabel)
        self.allyLayout.addWidget(self.allyContentLabel)
        self.allyLayout.addStretch()

        # 敌方阵容
        self.enemyLayout = QVBoxLayout()
        self.enemyTitleLabel = BodyLabel("敌方阵容", self)
        self.enemyTitleLabel.setStyleSheet("font-weight: bold; color: #E84057;")
        self.enemyContentLabel = BodyLabel("等待分析...", self)
        self.enemyContentLabel.setWordWrap(True)
        self.enemyLayout.addWidget(self.enemyTitleLabel)
        self.enemyLayout.addWidget(self.enemyContentLabel)
        self.enemyLayout.addStretch()

        # 战术建议
        self.suggestionLayout = QVBoxLayout()
        self.suggestionTitleLabel = BodyLabel("战术建议", self)
        self.suggestionTitleLabel.setStyleSheet("font-weight: bold; color: #00BBA3;")
        self.suggestionContentLabel = BodyLabel("等待分析...", self)
        self.suggestionContentLabel.setWordWrap(True)
        self.suggestionLayout.addWidget(self.suggestionTitleLabel)
        self.suggestionLayout.addWidget(self.suggestionContentLabel)
        self.suggestionLayout.addStretch()

        self.contentLayout.addLayout(self.allyLayout)
        self.contentLayout.addLayout(self.enemyLayout)
        self.contentLayout.addLayout(self.suggestionLayout)

        self.mainLayout.addWidget(self.titleLabel)
        self.mainLayout.addLayout(self.contentLayout)

    def updateAnalysis(self, analysis: Optional[CompositionAnalysis]):
        """更新阵容分析"""
        self.analysis = analysis

        if not analysis:
            self.allyContentLabel.setText("等待分析...")
            self.enemyContentLabel.setText("等待分析...")
            self.suggestionContentLabel.setText("等待分析...")
            return

        # 己方优势
        ally_text = ""
        if analysis.advantages:
            ally_text = "优势:\n" + "\n".join(f"• {a}" for a in analysis.advantages[:3])
        if analysis.disadvantages:
            if ally_text:
                ally_text += "\n\n"
            ally_text += "劣势:\n" + "\n".join(f"• {d}" for d in analysis.disadvantages[:3])
        self.allyContentLabel.setText(ally_text or "暂无明显优劣势")

        # 敌方分析
        enemy_text = ""
        if analysis.enemy_composition:
            scores = analysis.enemy_composition.to_dict()
            enemy_text = f"开团: {scores['engage']:.0f}% | Poke: {scores['poke']:.0f}%\n"
            enemy_text += f"保护: {scores['peel']:.0f}% | 团战: {scores['team_fight']:.0f}%"
        self.enemyContentLabel.setText(enemy_text or "暂无数据")

        # 战术建议
        if analysis.suggestions:
            suggestion_text = "\n".join(f"• {s}" for s in analysis.suggestions[:3])
        else:
            suggestion_text = "暂无特殊建议"
        self.suggestionContentLabel.setText(suggestion_text)


class BPStatusWidget(QFrame):
    """BP 状态显示"""

    aiAnalyzeClicked = pyqtSignal()  # AI 分析按钮点击信号

    def __init__(self, parent=None):
        super().__init__(parent)

        self._initUI()

    def _initUI(self):
        self.setFixedHeight(50)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 10, 20, 10)

        # 当前状态
        self.statusLabel = StrongBodyLabel("等待 BP 开始...", self)

        # 阶段指示器
        self.phaseLabel = BodyLabel("", self)
        self.phaseLabel.setStyleSheet("color: #00BBA3;")

        # AI 分析按钮
        from app.common.qfluentwidgets import PushButton, FluentIcon
        self.aiAnalyzeButton = PushButton("🤖 AI 分析", self)
        self.aiAnalyzeButton.setFixedWidth(100)
        self.aiAnalyzeButton.setToolTip("使用大模型进行智能分析")
        self.aiAnalyzeButton.clicked.connect(self.aiAnalyzeClicked.emit)

        self.mainLayout.addWidget(self.statusLabel)
        self.mainLayout.addStretch()
        self.mainLayout.addWidget(self.phaseLabel)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addWidget(self.aiAnalyzeButton)

    def updateStatus(self, phase: str, position: str = ""):
        """更新状态"""
        phase_text = {
            "ban": "禁用阶段",
            "pick": "选择阶段",
            "": "等待中"
        }.get(phase, phase)

        if phase:
            self.statusLabel.setText(f"当前阶段: {phase_text}")
            if position:
                self.phaseLabel.setText(f"需要位置: {position}")
            else:
                self.phaseLabel.setText("")
        else:
            self.statusLabel.setText("等待 BP 开始...")
            self.phaseLabel.setText("")


class BPInterface(SeraphineInterface):
    """BP 推荐界面"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.bp_analyzer = BPAnalyzer()
        self.current_recommendation: Optional[Recommendation] = None

        # 存储 BP 状态供 LLM 分析使用
        self._bp_state: dict = {}
        self._tier_data: dict = {}
        self._champion_names: Dict[int, str] = {}

        self._initUI()
        self._connectSignals()

    def _initUI(self):
        self.setObjectName("bpInterface")

        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.scrollArea = SmoothScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(30, 30, 30, 30)
        self.contentLayout.setSpacing(20)

        # 标题
        self.titleLabel = StrongBodyLabel("🎯 BP 助手", self)
        self.titleLabel.setStyleSheet("font-size: 20px;")

        # 状态栏
        self.statusWidget = BPStatusWidget(self)

        # Ban 推荐区域
        self.banSection = BanRecommendationSection(self)

        # Pick 推荐区域
        self.pickSection = PickRecommendationSection(self)

        # 阵容分析区域
        self.analysisSection = CompositionAnalysisSection(self)

        # 布局
        self.contentLayout.addWidget(self.titleLabel)
        self.contentLayout.addWidget(self.statusWidget)
        self.contentLayout.addWidget(self.banSection)
        self.contentLayout.addWidget(self.pickSection)
        self.contentLayout.addWidget(self.analysisSection)
        self.contentLayout.addStretch()

        self.scrollArea.setWidget(self.contentWidget)
        self.vBoxLayout.addWidget(self.scrollArea)

        StyleSheet.GAME_INFO_INTERFACE.apply(self)

    def _connectSignals(self):
        """连接信号"""
        signalBus.bpRecommendationUpdated.connect(self._onRecommendationUpdated)
        signalBus.bpPhaseChanged.connect(self._onPhaseChanged)

        # 点击英雄卡片
        self.banSection.championClicked.connect(self._onChampionClicked)
        self.pickSection.championClicked.connect(self._onChampionClicked)

        # AI 分析按钮
        self.statusWidget.aiAnalyzeClicked.connect(self._onAIAnalyze)

    @asyncSlot(dict)
    async def _onRecommendationUpdated(self, data: dict):
        """推荐更新"""
        logger.info("BP recommendation updated", TAG)

        # 解析推荐数据
        from app.ai.recommendation import BanRecommendation, PickRecommendation, Position

        # 更新 Ban 推荐
        if data.get('bans'):
            ban_recs = []
            for b in data['bans']:
                ban_recs.append(BanRecommendation(
                    champion_id=b['champion_id'],
                    champion_name=b['champion_name'],
                    priority=b['priority'],
                    reasons=[],
                    threat_score=b.get('threat_score', 0)
                ))
            await self.banSection.updateRecommendations(ban_recs)

        # 更新 Pick 推荐
        if data.get('picks'):
            pick_recs = []
            for p in data['picks']:
                pick_recs.append(PickRecommendation(
                    champion_id=p['champion_id'],
                    champion_name=p['champion_name'],
                    position=Position(p['position']),
                    priority=p['priority'],
                    reasons=[]
                ))
            await self.pickSection.updateRecommendations(
                pick_recs,
                data.get('position', '')
            )

        # 更新阵容分析
        if data.get('composition'):
            # TODO: 实现阵容分析解析
            pass

    @asyncSlot(str)
    async def _onPhaseChanged(self, phase: str):
        """阶段变化"""
        logger.info(f"BP phase changed: {phase}", TAG)
        self.statusWidget.updateStatus(phase)

    def _onChampionClicked(self, champion_id: int):
        """点击英雄"""
        logger.info(f"Champion clicked: {champion_id}", TAG)
        # 可以在这里添加详情显示或其他功能

    @asyncSlot()
    async def _onAIAnalyze(self):
        """AI 分析按钮点击"""
        from app.common.qfluentwidgets import InfoBar
        from app.common.llm_config import llm_client

        # 检查 LLM 是否配置
        if not llm_client.config.api_key:
            InfoBar.warning(
                "提示",
                "请先在 LLM Config 页面配置 API Key",
                duration=3000,
                parent=self
            )
            return

        # 检查是否有 BP 数据
        if not self._bp_state:
            InfoBar.warning(
                "提示",
                "等待 BP 数据加载...",
                duration=3000,
                parent=self
            )
            return

        logger.info("Starting AI analysis", TAG)
        self.statusWidget.aiAnalyzeButton.setEnabled(False)
        self.statusWidget.aiAnalyzeButton.setText("分析中...")

        try:
            from app.ai.llm_bp_service import llm_bp_service
            from app.lol.connector import connector

            # 获取英雄名称映射
            champion_names = {}
            for champ_id in range(1, 1000):
                try:
                    name = connector.manager.getChampionNameById(champ_id)
                    if name:
                        champion_names[champ_id] = name
                except:
                    pass

            # 获取 BP 状态
            ally_picks = self._bp_state.get('my_picks', [])
            enemy_picks = self._bp_state.get('their_picks', [])
            ally_bans = self._bp_state.get('my_bans', [])
            enemy_bans = self._bp_state.get('their_bans', [])
            phase = self._bp_state.get('phase', '')

            # 获取版本强势英雄
            tier_champions = []
            for pos, champs in self._tier_data.get('data', {}).items():
                tier_champions.extend(champs)

            if phase == 'ban':
                # Ban 阶段分析
                recommendations = await llm_bp_service.get_llm_ban_recommendations(
                    ally_picks=ally_picks,
                    enemy_picks=enemy_picks,
                    ally_bans=ally_bans,
                    enemy_bans=enemy_bans,
                    tier_champions=tier_champions,
                    champion_names=champion_names
                )

                if recommendations:
                    await self.banSection.updateRecommendations(recommendations)
                    InfoBar.success(
                        "AI 分析完成",
                        f"已生成 {len(recommendations)} 个 Ban 推荐",
                        duration=3000,
                        parent=self
                    )
            else:
                # Pick 阶段分析
                position_str = self._bp_state.get('current_position', 'MID')
                position_map = {
                    'TOP': Position.TOP,
                    'JUNGLE': Position.JUNGLE,
                    'MID': Position.MID,
                    'ADC': Position.ADC,
                    'SUPPORT': Position.SUPPORT
                }
                position = position_map.get(position_str, Position.MID)

                recommendations = await llm_bp_service.get_llm_pick_recommendations(
                    position=position,
                    ally_picks=ally_picks,
                    enemy_picks=enemy_picks,
                    ally_bans=ally_bans,
                    enemy_bans=enemy_bans,
                    player_masteries={},  # TODO: 获取玩家熟练度
                    tier_champions=tier_champions,
                    champion_names=champion_names
                )

                if recommendations:
                    await self.pickSection.updateRecommendations(recommendations, position_str)
                    InfoBar.success(
                        "AI 分析完成",
                        f"已生成 {len(recommendations)} 个 Pick 推荐",
                        duration=3000,
                        parent=self
                    )

        except Exception as e:
            logger.error(f"AI analysis failed: {e}", TAG)
            InfoBar.error(
                "AI 分析失败",
                str(e),
                duration=5000,
                parent=self
            )
        finally:
            self.statusWidget.aiAnalyzeButton.setEnabled(True)
            self.statusWidget.aiAnalyzeButton.setText("🤖 AI 分析")

    def clear(self):
        """清空界面"""
        self.statusWidget.updateStatus("")
        self.banSection._clearCards()
        self.pickSection._clearCards()
        self.analysisSection.updateAnalysis(None)
        self._bp_state = {}

    async def initialize(self):
        """初始化"""
        logger.info("Initializing BP interface", TAG)

        # 预加载 OP.GG 数据
        try:
            from app.lol.opgg import opgg
            tier_data = await opgg.getTierList("kr", "ranked", "platinum_plus")
            self.bp_analyzer.set_opgg_data(tier_data)
            self._tier_data = tier_data  # 保存供 LLM 分析使用
            logger.info("OP.GG data loaded", TAG)
        except Exception as e:
            logger.error(f"Failed to load OP.GG data: {e}", TAG)

    def updateBPState(self, state: dict):
        """更新 BP 状态"""
        self._bp_state = state
