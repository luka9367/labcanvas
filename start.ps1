# NanaDraw - Start Script for Windows
# This script starts both the backend and frontend services

$ErrorActionPreference = "Stop"

# Colors for output
$Green = "Green"
$Blue = "Cyan"
$Yellow = "Yellow"
$Red = "Red"

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor $Blue
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor $Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor $Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor $Red
}

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Info "Starting NanaDraw services..."
Write-Info "Working directory: $ScriptDir"

# Check Python
Write-Info "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python not found. Please install Python 3.10 or higher."
    exit 1
}

# Check Node.js
Write-Info "Checking Node.js installation..."
try {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js found: $nodeVersion"
} catch {
    Write-Error "Node.js not found. Please install Node.js 18 or higher."
    exit 1
}

# Setup backend
Write-Info "Setting up backend..."
Set-Location "$ScriptDir\backend"

# Create virtual environment if not exists
if (-not (Test-Path "venv")) {
    Write-Info "Creating Python virtual environment..."
    python -m venv venv
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Info "Installing backend dependencies..."
pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install backend dependencies"
    exit 1
}
Write-Success "Backend dependencies installed"

# Create data directories
Write-Info "Creating data directories..."
$DataDirs = @("data", "data\projects", "data\gallery", "data\bioicons", "data\references", "data\elements", "data\documents")
foreach ($dir in $DataDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Start backend
Write-Info "Starting backend server on http://localhost:8001"
$BackendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir\backend
    & .\venv\Scripts\Activate.ps1
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
}

# Wait for backend to start
Write-Info "Waiting for backend to start..."
$BackendReady = $false
$Retries = 0
while (-not $BackendReady -and $Retries -lt 30) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $BackendReady = $true
            Write-Success "Backend is ready!"
        }
    } catch {
        $Retries++
        Write-Host "." -NoNewline
    }
}

if (-not $BackendReady) {
    Write-Error "Backend failed to start within 30 seconds"
    Stop-Job $BackendJob
    exit 1
}

Write-Host ""

# Setup frontend
Write-Info "Setting up frontend..."
Set-Location "$ScriptDir\frontend"

# Check node_modules
if (-not (Test-Path "node_modules")) {
    Write-Info "Installing frontend dependencies..."
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install frontend dependencies"
        Stop-Job $BackendJob
        exit 1
    }
    Write-Success "Frontend dependencies installed"
} else {
    Write-Success "Frontend dependencies already installed"
}

# Start frontend
Write-Info "Starting frontend dev server on http://localhost:3001"
$FrontendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir\frontend
    npm run dev
}

# Wait for frontend to start
Write-Info "Waiting for frontend to start..."
$FrontendReady = $false
$Retries = 0
while (-not $FrontendReady -and $Retries -lt 30) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -ErrorAction SilentlyContinue
        $FrontendReady = $true
        Write-Success "Frontend is ready!"
    } catch {
        $Retries++
        Write-Host "." -NoNewline
    }
}

if (-not $FrontendReady) {
    Write-Warning "Frontend may not be fully ready yet, but continuing..."
}

Write-Host ""
Write-Success "========================================"
Write-Success "NanaDraw is now running!"
Write-Success ""
Write-Success "Backend:  http://localhost:8001"
Write-Success "Frontend: http://localhost:3001"
Write-Success "API Docs: http://localhost:8001/docs"
Write-Success "========================================"
Write-Host ""
Write-Info "Press Ctrl+C to stop all services"

# Monitor jobs
try {
    while ($true) {
        $BackendStatus = Receive-Job $BackendJob
        $FrontendStatus = Receive-Job $FrontendJob
        
        if ($BackendStatus) {
            Write-Host "[BACKEND] $BackendStatus"
        }
        if ($FrontendStatus) {
            Write-Host "[FRONTEND] $FrontendStatus"
        }
        
        # Check if jobs are still running
        if ($BackendJob.State -eq "Failed") {
            Write-Error "Backend job failed"
            break
        }
        if ($FrontendJob.State -eq "Failed") {
            Write-Error "Frontend job failed"
            break
        }
        
        Start-Sleep -Milliseconds 100
    }
} finally {
    Write-Info "Stopping services..."
    Stop-Job $BackendJob -ErrorAction SilentlyContinue
    Stop-Job $FrontendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job $FrontendJob -ErrorAction SilentlyContinue
    Write-Success "Services stopped"
}
