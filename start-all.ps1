# Start backend and frontend in separate PowerShell windows
# Usage: .\start-all.ps1

# Start backend (Flask) - with venv activation
$backendCmd = "cd '$PWD\backend'; & '$PWD\.venv\Scripts\Activate.ps1'; python run.py"
$backend = Start-Process powershell -ArgumentList '-NoExit', '-Command', $backendCmd -PassThru

# Start frontend (React)
$frontend = Start-Process powershell -ArgumentList '-NoExit', '-Command', 'npm start' -WorkingDirectory "$PWD\frontend" -PassThru

Write-Output "Started backend (PID: $($backend.Id)) and frontend (PID: $($frontend.Id))"