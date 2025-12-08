@echo off
REM Setup script for Kortex Agent (Windows)

echo 🧠 Setting up Kortex Agent...
echo.

REM Check if Python 3 is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 3 is not installed. Please install Python 3 first.
    echo.
    echo Download from: https://www.python.org/downloads/
    exit /b 1
)

echo ✓ Python 3 found

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed. Please install Node.js and npm first.
    echo.
    echo Download from: https://nodejs.org/
    exit /b 1
)

echo ✓ npm found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Install Python dependencies in virtual environment
echo 📦 Installing Python dependencies...
venv\Scripts\pip install -r requirements.txt

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
cd frontend && npm install && cd ..

echo.
echo ✓ Setup complete!
echo.
echo ⚠️  IMPORTANT: Set your Gemini API key before running:
echo    set GEMINI_API_KEY=your-api-key-here
echo.
echo Get your API key from: https://aistudio.google.com/app/apikey
echo.
echo To run the chatbot:
echo    start.bat
echo.
