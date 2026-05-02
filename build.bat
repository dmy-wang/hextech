@echo off
chcp 65001 >nul
echo ========================================
echo   Hextech 打包脚本
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller==5.13
)

:: 安装依赖
echo [信息] 检查依赖...
pip install -r requirements.txt

:: 清理旧的打包文件
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: 打包
echo [信息] 开始打包...
pyinstaller hextech.spec --clean

if errorlevel 1 (
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo   输出目录: dist\Hextech.exe
echo ========================================
echo.

:: 询问是否运行
set /p run="是否立即运行？(y/n): "
if /i "%run%"=="y" (
    start "" "dist\Hextech.exe"
)

pause
