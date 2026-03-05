@echo off
REM Quick Setup Script for Clara AI Automation Pipeline
REM Windows Batch File

echo ==========================================
echo Clara AI Automation Pipeline Setup
echo ==========================================
echo.

REM Check Python installation
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/6] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Create .env file if it doesn't exist
echo [4/6] Setting up environment variables...
if exist .env (
    echo .env file already exists, skipping...
) else (
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and add your OpenRouter API key
    echo Get your free API key from: https://openrouter.ai/keys
    echo.
    echo Opening .env file...
    timeout /t 2 >nul
    notepad .env
)
echo.

REM Create necessary directories
echo [5/6] Creating directories...
if not exist outputs\accounts mkdir outputs\accounts
if not exist logs mkdir logs
if not exist database mkdir database
echo Directories created
echo.

REM Test installation
echo [6/6] Testing installation...
python -c "from scripts.utils import llm_client; print('LLM client loaded successfully')"
if errorlevel 1 (
    echo WARNING: Could not load LLM client. Check your .env configuration.
) else (
    echo Installation test passed
)
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Ensure your .env file has a valid API key
echo 2. Run: python scripts/batch_process.py --mode demo
echo.
echo For full instructions, see QUICKSTART.md
echo.
pause
