@echo off
REM Batch script to run the FastAPI backend
echo Starting FastAPI backend...

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating venv...
    py -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt

REM Run the FastAPI app
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

