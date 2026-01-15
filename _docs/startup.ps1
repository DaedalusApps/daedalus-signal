# DaedalusSignal Startup Script
# Starts the frontend development server

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting DaedalusSignal..." -ForegroundColor Cyan
Write-Host ""

# Start Frontend
Write-Host "Starting Frontend (Next.js on port 3000)..." -ForegroundColor Yellow
$frontendPath = Join-Path $projectRoot "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

Write-Host ""
Write-Host "Frontend starting in separate window!" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  API:          https://signal.daedalusapps.com/api (production)" -ForegroundColor White
Write-Host ""
Write-Host "To seed the database, run: php api/seed.php" -ForegroundColor Gray
Write-Host "Press Ctrl+C in the window to stop the service." -ForegroundColor Gray
