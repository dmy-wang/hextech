# Hextech 打包说明

## 环境要求

- Windows 10/11 (64位)
- **Python 3.8 - 3.11** (推荐 3.10 或 3.11)
  - ⚠️ Python 3.12+ 可能存在兼容性问题
  - Python 3.13 不推荐使用
- 英雄联盟客户端（运行时需要）

## 打包步骤

### 方法一：使用打包脚本（推荐）

1. **克隆项目**
```powershell
git clone https://github.com/dmy-wang/hextech.git
cd hextech
```

2. **运行打包脚本**
```powershell
# PowerShell
.\build.ps1

# 或 CMD
.\build.bat
```

3. **获取 exe 文件**
打包完成后，可执行文件位于 `dist\Hextech.exe`

### 方法二：手动打包

1. **安装依赖**
```powershell
pip install -r requirements.txt
pip install pyinstaller==5.13
```

2. **执行打包**
```powershell
pyinstaller hextech.spec --clean
```

3. **获取 exe 文件**
打包完成后，可执行文件位于 `dist\Hextech.exe`

## 常见问题

### 1. pywin32 安装失败
```powershell
pip install pywin32 --no-cache-dir
# 或指定版本
pip install pywin32==306
```

### 2. 打包后运行报错缺少模块
检查 `hextech.spec` 文件中的 `hiddenimports` 列表，添加缺失的模块。

### 3. 图标不显示
确保 `app/resource/images/logo.ico` 文件存在。

### 4. 运行时提示缺少 DLL
安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### 5. 杀毒软件报毒
PyInstaller 打包的程序可能被误报，添加白名单即可。

## 打包参数说明

在 `hextech.spec` 中可调整：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `console` | 是否显示控制台 | `False` |
| `debug` | 调试模式 | `False` |
| `upx` | UPX 压缩 | `True` |

## 开发调试

直接运行源码：
```powershell
python main.py
```

## 打包后目录结构

```
dist/
└── Hextech.exe          # 主程序
```

## 分发

打包完成后，可以直接分发 `Hextech.exe` 文件，无需其他依赖。

建议打包为 ZIP 或 7z 压缩包分发：
```powershell
# 使用 7-Zip
7z a Hextech-v1.0.0.7z dist\Hextech.exe
```
