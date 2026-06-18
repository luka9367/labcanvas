# NanaDraw Startup Script for Windows PowerShell

$ErrorActionPreference = "Stop"

# Colors
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

Write-Host "========================================" -ForegroundColor $Cyan
Write-Host "       NanaDraw 启动脚本" -ForegroundColor $Cyan
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

# Function to check if a port is in use
function Test-PortInUse {
    param($Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

# Function to kill process on port
function Stop-ProcessOnPort {
    param($Port)
    try {
        $process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                   Select-Object -First 1 | 
                   ForEach-Object { Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue }
        if ($process) {
            Write-Host "正在停止占用端口 $Port 的进程..." -ForegroundColor $Yellow
            Stop-Process -Id $process.Id -Force
            Start-Sleep -Seconds 1
        }
    } catch {
        # Ignore errors
    }
}

# Check Python
Write-Host "检查 Python 环境..." -ForegroundColor $Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor $Green
} catch {
    Write-Host "✗ 未找到 Python，请安装 Python 3.9+" -ForegroundColor $Red
    exit 1
}

# Check Node.js
Write-Host "检查 Node.js 环境..." -ForegroundColor $Cyan
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor $Green
} catch {
    Write-Host "✗ 未找到 Node.js，请安装 Node.js 18+" -ForegroundColor $Red
    exit 1
}

Write-Host ""

# Check ports
if (Test-PortInUse -Port 8001) {
    Write-Host "端口 8001 被占用，尝试释放..." -ForegroundColor $Yellow
    Stop-ProcessOnPort -Port 8001
}

if (Test-PortInUse -Port 3001) {
    Write-Host "端口 3001 被占用，尝试释放..." -ForegroundColor $Yellow
    Stop-ProcessOnPort -Port 3001
}

# Setup backend
Write-Host "设置后端环境..." -ForegroundColor $Cyan
Set-Location $RootDir\backend

# Create virtual environment if not exists
if (-not (Test-Path ".venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor $Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "激活虚拟环境..." -ForegroundColor $Yellow
$venvPython = "$RootDir\backend\.venv\Scripts\python.exe"
$venvPip = "$RootDir\backend\.venv\Scripts\pip.exe"

# Install dependencies
Write-Host "安装后端依赖..." -ForegroundColor $Yellow
& $venvPip install -q -r requirements.txt

# Create necessary directories
$dirs = @("data", "data\projects", "static", "static\gallery", "static\bioicons", "static\bioicons\svgs")
foreach ($dir in $dirs) {
    $path = Join-Path $RootDir\backend $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Force -Path $path | Out-Null
    }
}

Write-Host "✓ 后端环境准备完成" -ForegroundColor $Green
Write-Host ""

# Setup frontend
Write-Host "设置前端环境..." -ForegroundColor $Cyan
Set-Location $RootDir\frontend

# Check node_modules
if (-not (Test-Path "node_modules")) {
    Write-Host "安装前端依赖..." -ForegroundColor $Yellow
    npm install
}

Write-Host "✓ 前端环境准备完成" -ForegroundColor $Green
Write-Host ""

# Start backend
Write-Host "启动后端服务..." -ForegroundColor $Cyan
$backendJob = Start-Job -ScriptBlock {
    param($RootDir)
    Set-Location $RootDir\backend
    $env:PYTHONPATH = "$RootDir\backend"
    & "$RootDir\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
} -ArgumentList $RootDir

# Wait for backend to start
Write-Host "等待后端启动..." -ForegroundColor $Yellow
Start-Sleep -Seconds 3

# Check if backend is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/models" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ 后端服务已启动 (http://localhost:8001)" -ForegroundColor $Green
    }
} catch {
    Write-Host "⚠ 后端可能还在启动中，请稍候..." -ForegroundColor $Yellow
}

Write-Host ""

# Start frontend
Write-Host "启动前端服务..." -ForegroundColor $Cyan
Set-Location $RootDir\frontend

Write-Host ""
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host "  NanaDraw 正在运行！" -ForegroundColor $Green
Write-Host "========================================" -ForegroundColor $Cyan
Write-Host ""
Write-Host "  前端地址: http://localhost:3001" -ForegroundColor $Cyan
Write-Host "  后端地址: http://localhost:8001" -ForegroundColor $Cyan
Write-Host "  API 文档: http://localhost:8001/docs" -ForegroundColor $Cyan
Write-Host ""
Write-Host "  按 Ctrl+C 停止服务" -ForegroundColor $Yellow
Write-Host ""

# Start frontend (this will block)
try {
    npm run dev
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor $Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Write-Host "✓ 服务已停止" -ForegroundColor $Green
}
