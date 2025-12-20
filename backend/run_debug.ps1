# PowerShell script to run the FastAPI backend with DEBUG logging
Write-Host "Starting FastAPI backend in DEBUG mode..." -ForegroundColor Cyan

# Check if venv exists
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found. Creating venv..." -ForegroundColor Yellow
    py -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}

# Get the Python executable from venv
$pythonExe = "venv\Scripts\python.exe"
$pipExe = "venv\Scripts\pip.exe"

# Install/update dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
& $pipExe install -q -r requirements.txt

# Set DEBUG log level environment variable
$env:LOG_LEVEL = "DEBUG"

# Run the FastAPI app with debug logging
Write-Host "Starting server on http://localhost:8000 (DEBUG mode)" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
& $pythonExe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

