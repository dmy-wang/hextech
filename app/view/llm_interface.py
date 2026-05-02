# coding:utf-8
"""
大模型 API 配置界面
"""
import asyncio
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame,
    QSpacerItem, QSizePolicy
)
from qasync import asyncSlot

from app.common.qfluentwidgets import (
    StrongBodyLabel, BodyLabel, LineEdit, PushButton,
    ComboBox, SpinBox, SwitchButton, CardWidget,
    InfoBar, InfoBarPosition, ProgressRing, TextEdit,
    SettingCardGroup, SettingCard, ExpandLayout,
    isDarkTheme
)
from app.common.style_sheet import StyleSheet
from app.common.logger import logger
from app.common.llm_config import (
    LLMConfig, LLMClient, PROVIDER_PRESETS, llm_client
)
from app.components.seraphine_interface import SeraphineInterface


TAG = "LLMInterface"


class ConnectionTestThread(QThread):
    """连接测试线程"""
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, config: LLMConfig, parent=None):
        super().__init__(parent)
        self.config = config

    def run(self):
        try:
            # 在新线程中创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            client = LLMClient(self.config)
            success = loop.run_until_complete(client.test_connection())
            loop.run_until_complete(client.close())
            loop.close()

            if success:
                self.finished.emit(True, "连接成功！API 配置有效。")
            else:
                self.finished.emit(False, "连接失败，请检查配置。")
        except Exception as e:
            self.finished.emit(False, f"连接失败: {str(e)}")


