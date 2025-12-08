@echo off
REM Kortex Agent Startup Script - Start both backend and frontend simultaneously (Windows)

echo 🧠 Starting Kortex Agent...
echo.

REM Check if in correct directory
if not exist "backend" (
    echo ❌ Error: Run this script from the kortex-agent/ directory
    exit /b 1
)
if not exist "frontend" (
    echo ❌ Error: Run this script from the kortex-agent/ directory
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ❌ Error: Virtual environment not found. Run setup.bat first.
    exit /b 1
)

REM Start backend in new window
echo 🔧 Starting Flask backend (port 5001)...
start "Kortex Backend" cmd /k "cd backend && set FLASK_APP=app.py && ..\venv\Scripts\python -m flask run --host=0.0.0.0 --port=5001"

REM Wait a bit for backend to start
timeout /t 2 /nobreak >nul

REM Start frontend in new window
echo ⚛️  Starting React frontend (port 3000)...
start "Kortex Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ Kortex Agent is running!
echo    Backend:  http://localhost:5001
echo    Frontend: http://localhost:3000
echo.
echo Close both terminal windows to stop the servers
echo.
