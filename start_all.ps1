# Start NanaDraw Backend
$env:PYTHONPATH = "c:\Users\20411\Desktop\11\backend"
$backendJob = Start-Job -ScriptBlock {
    Set-Location "c:\Users\20411\Desktop\11\backend"
    & .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
}

# Wait for backend to start
Write-Host "Starting backend..." -ForegroundColor Green
Start-Sleep 3

# Start Frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "c:\Users\20411\Desktop\11\frontend"
    & npm run dev
}

Write-Host "Starting frontend..." -ForegroundColor Green
Start-Sleep 3

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "NanaDraw is starting..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8001" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3001" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host "======================================`n" -ForegroundColor Cyan

# Show logs
while ($true) {
    $backendOutput = Receive-Job -Job $backendJob
    $frontendOutput = Receive-Job -Job $frontendJob
    
    if ($backendOutput) {
        Write-Host "[BACKEND] $backendOutput" -ForegroundColor Gray
    }
    if ($frontendOutput) {
        Write-Host "[FRONTEND] $frontendOutput" -ForegroundColor DarkGray
    }
    
    Start-Sleep 1
}