class ProviderConfigCard(CardWidget):
    """提供商配置卡片"""

    configChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_provider = "deepseek"

        self._initUI()
        self._loadConfig()

    def _initUI(self):
        self.setFixedHeight(280)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.vBoxLayout.setSpacing(12)

        # 标题
        self.titleLabel = StrongBodyLabel("🤖 模型配置", self)
        self.titleLabel.setStyleSheet("font-size: 16px;")

        # 提供商选择
        self.providerLayout = QHBoxLayout()
        self.providerLabel = BodyLabel("提供商:", self)
        self.providerComboBox = ComboBox(self)
        self.providerComboBox.addItems(["DeepSeek", "OpenAI", "Anthropic", "自定义"])
        self.providerComboBox.currentIndexChanged.connect(self._onProviderChanged)

        self.providerLayout.addWidget(self.providerLabel)
        self.providerLayout.addWidget(self.providerComboBox)
        self.providerLayout.addStretch()

        # API Key
        self.apiKeyLayout = QHBoxLayout()
        self.apiKeyLabel = BodyLabel("API Key:", self)
        self.apiKeyEdit = LineEdit(self)
        self.apiKeyEdit.setEchoMode(LineEdit.Password)
        self.apiKeyEdit.setPlaceholderText("输入你的 API Key")
        self.apiKeyEdit.setClearButtonEnabled(True)
        self.apiKeyEdit.setFixedWidth(350)
        self.showKeyButton = PushButton("显示", self)
        self.showKeyButton.setFixedWidth(60)
        self.showKeyButton.clicked.connect(self._toggleKeyVisibility)

        self.apiKeyLayout.addWidget(self.apiKeyLabel)
        self.apiKeyLayout.addWidget(self.apiKeyEdit)
        self.apiKeyLayout.addWidget(self.showKeyButton)
        self.apiKeyLayout.addStretch()

        # Base URL
        self.baseUrlLayout = QHBoxLayout()
        self.baseUrlLabel = BodyLabel("Base URL:", self)
        self.baseUrlEdit = LineEdit(self)
        self.baseUrlEdit.setPlaceholderText("API 基础地址")
        self.baseUrlEdit.setFixedWidth(350)

        self.baseUrlLayout.addWidget(self.baseUrlLabel)
        self.baseUrlLayout.addWidget(self.baseUrlEdit)
        self.baseUrlLayout.addStretch()

        # 模型选择
        self.modelLayout = QHBoxLayout()
        self.modelLabel = BodyLabel("模型:", self)
        self.modelComboBox = ComboBox(self)
        self.modelComboBox.setFixedWidth(200)

        self.modelLayout.addWidget(self.modelLabel)
        self.modelLayout.addWidget(self.modelComboBox)
        self.modelLayout.addStretch()

        # 参数配置
        self.paramsLayout = QHBoxLayout()

        self.tempLabel = BodyLabel("温度:", self)
        self.tempSpinBox = SpinBox(self)
        self.tempSpinBox.setRange(0, 100)
        self.tempSpinBox.setValue(70)
        self.tempSpinBox.setSingleStep(10)
        self.tempSpinBox.setFixedWidth(80)

        self.maxTokensLabel = BodyLabel("最大 Token:", self)
        self.maxTokensSpinBox = SpinBox(self)
        self.maxTokensSpinBox.setRange(100, 8192)
        self.maxTokensSpinBox.setValue(2048)
        self.maxTokensSpinBox.setSingleStep(256)
        self.maxTokensSpinBox.setFixedWidth(100)

        self.paramsLayout.addWidget(self.tempLabel)
        self.paramsLayout.addWidget(self.tempSpinBox)
        self.paramsLayout.addSpacing(30)
        self.paramsLayout.addWidget(self.maxTokensLabel)
        self.paramsLayout.addWidget(self.maxTokensSpinBox)
        self.paramsLayout.addStretch()

        # 布局
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addLayout(self.providerLayout)
        self.vBoxLayout.addLayout(self.apiKeyLayout)
        self.vBoxLayout.addLayout(self.baseUrlLayout)
        self.vBoxLayout.addLayout(self.modelLayout)
        self.vBoxLayout.addLayout(self.paramsLayout)

    def _onProviderChanged(self, index: int):
        """提供商变更"""
        providers = ["deepseek", "openai", "anthropic", "custom"]
        self._current_provider = providers[index]

        preset = PROVIDER_PRESETS.get(self._current_provider, {})

        # 更新 Base URL
        self.baseUrlEdit.setText(preset.get("base_url", ""))

        # 更新模型列表
        self.modelComboBox.clear()
        models = preset.get("models", [])
        if models:
            self.modelComboBox.addItems(models)
            self.modelComboBox.setCurrentText(preset.get("default_model", models[0]))

        # 自定义时允许编辑
        is_custom = self._current_provider == "custom"
        self.baseUrlEdit.setReadOnly(not is_custom)

    def _toggleKeyVisibility(self):
        """切换密钥可见性"""
        if self.apiKeyEdit.echoMode() == LineEdit.Password:
            self.apiKeyEdit.setEchoMode(LineEdit.Normal)
            self.showKeyButton.setText("隐藏")
        else:
            self.apiKeyEdit.setEchoMode(LineEdit.Password)
            self.showKeyButton.setText("显示")

    def getConfig(self) -> LLMConfig:
        """获取当前配置"""
        provider_map = {
            "DeepSeek": "deepseek",
            "OpenAI": "openai",
            "Anthropic": "anthropic",
            "自定义": "custom"
        }

        return LLMConfig(
            provider=provider_map.get(self.providerComboBox.text(), "deepseek"),
            api_key=self.apiKeyEdit.text(),
            base_url=self.baseUrlEdit.text(),
            model=self.modelComboBox.text(),
            temperature=self.tempSpinBox.value() / 100,
            max_tokens=self.maxTokensSpinBox.value()
        )

    def setConfig(self, config: LLMConfig):
        """设置配置"""
        provider_index = {
            "deepseek": 0,
            "openai": 1,
            "anthropic": 2,
            "custom": 3
        }.get(config.provider, 0)

        self.providerComboBox.setCurrentIndex(provider_index)
        self.apiKeyEdit.setText(config.api_key)
        self.baseUrlEdit.setText(config.base_url)

        # 设置模型
        if config.model:
            index = self.modelComboBox.findText(config.model)
            if index >= 0:
                self.modelComboBox.setCurrentIndex(index)
            else:
                self.modelComboBox.addItem(config.model)
                self.modelComboBox.setCurrentText(config.model)

        self.tempSpinBox.setValue(int(config.temperature * 100))
        self.maxTokensSpinBox.setValue(config.max_tokens)

    def _loadConfig(self):
        """加载配置"""
        # 设置默认值
        preset = PROVIDER_PRESETS["deepseek"]
        self.baseUrlEdit.setText(preset["base_url"])
        self.modelComboBox.clear()
        self.modelComboBox.addItems(preset["models"])

        # 如果有保存的配置，加载它
        # TODO: 从持久化配置加载
        pass

    def paintEvent(self, event):
        painter = self.painter
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景
        if isDarkTheme():
            bgColor = QColor(255, 255, 255, 15)
        else:
            bgColor = QColor(0, 0, 0, 10)

        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)


