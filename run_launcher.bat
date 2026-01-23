@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM  NEXUS WiFi Radar - Launcher
REM ═══════════════════════════════════════════════════════════════════════════
REM  Starts the NEXUS Launcher with animated boot sequence
REM  
REM  From the launcher you can:
REM  - Launch the main Radar GUI
REM  - Start Intelligence Dashboard
REM  - Run CLI scans
REM  - Start web dashboard server
REM  - Access settings and logs
REM ═══════════════════════════════════════════════════════════════════════════

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python -m nexus launcher
) else (
    echo [ERROR] Virtual environment not found.
    echo Please run: python -m venv venv
    echo Then: pip install -e .
    pause
)
