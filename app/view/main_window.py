# coding:utf-8
"""
Hextech 主窗口
AI 游戏辅助工具
"""
import os
import sys
import traceback
import time
from pathlib import Path

import asyncio
from aiohttp.client_exceptions import ClientConnectorError
from qasync import asyncClose, asyncSlot
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QTimer
from PyQt5.QtGui import QIcon, QImage
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon

from app.common.qfluentwidgets import (
    NavigationItemPosition, InfoBar, InfoBarPosition, Action,
    FluentWindow, SplashScreen, FluentIcon
)

from app.view.start_interface import StartInterface
from app.view.bp_interface import BPInterface
from app.common.util import getLolClientPid, getTasklistPath, getLoLPathByRegistry
from app.components.avatar_widget import NavigationAvatarWidget
from app.components.temp_system_tray_menu import TmpSystemTrayMenu
from app.common.icons import Icon
from app.common.config import cfg, VERSION, BETA
from app.common.logger import logger
from app.common.signals import signalBus
from app.components.message_box import WaitingForLolMessageBox, ExceptionMessageBox
from app.lol.exceptions import RetryMaximumAttempts
from app.lol.listener import LolProcessExistenceListener, StoppableThread
from app.lol.connector import connector
from app.lol.champions import ChampionAlias

TAG = "MainWindow"


