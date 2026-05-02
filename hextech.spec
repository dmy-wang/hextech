# -*- mode: python ; coding: utf-8 -*-
"""
Hextech PyInstaller 打包配置
在 Windows 上运行: pyinstaller hextech.spec
"""

import sys
import os

block_cipher = None

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # 资源文件
        ('app/resource', 'app/resource'),
        ('champion_mapping.json', '.'),
    ],
    hiddenimports=[
        # PyQt5 相关
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'qasync',
        # qfluentwidgets 相关
        'qfluentwidgets',
        'qfluentwidgets.common',
        'qfluentwidgets.components',
        'qfluentwidgets.components.widgets',
        # Windows 特定模块
        'winreg',
        'win32api',
        'win32gui',
        'win32con',
        'pywin32_system32',
        # 项目模块
        'app.common',
        'app.common.config',
        'app.common.logger',
        'app.common.signals',
        'app.common.style_sheet',
        'app.common.icons',
        'app.common.qfluentwidgets',
        'app.common.util',
        'app.common.llm_config',
        'app.common.update',
        'app.lol',
        'app.lol.connector',
        'app.lol.listener',
        'app.lol.opgg',
        'app.lol.tools',
        'app.lol.exceptions',
        'app.lol.aram',
        'app.lol.champions',
        'app.ai',
        'app.ai.recommendation',
        'app.ai.champion_evaluator',
        'app.ai.bp_analyzer',
        'app.ai.summoner_analyzer',
        'app.ai.team_analyzer',
        'app.ai.llm_bp_service',
        'app.view',
        'app.view.main_window',
        'app.view.start_interface',
        'app.view.bp_interface',
        'app.view.llm_interface',
        'app.components',
        'app.components.avatar_widget',
        'app.components.champion_icon_widget',
        'app.components.message_box',
        'app.components.seraphine_interface',
        'app.components.temp_system_tray_menu',
        # 其他依赖
        'aiohttp',
        'requests',
        'psutil',
        'pyperclip',
        'async_lru',
        'json',
        'asyncio',
        'threading',
        'queue',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Hextech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/resource/images/logo.ico',  # 应用图标
)