class TestConnectionCard(CardWidget):
    """连接测试卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initUI()

    def _initUI(self):
        self.setFixedHeight(120)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.hBoxLayout.setSpacing(20)

        # 左侧按钮区域
        self.buttonLayout = QVBoxLayout()

        self.titleLabel = StrongBodyLabel("🔌 连接测试", self)
        self.testButton = PushButton("测试连接", self)
        self.testButton.setFixedWidth(120)

        self.buttonLayout.addWidget(self.titleLabel)
        self.buttonLayout.addWidget(self.testButton)

        # 右侧状态区域
        self.statusLayout = QVBoxLayout()

        self.statusLabel = BodyLabel("点击按钮测试 API 连接", self)
        self.statusLabel.setStyleSheet("color: gray;")

        self.progressRing = ProgressRing(self)
        self.progressRing.setFixedSize(24, 24)
        self.progressRing.setVisible(False)

        statusRow = QHBoxLayout()
        statusRow.addWidget(self.progressRing)
        statusRow.addWidget(self.statusLabel)
        statusRow.addStretch()

        self.statusLayout.addLayout(statusRow)

        self.hBoxLayout.addLayout(self.buttonLayout)
        self.hBoxLayout.addLayout(self.statusLayout)
        self.hBoxLayout.addStretch()

    def showTesting(self):
        """显示测试中状态"""
        self.testButton.setEnabled(False)
        self.progressRing.setVisible(True)
        self.statusLabel.setText("正在测试连接...")
        self.statusLabel.setStyleSheet("color: #0093FF;")

    def showResult(self, success: bool, message: str):
        """显示测试结果"""
        self.testButton.setEnabled(True)
        self.progressRing.setVisible(False)
        self.statusLabel.setText(message)

        if success:
            self.statusLabel.setStyleSheet("color: #00BBA3;")
        else:
            self.statusLabel.setStyleSheet("color: #E84057;")

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if isDarkTheme():
            bgColor = QColor(255, 255, 255, 15)
        else:
            bgColor = QColor(0, 0, 0, 10)

        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)


class ChatTestCard(CardWidget):
    """对话测试卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initUI()

    def _initUI(self):
        self.setMinimumHeight(250)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(20, 15, 20, 15)
        self.vBoxLayout.setSpacing(10)

        # 标题
        self.titleLabel = StrongBodyLabel("💬 对话测试", self)

        # 输入框
        self.inputEdit = TextEdit(self)
        self.inputEdit.setPlaceholderText("输入测试消息...")
        self.inputEdit.setFixedHeight(80)

        # 按钮行
        self.buttonLayout = QHBoxLayout()
        self.sendButton = PushButton("发送", self)
        self.sendButton.setFixedWidth(100)
        self.clearButton = PushButton("清空", self)
        self.clearButton.setFixedWidth(80)

        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.clearButton)
        self.buttonLayout.addWidget(self.sendButton)

        # 输出框
        self.outputEdit = TextEdit(self)
        self.outputEdit.setReadOnly(True)
        self.outputEdit.setPlaceholderText("模型回复将显示在这里...")
        self.outputEdit.setFixedHeight(80)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.inputEdit)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addWidget(self.outputEdit)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if isDarkTheme():
            bgColor = QColor(255, 255, 255, 15)
        else:
            bgColor = QColor(0, 0, 0, 10)

        painter.setBrush(bgColor)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)


