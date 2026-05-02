# Hextech 打包脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hextech Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.8+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 检查 PyInstaller
try {
    $pyinstaller = pip show pyinstaller 2>&1
    Write-Host "[OK] PyInstaller installed" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller==5.13
}

# 安装依赖
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 清理
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 打包
Write-Host "[INFO] Building..." -ForegroundColor Yellow
pyinstaller hextech.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Build Success!" -ForegroundColor Green
    Write-Host "  Output: dist\Hextech.exe" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green

    $run = Read-Host "Run now? (y/n)"
    if ($run -eq "y") {
        Start-Process "dist\Hextech.exe"
    }
} else {
    Write-Host "[ERROR] Build failed!" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
