# DaedalusSignal Stop Script
# Stops frontend (port 3000) and backend (port 5000) processes

Write-Host "Stopping DaedalusSignal services..." -ForegroundColor Cyan
Write-Host ""

# Function to stop process on a specific port
function Stop-ProcessOnPort {
    param (
        [int]$Port,
        [string]$ServiceName
    )
    
    Write-Host "Stopping $ServiceName (port $Port)..." -ForegroundColor Yellow
    
    # Find process ID using the port
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                  Where-Object { $_.State -eq 'Listen' } | 
                  Select-Object -First 1
    
    if ($connection) {
        $processId = $connection.OwningProcess
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        
        if ($process) {
            Stop-Process -Id $processId -Force
            Write-Host "  Stopped $($process.ProcessName) (PID: $processId)" -ForegroundColor Green
        }
    } else {
        Write-Host "  No process found on port $Port" -ForegroundColor Gray
    }
}

# Stop Backend (Flask on port 5000)
Stop-ProcessOnPort -Port 5000 -ServiceName "Backend (Flask)"

# Stop Frontend (Next.js on port 3000)
Stop-ProcessOnPort -Port 3000 -ServiceName "Frontend (Next.js)"

Write-Host ""
Write-Host "DaedalusSignal services stopped!" -ForegroundColor Green