class MainWindow(FluentWindow):
    mainWindowHide = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        logger.critical(f"Hextech started, version: {BETA or VERSION}", TAG)

        self.windowSize = cfg.get(cfg.windowSize)

        self.__initConfig()
        self.__initWindow()
        self.__initSystemTray()

        # 创建子界面
        self.startInterface = StartInterface(self)
        self.bpInterface = BPInterface(self)

        logger.critical("Hextech interfaces initialized", TAG)

        # 创建监听器
        self.isClientProcessRunning = False
        self.processListener = LolProcessExistenceListener(self)

        logger.critical("Hextech listeners started", TAG)

        self.currentSummoner = None
        self.lastTipsTime = 0
        self.lastTipsType = None

        self.__initInterface()
        self.__initNavigation()
        self.__initListener()
        self.__connectSignalToSlot()
        self.__autoStartLolClient()

        self.splashScreen.finish()

        logger.critical("Hextech initialized", TAG)

    def __initConfig(self):
        folder = cfg.get(cfg.lolFolder)

        isEmptyList = folder == []
        isEmptyStr = folder == str(Path("").absolute()).replace("\\", "/") or folder == ""

        if isEmptyList or isEmptyStr:
            path = getLoLPathByRegistry()
            if not path:
                return
            cfg.set(cfg.lolFolder, [path])
            return

        if type(folder) is str:
            cfg.set(cfg.lolFolder, [folder])

    def __initInterface(self):
        self.__lockInterface()
        self.startInterface.setObjectName("startInterface")
        self.bpInterface.setObjectName("bpInterface")

    def __initNavigation(self):
        pos = NavigationItemPosition.SCROLL

        self.navigationInterface.addSeparator(NavigationItemPosition.TOP)

        self.addSubInterface(
            self.startInterface, Icon.HOME, self.tr("Start"), pos)
        self.addSubInterface(
            self.bpInterface, Icon.GAME, self.tr("BP Assistant"), pos)

        pos = NavigationItemPosition.BOTTOM

        self.avatarWidget = NavigationAvatarWidget(
            avatar="app/resource/images/game.png", name=self.tr("Start LOL"))
        self.navigationInterface.addWidget(
            routeKey="avatar",
            widget=self.avatarWidget,
            onClick=self.__onAvatarWidgetClicked,
            position=pos,
        )

        self.navigationInterface.setExpandWidth(250)
        self.navigationInterface.setMinimumExpandWidth(1321)

    def __connectSignalToSlot(self):
        signalBus.tasklistNotFound.connect(self.__showWaitingMessageBox)
        signalBus.lolClientStarted.connect(self.__onLolClientStarted)
        signalBus.lolClientEnded.connect(self.__onLolClientEnded)
        signalBus.lolClientChanged.connect(self.__onLolClientChanged)
        signalBus.terminateListeners.connect(self.__terminateListeners)
        signalBus.currentSummonerProfileChanged.connect(
            self.__onCurrentSummonerProfileChanged)
        signalBus.gameStatusChanged.connect(self.__onGameStatusChanged)
        signalBus.champSelectChanged.connect(self.__onChampSelectChanged)
        signalBus.lcuApiExceptionRaised.connect(self.__onShowLcuConnectError)
        signalBus.getCmdlineError.connect(self.__showNeedAdminMessageBox)

        self.stackedWidget.currentChanged.connect(
            self.__onCurrentStackedChanged)
        self.mainWindowHide.connect(self.__onWindowHide)

    def __initWindow(self):
        self.setMinimumSize(1134, 826)
        self.setWindowIcon(QIcon("app/resource/images/logo.png"))
        self.setWindowTitle("Hextech")

        self.titleBar.titleLabel.setStyleSheet(
            "QLabel {font: 13px 'Segoe UI', 'Microsoft YaHei';}")
        self.titleBar.hBoxLayout.insertSpacing(0, 10)

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

        self.oldHook = sys.excepthook
        sys.excepthook = self.exceptHook

    @asyncSlot(str, BaseException)
    async def __onShowLcuConnectError(self, api, obj):
        if time.time() - self.lastTipsTime < 1.5 and self.lastTipsType is type(obj):
            return
        else:
            self.lastTipsTime = time.time()
            self.lastTipsType = type(obj)

        if type(obj) is RetryMaximumAttempts:
            msg = self.tr("Exceeded maximum retry attempts.")
        else:
            msg = repr(obj)

        InfoBar.error(
            self.tr("LCU request error"),
            self.tr(f"Connect API") + f" {api}: {msg}",
            duration=5000,
            orient=Qt.Vertical,
            parent=self,
            position=InfoBarPosition.BOTTOM_RIGHT
        )

    def __onWindowHide(self, hide):
        if hide:
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()

    def __showWaitingMessageBox(self):
        self.tasklistEnabled = False
        msgBox = WaitingForLolMessageBox(self.window())
        if not msgBox.exec():
            signalBus.terminateListeners.emit()
            sys.exit()

    def __showNeedAdminMessageBox(self):
        from app.components.message_box import MessageBox
        msgBox = MessageBox(self.tr("Get cmdline error"), self.tr(
            "Try running Hextech as an administrator"), self.window())
        msgBox.cancelButton.setVisible(False)
        msgBox.exec()
        signalBus.terminateListeners.emit()
        sys.exit()

    def __initSystemTray(self):
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setToolTip("Hextech")
        self.trayIcon.setIcon(QIcon("app/resource/images/logo.png"))

        bpAction = Action(Icon.GAME, self.tr("BP Assistant"), self)
        quitAction = Action(Icon.EXIT, self.tr('Quit'), self)

        def quit():
            self.isTrayExit = True
            self.close()

        bpAction.triggered.connect(
            lambda: self.checkAndSwitchTo(self.bpInterface))
        quitAction.triggered.connect(quit)

        self.trayMenu = TmpSystemTrayMenu(self)
        self.trayMenu.addAction(bpAction)
        self.trayMenu.addAction(quitAction)

        self.trayIcon.setContextMenu(self.trayMenu)
        self.trayIcon.activated.connect(lambda reason: self.show(
        ) if reason == QSystemTrayIcon.DoubleClick else None)
        self.trayIcon.show()

    def show(self):
        self.activateWindow()
        self.setWindowState(self.windowState() & ~
                            Qt.WindowMinimized | Qt.WindowActive)
        self.showNormal()

    def __initListener(self):
        self.processListener.start()

    async def __changeCareerToCurrentSummoner(self):
        summoner = await connector.getCurrentSummoner()
        self.currentSummoner = summoner

    @asyncSlot(int)
    async def __onLolClientStarted(self, pid):
        logger.info(f"League of Legends client started: {pid}", TAG)
        res = await self.__startConnector(pid)
        if not res:
            return

        self.isClientProcessRunning = True
        await self.__changeCareerToCurrentSummoner()
        await self.__updateAvatarIconName()

        self.startInterface.hideLoadingPage()

        # 初始化英雄别名
        await ChampionAlias.checkAndUpdate()

        self.__unlockInterface()

    async def __startConnector(self, pid):
        try:
            await connector.start(pid)
            return True
        except RetryMaximumAttempts:
            await connector.close()
            if self.processListener.isRunning():
                self.processListener.runningPid = 0
            else:
                signalBus.tasklistNotFound.emit()
            return False

    @asyncSlot(int)
    async def __onLolClientChanged(self, pid):
        logger.critical(f"League of Legends client changed: {pid}", TAG)
        await self.__onLolClientEnded()
        self.processListener.runningPid = pid
        await self.__onLolClientStarted(pid)

    @asyncSlot()
    async def __onLolClientEnded(self):
        logger.critical("League of Legends client ended", TAG)
        await connector.close()

        self.isClientProcessRunning = False
        self.currentSummoner = None

        await self.__updateAvatarIconName()

        self.startInterface.showLoadingPage()
        self.setWindowTitle("Hextech")
        self.checkAndSwitchTo(self.startInterface)
        self.__lockInterface()

    async def __updateAvatarIconName(self):
        if self.currentSummoner:
            try:
                iconId = self.currentSummoner['profileIconId']
                icon = await connector.getProfileIcon(iconId)
                name = (self.currentSummoner.get("gameName")
                        or self.currentSummoner['displayName'])
            except:
                icon = "app/resource/images/game.png"
                name = self.tr("Start LOL")
        else:
            icon = "app/resource/images/game.png"
            name = self.tr("Start LOL")

        self.avatarWidget.avatar = QImage(icon).scaled(
            24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.avatarWidget.name = name
        self.avatarWidget.repaint()

    def __autoStartLolClient(self):
        if self.isClientProcessRunning:
            return

        if not cfg.get(cfg.enableStartLolWithApp):
            return

        path = getTasklistPath()
        pid = getLolClientPid(path)

        if pid == 0:
            self.__startLolClient()

    def __startLolClient(self):
        for clientName in ("client.exe", "LeagueClient.exe"):
            path = f'{cfg.get(cfg.lolFolder)[0]}/{clientName}'
            if os.path.exists(path):
                os.popen(f'"{path}"')
                break

    def __onAvatarWidgetClicked(self):
        if not self.isClientProcessRunning:
            self.__startLolClient()

    def checkAndSwitchTo(self, interface):
        index = self.stackedWidget.indexOf(interface)
        if not self.stackedWidget.currentIndex() == index:
            self.navigationInterface.widget(interface.objectName()).click()

    def __unlockInterface(self):
        pass

    def __lockInterface(self):
        pass

    def __terminateListeners(self):
        self.processListener.terminate()

    @asyncClose
    async def closeEvent(self, a0) -> None:
        self.__terminateListeners()
        cfg.set(cfg.windowSize, self.windowSize)
        return super().closeEvent(a0)

    @asyncSlot(dict)
    async def __onCurrentSummonerProfileChanged(self, data: dict):
        self.currentSummoner = data
        await self.__updateAvatarIconName()
        logger.debug(f"Update Summoner Info : {data}", TAG)

    @asyncSlot(str)
    async def __onGameStatusChanged(self, status):
        logger.critical(f"Client gameflow phase changed: {status}", TAG)

        if status == 'ChampSelect':
            await self.__onChampionSelectBegin()
        elif status == 'GameStart':
            await self.__onGameStart()
        elif status == 'InProgress':
            pass
        elif status in ['None', 'Lobby']:
            await self.__onGameEnd()

    async def __onChampionSelectBegin(self):
        """进入英雄选择界面"""
        logger.info("Champion select began", TAG)

        # 切换到 BP 界面
        self.checkAndSwitchTo(self.bpInterface)

        # 初始化 BP 分析器
        await self.bpInterface.initialize()

    @asyncSlot(dict)
    async def __onChampSelectChanged(self, data):
        """BP 状态变化"""
        data = data['data']
        phase = data.get('timer', {}).get('phase', '')
        logger.debug(f"Champ select changed: {phase}", TAG)

        # 更新 BP 推荐
        try:
            recommendation = await self.bpInterface.bp_analyzer.analyze(data)
            signalBus.bpRecommendationUpdated.emit(recommendation.to_dict())
            signalBus.bpPhaseChanged.emit(phase.lower())
        except Exception as e:
            logger.error(f"Failed to analyze BP: {e}", TAG)

    async def __onGameStart(self):
        """进入游戏"""
        logger.info("Game started", TAG)
        # TODO: 赛前分析完成

    async def __onGameEnd(self):
        """游戏结束"""
        logger.info("Game ended", TAG)
        self.bpInterface.clear()

    def __onCurrentStackedChanged(self, index):
        pass

    def eventFilter(self, obj, e: QEvent):
        if e.type() == QEvent.Type.Resize:
            self.windowSize = self.size()
        if e.type() == QEvent.Type.Move:
            self.resize(self.windowSize)
        return super().eventFilter(obj, e)

    def exceptHook(self, ty, value, tb):
        tracebackFormat = traceback.format_exception(ty, value, tb)
        title = self.tr('Exception occurred')
        content = "".join(tracebackFormat)

        if ty in [ConnectionRefusedError, ClientConnectorError]:
            return

        logger.error(f"Exception occurred:\n{content}", "Crash")
        content = f"Hextech ver.{BETA or VERSION}\n{'-'*5}\n{content}"

        w = ExceptionMessageBox(title, content, self.window())
        if w.exec():
            import pyperclip
            pyperclip.copy(content)

        self.oldHook(ty, value, tb)
        signalBus.terminateListeners.emit()
        sys.exit()
