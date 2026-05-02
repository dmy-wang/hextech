# Hextech 打包脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hextech Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python 版本
$pythonVersion = (python --version 2>&1).ToString()
Write-Host "[OK] $pythonVersion" -ForegroundColor Green

# 检查 Python 版本兼容性
if ($pythonVersion -match "3\.(\d+)") {
    $minorVersion = [int]$matches[1]
    if ($minorVersion -gt 11) {
        Write-Host "[WARN] Python 3.$minorVersion detected. Recommended: Python 3.10 or 3.11" -ForegroundColor Yellow
        Write-Host "       Some packages may have compatibility issues." -ForegroundColor Yellow
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit 1
        }
    }
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

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 清理
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

# 打包 (使用 python -m PyInstaller 避免 PATH 问题)
Write-Host "[INFO] Building..." -ForegroundColor Yellow
python -m PyInstaller hextech.spec --clean

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
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
}

Read-Host "Press Enter to exit"
