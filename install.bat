@echo off
REM NEXUS WiFi Radar - Windows Installation Script

echo ==================================
echo NEXUS WiFi Radar Installation
echo ==================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo X Python not found. Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Found Python %PYTHON_VERSION%

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Warning: Virtual environment already exists. Skipping.
) else (
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo X Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install NEXUS
echo.
echo Installing NEXUS WiFi Radar...
pip install -e .
if %ERRORLEVEL% NEQ 0 (
    echo X Installation failed
    pause
    exit /b 1
)
echo [OK] NEXUS installed

REM Optional: Run tests
echo.
set /p RUN_TESTS="Run test suite? (y/N): "
if /i "%RUN_TESTS%"=="y" (
    pip install pytest
    pytest -v
)

REM Success
echo.
echo ==================================
echo [OK] Installation Complete!
echo ==================================
echo.
echo To launch NEXUS:
echo   1. Double-click run_launcher.bat
echo   2. Or run: venv\Scripts\python.exe -m nexus gui
echo.
echo For CLI mode:
echo   venv\Scripts\python.exe -m nexus scan
echo.
echo Documentation: README.md
echo Issues: https://github.com/your-repo/nexus-wifi-radar/issues
echo.
pause
