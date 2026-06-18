# NanaDraw Installation Script for Windows PowerShell

$ErrorActionPreference = "Stop"

# Colors
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

Write-Host "========================================" -ForegroundColor $Cyan
Write-Host "     NanaDraw 安装脚本" -ForegroundColor $Cyan
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

# Check Python
Write-Host "检查 Python 环境..." -ForegroundColor $Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor $Green
} catch {
    Write-Host "✗ 未找到 Python，请安装 Python 3.9+" -ForegroundColor $Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor $Yellow
    exit 1
}

# Check Node.js
Write-Host "检查 Node.js 环境..." -ForegroundColor $Cyan
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor $Green
} catch {
    Write-Host "✗ 未找到 Node.js，请安装 Node.js 18+" -ForegroundColor $Red
    Write-Host "下载地址: https://nodejs.org/" -ForegroundColor $Yellow
    exit 1
}

Write-Host ""

# Create directories
Write-Host "创建项目目录..." -ForegroundColor $Cyan
$dirs = @(
    "backend\data\projects",
    "backend\static\gallery",
    "backend\static\bioicons\svgs"
)
foreach ($dir in $dirs) {
    $path = Join-Path $RootDir $dir
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}
Write-Host "✓ 目录创建完成" -ForegroundColor $Green
Write-Host ""

# Setup backend
Write-Host "安装后端依赖..." -ForegroundColor $Cyan
Set-Location $RootDir\backend

# Create virtual environment
Write-Host "创建 Python 虚拟环境..." -ForegroundColor $Yellow
python -m venv .venv

# Activate and install
$venvPip = "$RootDir\backend\.venv\Scripts\pip.exe"
Write-Host "安装依赖包..." -ForegroundColor $Yellow
& $venvPip install -r requirements.txt

Write-Host "✓ 后端安装完成" -ForegroundColor $Green
Write-Host ""

# Setup frontend
Write-Host "安装前端依赖..." -ForegroundColor $Cyan
Set-Location $RootDir\frontend

Write-Host "这可能需要几分钟..." -ForegroundColor $Yellow
npm install

Write-Host "✓ 前端安装完成" -ForegroundColor $Green
Write-Host ""

# Create startup shortcuts
Write-Host "创建启动快捷方式..." -ForegroundColor $Cyan

# Create a simple batch file for easy startup
$batchContent = @"
@echo off
echo Starting NanaDraw...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1"
pause
"@

$batchContent | Out-File -FilePath "$RootDir\start.bat" -Encoding ASCII

Write-Host "✓ 安装完成！" -ForegroundColor $Green
Write-Host ""
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host "  安装成功！" -ForegroundColor $Green
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host ""
Write-Host "启动方式:" -ForegroundColor $Cyan
Write-Host "  1. 双击 start.bat" -ForegroundColor $Yellow
Write-Host "  2. 或运行: .\scripts\start.ps1" -ForegroundColor $Yellow
Write-Host ""
Write-Host "首次使用请配置 API Key:" -ForegroundColor $Cyan
Write-Host "  访问 http://localhost:3001/settings" -ForegroundColor $Yellow
Write-Host "  填入您的智谱 AI API Key" -ForegroundColor $Yellow
Write-Host ""
