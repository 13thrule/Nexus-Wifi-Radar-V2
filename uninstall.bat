@echo off
REM NEXUS WiFi Radar - Windows Uninstallation Script

title NEXUS Uninstaller
color 0C

echo ==========================================
echo   NEXUS WiFi Radar - Uninstaller
echo ==========================================
echo.
echo This will remove:
echo   - Virtual environment (venv/)
echo   - Python cache files (__pycache__)
echo   - Build artifacts (dist/, *.egg-info)
echo.
echo Your source code and configuration will be preserved.
echo.
set /p CONFIRM="Are you sure you want to uninstall? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo.
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting uninstallation...
echo.

REM Stop any running NEXUS processes
echo [1/5] Stopping NEXUS processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *NEXUS*" >nul 2>&1
timeout /t 2 /nobreak >nul
echo       Done.

REM Remove virtual environment
echo [2/5] Removing virtual environment...
if exist venv (
    rmdir /s /q venv
    echo       Removed venv/
) else (
    echo       Virtual environment not found (already removed)
)

REM Remove Python cache
echo [3/5] Removing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc *.pyo) do @if exist "%%f" del /q "%%f"
echo       Done.

REM Remove build artifacts
echo [4/5] Removing build artifacts...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.egg-info rmdir /s /q *.egg-info
for /d %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
echo       Done.

REM Remove .pyc files in nexus
echo [5/5] Cleaning nexus package...
if exist nexus (
    for /r nexus %%f in (*.pyc) do @if exist "%%f" del /q "%%f"
    for /d /r nexus %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
)
echo       Done.

echo.
echo ==========================================
echo   Uninstallation Complete!
echo ==========================================
echo.
echo NEXUS has been uninstalled from your system.
echo.
echo Preserved files:
echo   - Source code (nexus/)
echo   - Documentation (docs/, *.md)
echo   - Configuration files
echo   - Screenshots (assets/)
echo.
echo To reinstall, run: install.bat
echo.
pause
