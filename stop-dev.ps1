param (
    [switch]$Quiet
)

if (-not $Quiet) {
    Write-Host "Stopping FinPilot AI dev processes on ports 8000 and 5173..." -ForegroundColor Yellow
}

$ports = @(8000, 5173)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $procId = $conn.OwningProcess
            if ($procId -gt 0) {
                if (-not $Quiet) {
                    Write-Host "Stopping process tree for PID $procId listening on port $port..." -ForegroundColor Yellow
                }
                # Use taskkill /F /T to forcefully terminate the process and all child processes (including uvicorn workers)
                taskkill /F /T /PID $procId 2>$null | Out-Null
            }
        }
    }
}

# Catch any remaining multiprocessing spawn workers or orphan dev servers
Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'node.exe'" -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.CommandLine -like "*uvicorn*app.main:app*" -or $_.CommandLine -like "*spawn_main*" -or $_.CommandLine -like "*vite*") {
        if (-not $Quiet) {
            Write-Host "Stopping orphan dev process PID $($_.ProcessId)..." -ForegroundColor Yellow
        }
        taskkill /F /T /PID $_.ProcessId 2>$null | Out-Null
    }
}

if (-not $Quiet) {
    Write-Host "FinPilot services stopped." -ForegroundColor Green
}
