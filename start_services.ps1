# NanaDraw 服务启动脚本
# 功能：自动清理端口冲突、启动前后端服务、提供访问链接

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NanaDraw 服务启动器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. 清理端口占用
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

Write-Host "`n[1/4] Cleaning port conflicts..." -ForegroundColor Green
Clear-Port 8000
Clear-Port 3001
Start-Sleep -Seconds 2

# 2. 启动后端
Write-Host "`n[2/4] Starting backend (port 8000)..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    param($cwd)
    Set-Location $cwd
    & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
} -ArgumentList (Resolve-Path "./backend").Path

# 3. 启动前端
Write-Host "[3/4] Starting frontend (port 3001)..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    param($cwd)
    Set-Location $cwd
    & npm run dev
} -ArgumentList (Resolve-Path "./frontend").Path

# 4. 等待服务就绪
Write-Host "`n[4/4] Waiting for services to be ready..." -ForegroundColor Green
$backendReady = $false
$frontendReady = $false
$maxWait = 60
$elapsed = 0

while ($elapsed -lt $maxWait -and (-not $backendReady -or -not $frontendReady)) {
    Start-Sleep -Seconds 1
    $elapsed++

    if (-not $backendReady) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                $backendReady = $true
                Write-Host "  Backend ready!" -ForegroundColor Green
            }
        } catch { }
    }

    if (-not $frontendReady) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) {
                $frontendReady = $true
                Write-Host "  Frontend ready!" -ForegroundColor Green
            }
        } catch { }
    }
}

if ($backendReady -and $frontendReady) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "  All services are running!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3001/" -ForegroundColor Cyan
    Write-Host "  Backend:  http://localhost:8000/" -ForegroundColor Cyan
    Write-Host "  Health:   http://localhost:8000/health" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "`nPress Ctrl+C to stop all services." -ForegroundColor Yellow

    # Keep alive and monitor
    try {
        while ($true) {
            Start-Sleep -Seconds 5
            # Check backend health
            try {
                $null = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            } catch {
                Write-Host "`n[WARNING] Backend health check failed! Attempting restart..." -ForegroundColor Red
                Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
                Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
                $backendJob = Start-Job -ScriptBlock {
                    param($cwd)
                    Set-Location $cwd
                    & python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
                } -ArgumentList (Resolve-Path "./backend").Path
            }
        }
    } finally {
        Write-Host "`nStopping services..." -ForegroundColor Yellow
        Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
        Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
        Write-Host "Done." -ForegroundColor Green
    }
} else {
    Write-Host "`nServices failed to start within ${maxWait}s." -ForegroundColor Red
    Receive-Job -Job $backendJob
    Receive-Job -Job $frontendJob
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -ErrorAction SilentlyContinue
}
