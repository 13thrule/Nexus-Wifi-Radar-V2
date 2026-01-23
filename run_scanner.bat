@echo off
REM WiFi Signal Strength Scanner - Auto Room Footprint Detection
title WiFi Signal Scanner
color 0A

echo.
echo 
echo      WiFi Signal Scanner - Room Footprint Detection           
echo           Preparing environment...                            
echo 
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found!
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

REM Check and install/activate virtual environment
echo  Checking dependencies...
cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo  Virtual environment activated
) else (
    echo  Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -e . --quiet
)

echo  All dependencies ready
echo.
echo Starting Nexus WiFi Radar GUI...
echo.

REM Launch the GUI app
python -m nexus gui

echo.
echo  Scanner closed. Check folder for exported data and images.
pause
