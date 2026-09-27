# FinPilot AI - Development Server Startup Script (Windows / PowerShell)
# Usage: .\start-dev.ps1

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   FinPilot AI - Starting Dev Environment " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$RootDir = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"

$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"

# 1. Ensure Backend Virtual Environment exists
if (-not (Test-Path $PythonExe)) {
    Write-Host "[Backend] Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv (Join-Path $BackendDir ".venv")
    & $PythonExe -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

# 2. Check Backend .env
if (-not (Test-Path (Join-Path $BackendDir ".env"))) {
    Write-Host "[Backend] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item (Join-Path $BackendDir ".env.example") (Join-Path $BackendDir ".env")
}

# 3. Check Frontend node_modules
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "[Frontend] Installing npm packages..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    npm install
    Pop-Location
}

# 4. Check Frontend .env
if (-not (Test-Path (Join-Path $FrontendDir ".env"))) {
    Write-Host "[Frontend] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item (Join-Path $FrontendDir ".env.example") (Join-Path $FrontendDir ".env")
}

# 5. Run Alembic Database Migrations
Write-Host "[Database] Running Alembic migrations (upgrade head)..." -ForegroundColor Cyan
Push-Location $BackendDir
& $PythonExe -m alembic upgrade head
Pop-Location

# 6. Clean any stale processes on ports 8000 / 5173
& (Join-Path $RootDir "stop-dev.ps1") -Quiet

Write-Host "`n[1/2] Starting FastAPI backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
$backendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $BackendDir `
    -NoNewWindow `
    -PassThru

Write-Host "[2/2] Starting React + Vite frontend on http://localhost:5173 ..." -ForegroundColor Green
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) { $npmCmd = "npm" }

$frontendProc = Start-Process -FilePath $npmCmd `
    -ArgumentList "run", "dev", "--", "--host", "localhost", "--port", "5173" `
    -WorkingDirectory $FrontendDir `
    -NoNewWindow `
    -PassThru

# Wait briefly for services to initialize
Start-Sleep -Seconds 2

# 6. Open in Google Chrome
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    (Get-Command chrome.exe -ErrorAction SilentlyContinue).Source
)
$chromeExe = $chromePaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if ($chromeExe) {
    Write-Host "[Browser] Launching Google Chrome at http://localhost:5173/ ..." -ForegroundColor Cyan
    Start-Process -FilePath $chromeExe -ArgumentList "http://localhost:5173/"
} else {
    Write-Host "[Browser] Opening default browser at http://localhost:5173/ ..." -ForegroundColor Cyan
    Start-Process "http://localhost:5173/"
}

Write-Host "`n-----------------------------------------" -ForegroundColor Cyan
Write-Host "Services running:" -ForegroundColor Green
Write-Host " - Backend API:  http://127.0.0.1:8000 (Docs: /docs, Health: /health)" -ForegroundColor White
Write-Host " - Frontend UI:  http://localhost:5173" -ForegroundColor White
Write-Host "-----------------------------------------" -ForegroundColor Cyan
Write-Host "Press Ctrl+C or run .\stop-dev.ps1 in another terminal to stop services.`n" -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($backendProc.HasExited -or $frontendProc.HasExited) {
            Write-Host "`nOne of the dev processes stopped unexpectedly." -ForegroundColor Yellow
            break
        }
    }
}
finally {
    Write-Host "`nStopping FinPilot AI dev processes..." -ForegroundColor Red
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProc -and -not $frontendProc.HasExited) {
        Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue
    }
    & (Join-Path $RootDir "stop-dev.ps1") -Quiet
    Write-Host "All development services stopped." -ForegroundColor Green
}
