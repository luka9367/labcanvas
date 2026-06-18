# LabCanvas 本地后端启动脚本（配合内网穿透使用）
# 功能：只启动后端服务，绑定 0.0.0.0，让外部通过穿透域名访问

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LabCanvas 本地后端启动器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 清理端口占用
function Clear-Port($port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 }
    foreach ($conn in $conns) {
        $pid = $conn.OwningProcess
        try {
            $proc = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "Killing process on port $port : PID=$pid ($($proc.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $pid -Force
        } catch {
            Write-Host "Failed to kill PID $pid : $_" -ForegroundColor Red
        }
    }
}

Write-Host "`n[1/2] Cleaning port 8000..." -ForegroundColor Green
Clear-Port 8000
Start-Sleep -Seconds 2

# 启动后端
Write-Host "`n[2/2] Starting backend on 0.0.0.0:8000..." -ForegroundColor Green
Write-Host "请配合 cpolar 使用：cpolar http 8000" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green

Set-Location (Resolve-Path "./backend").Path
& python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
