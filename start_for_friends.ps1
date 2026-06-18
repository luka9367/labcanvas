# LabCanvas one-click sharing launcher for friends
# Requires: cpolar installed and logged in (free version works)
# Usage: run this script, it will open backend/gateway windows and start cpolar automatically

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LabCanvas Sharing Launcher" -ForegroundColor Cyan
Write-Host "  Friends only need one cpolar link" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

function Get-AvailablePort($startPort, $endPort) {
    for ($port = $startPort; $port -le $endPort; $port++) {
        $inUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 }
        if (-not $inUse) {
            return $port
        }
    }
    throw "No available port between $startPort and $endPort"
}

function Clear-Port($port) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 }
    foreach ($conn in $conns) {
        $procId = $conn.OwningProcess
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Write-Host "Killing process on port $port : PID=$procId ($($proc.ProcessName))" -ForegroundColor Yellow
            Stop-Process -Id $procId -Force
        } catch {
            Write-Host "Failed to kill PID $procId : $_" -ForegroundColor Red
        }
    }
}

# Step 0: choose ports
Write-Host "`n[0/5] Choosing available ports..." -ForegroundColor Green
$backendPort = Get-AvailablePort 8080 8090
$gatewayPort = Get-AvailablePort 5000 5010
Write-Host "  Backend port: $backendPort" -ForegroundColor Cyan
Write-Host "  Gateway port: $gatewayPort" -ForegroundColor Cyan

# Step 1: start backend in a separate window
Write-Host "`n[1/5] Starting backend in separate window (0.0.0.0:$backendPort)..." -ForegroundColor Green
$backendPath = Resolve-Path "./backend"
$pythonPath = Join-Path $backendPath ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = "python"
}

$backendCmd = "cd /d `"$($backendPath.Path)`" & `"$pythonPath`" -m uvicorn app.main:app --host 0.0.0.0 --port $backendPort"
$backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k title LabCanvas Backend & $backendCmd" -PassThru

# Step 2: wait for backend ready
Write-Host "`n[2/5] Waiting for backend ready..." -ForegroundColor Green
$backendReady = $false
$maxWait = 60
$elapsed = 0
while ($elapsed -lt $maxWait -and -not $backendReady) {
    Start-Sleep -Seconds 1
    $elapsed++
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$backendPort/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "  Backend ready!" -ForegroundColor Green
        }
    } catch { }
}

if (-not $backendReady) {
    Write-Host "  Backend failed to start" -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Step 3: build frontend
Write-Host "`n[3/5] Building frontend..." -ForegroundColor Green
Set-Location (Resolve-Path "./frontend").Path
& npm run build
Set-Location (Resolve-Path "..").Path

# Step 4: generate gateway script and start in separate window
Write-Host "`n[4/5] Starting gateway in separate window (0.0.0.0:$gatewayPort)..." -ForegroundColor Green

$gatewayScript = @"
import http.server
import socketserver
import urllib.request
import os

API_BASE = 'http://localhost:$backendPort'
WEB_DIR = os.path.abspath('./frontend/dist')
PORT = $gatewayPort

class Gateway(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'):
            self._proxy()
        else:
            self._serve_static()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self._proxy()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        if self.path.startswith('/api/'):
            self._proxy()
        else:
            self._serve_static()

    def _proxy(self):
        url = API_BASE + self.path
        content_length = self.headers.get('Content-Length')
        body = None
        if content_length:
            body = self.rfile.read(int(content_length))

        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    'Content-Type': self.headers.get('Content-Type', ''),
                    'Authorization': self.headers.get('Authorization', ''),
                },
                method=self.command,
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() in ('transfer-encoding', 'content-encoding'):
                        continue
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())

    def _serve_static(self):
        path = self.path
        if path == '/':
            path = '/index.html'
        file_path = os.path.join(WEB_DIR, path.lstrip('/'))
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(WEB_DIR, 'index.html')

        if os.path.exists(file_path):
            self.send_response(200)
            if file_path.endswith('.html'):
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            elif file_path.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript')
            elif file_path.endswith('.css'):
                self.send_header('Content-Type', 'text/css')
            elif file_path.endswith('.json'):
                self.send_header('Content-Type', 'application/json')
            else:
                self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

os.chdir(WEB_DIR)
with socketserver.ThreadingTCPServer(('0.0.0.0', PORT), Gateway) as httpd:
    print(f'Gateway running at http://0.0.0.0:{PORT}')
    print('Multi-threading enabled, supports multiple concurrent users')
    httpd.serve_forever()
"@

$gatewayPath = Join-Path $env:TEMP "labcanvas_gateway.py"
$gatewayScript | Out-File -FilePath $gatewayPath -Encoding utf8

$gatewayCmd = "cd /d `"$((Resolve-Path '.').Path)`" & python `"$gatewayPath`""
$gatewayProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/k title LabCanvas Gateway & $gatewayCmd" -PassThru

# Step 5: wait for gateway ready
Write-Host "`n[5/5] Waiting for gateway ready..." -ForegroundColor Green
$gatewayReady = $false
$elapsed = 0
while ($elapsed -lt $maxWait -and -not $gatewayReady) {
    Start-Sleep -Seconds 1
    $elapsed++
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$gatewayPort" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $gatewayReady = $true
            Write-Host "  Gateway ready!" -ForegroundColor Green
        }
    } catch { }
}

if (-not $gatewayReady) {
    Write-Host "  Gateway failed to start" -ForegroundColor Red
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $gatewayProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Step 6: start cpolar automatically
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Starting cpolar tunnel..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

$cpolarPath = "D:\cpolar\cpolar.exe"
if (-not (Test-Path $cpolarPath)) {
    $cpolarPath = "cpolar"
}

& $cpolarPath http $gatewayPort

# When cpolar exits, clean up
try {
    Write-Host "`nCpolar stopped. Cleaning up..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $gatewayProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
} catch {}
