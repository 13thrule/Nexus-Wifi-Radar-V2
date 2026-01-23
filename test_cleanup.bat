@echo off
REM Test NEXUS process cleanup after exit

echo ========================================
echo   NEXUS Process Cleanup Test
echo ========================================
echo.

echo [1/4] Checking for existing Python processes...
tasklist | findstr /i python.exe
echo.

echo [2/4] Launching NEXUS (close it manually after 10 seconds)...
timeout /t 2 /nobreak >nul
start "NEXUS Test" .\venv\Scripts\python.exe -m nexus gui
echo       NEXUS launched. Please close the window manually.
echo.

echo [3/4] Waiting 15 seconds for you to close NEXUS...
timeout /t 15 /nobreak
echo.

echo [4/4] Checking for lingering Python processes...
echo.
echo Python processes still running:
tasklist | findstr /i python.exe
echo.

echo Counting Python processes:
for /f %%A in ('tasklist ^| findstr /i python.exe ^| find /c /v ""') do set COUNT=%%A
if "%COUNT%"=="0" (
    echo.
    echo ========================================
    echo   SUCCESS: No lingering processes!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   WARNING: %COUNT% Python process(es) still running
    echo   This might include other Python programs
    echo ========================================
)
echo.

echo If you see lingering NEXUS processes, press Y to kill them.
set /p KILL="Kill Python processes? (Y/N): "
if /i "%KILL%"=="Y" (
    taskkill /F /IM python.exe /T
    echo Processes killed.
)

echo.
pause