class LLMInterface(SeraphineInterface):
    """大模型配置界面"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._testThread: Optional[ConnectionTestThread] = None

        self._initUI()
        self._connectSignals()

    def _initUI(self):
        self.setObjectName("llmInterface")

        self.scrollWidget = QWidget()
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.scrollArea = self  # 使用 SmoothScrollArea 基类

        self.contentWidget = QWidget()
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(30, 30, 30, 30)
        self.contentLayout.setSpacing(20)

        # 标题
        self.titleLabel = StrongBodyLabel("🧠 大模型 API 配置", self)
        self.titleLabel.setStyleSheet("font-size: 20px;")

        self.descLabel = BodyLabel(
            "配置大模型 API 以启用 AI 辅助功能。支持 OpenAI 兼容的 API 格式。",
            self
        )
        self.descLabel.setStyleSheet("color: gray;")

        # 提供商配置
        self.providerCard = ProviderConfigCard(self)

        # 连接测试
        self.testCard = TestConnectionCard(self)

        # 对话测试
        self.chatCard = ChatTestCard(self)

        # 布局
        self.contentLayout.addWidget(self.titleLabel)
        self.contentLayout.addWidget(self.descLabel)
        self.contentLayout.addWidget(self.providerCard)
        self.contentLayout.addWidget(self.testCard)
        self.contentLayout.addWidget(self.chatCard)
        self.contentLayout.addStretch()

        self.vBoxLayout.addWidget(self.contentWidget)

    def _connectSignals(self):
        """连接信号"""
        self.testCard.testButton.clicked.connect(self._onTestConnection)
        self.chatCard.sendButton.clicked.connect(self._onSendChat)
        self.chatCard.clearButton.clicked.connect(self._onClearChat)

    def _onTestConnection(self):
        """测试连接"""
        config = self.providerCard.getConfig()

        if not config.api_key:
            InfoBar.warning(
                "警告",
                "请先输入 API Key",
                duration=3000,
                parent=self
            )
            return

        if not config.base_url:
            InfoBar.warning(
                "警告",
                "请先配置 Base URL",
                duration=3000,
                parent=self
            )
            return

        self.testCard.showTesting()

        # 启动测试线程
        self._testThread = ConnectionTestThread(config, self)
        self._testThread.finished.connect(self._onTestFinished)
        self._testThread.start()

    def _onTestFinished(self, success: bool, message: str):
        """测试完成"""
        self.testCard.showResult(success, message)

        if success:
            # 保存配置到全局客户端
            llm_client.update_config(self.providerCard.getConfig())
            InfoBar.success(
                "成功",
                "API 配置已保存",
                duration=3000,
                parent=self
            )

    @asyncSlot()
    async def _onSendChat(self):
        """发送测试消息"""
        message = self.chatCard.inputEdit.toPlainText().strip()

        if not message:
            return

        config = self.providerCard.getConfig()

        if not config.api_key:
            InfoBar.warning(
                "警告",
                "请先配置 API Key",
                duration=3000,
                parent=self
            )
            return

        self.chatCard.sendButton.setEnabled(False)
        self.chatCard.outputEdit.setPlainText("正在生成回复...")

        try:
            client = LLMClient(config)
            response = await client.chat([{"role": "user", "content": message}])
            await client.close()

            self.chatCard.outputEdit.setPlainText(response)
        except Exception as e:
            self.chatCard.outputEdit.setPlainText(f"错误: {str(e)}")
            logger.error(f"Chat test failed: {e}", TAG)
        finally:
            self.chatCard.sendButton.setEnabled(True)

    def _onClearChat(self):
        """清空对话"""
        self.chatCard.inputEdit.clear()
        self.chatCard.outputEdit.clear()
