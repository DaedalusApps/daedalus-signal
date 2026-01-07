# DaedalusSignal Startup Script
# Seeds the database and starts both frontend and backend in separate terminal windows

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting DaedalusSignal..." -ForegroundColor Cyan
Write-Host ""

# Seed the database first
Write-Host "Initializing database and seeding data..." -ForegroundColor Yellow
$backendPath = Join-Path $projectRoot "backend"
Push-Location $backendPath
& .\venv\Scripts\Activate.ps1
python seed.py
Pop-Location
Write-Host ""

# Start Backend
Write-Host "Starting Backend (Flask API on port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; python run.py"

# Give backend a moment to start
Start-Sleep -Seconds 2

# Start Frontend
Write-Host "Starting Frontend (Next.js on port 3000)..." -ForegroundColor Yellow
$frontendPath = Join-Path $projectRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

Write-Host ""
Write-Host "Both services starting in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  http://localhost:5000" -ForegroundColor White
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Admin login uses credentials from backend/.env" -ForegroundColor Gray
Write-Host "Press Ctrl+C in each window to stop the services." -ForegroundColor Gray
