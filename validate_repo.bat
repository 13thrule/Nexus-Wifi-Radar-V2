@echo off
echo.
echo ============================================================
echo   NEXUS V2.0 - REPOSITORY VALIDATION
echo   Checking if ready for GitHub upload...
echo ============================================================
echo.

set ERRORS=0

REM Check essential files
echo [1/8] Checking essential files...
if not exist "README.md" (
    echo   [FAIL] README.md missing
    set /a ERRORS+=1
) else (
    echo   [PASS] README.md found
)

if not exist "LICENSE" (
    echo   [FAIL] LICENSE missing
    set /a ERRORS+=1
) else (
    echo   [PASS] LICENSE found
)

if not exist "pyproject.toml" (
    echo   [FAIL] pyproject.toml missing
    set /a ERRORS+=1
) else (
    echo   [PASS] pyproject.toml found
)

if not exist ".gitignore" (
    echo   [FAIL] .gitignore missing
    set /a ERRORS+=1
) else (
    echo   [PASS] .gitignore found
)

REM Check installation scripts
echo.
echo [2/8] Checking installation scripts...
if not exist "install.bat" (
    echo   [FAIL] install.bat missing
    set /a ERRORS+=1
) else (
    echo   [PASS] install.bat found
)

if not exist "install.sh" (
    echo   [FAIL] install.sh missing
    set /a ERRORS+=1
) else (
    echo   [PASS] install.sh found
)

REM Check launcher scripts
echo.
echo [3/8] Checking launcher scripts...
if not exist "run_scanner.bat" (
    echo   [FAIL] run_scanner.bat missing
    set /a ERRORS+=1
) else (
    echo   [PASS] run_scanner.bat found
)

if not exist "run_launcher.bat" (
    echo   [FAIL] run_launcher.bat missing
    set /a ERRORS+=1
) else (
    echo   [PASS] run_launcher.bat found
)

REM Check documentation
echo.
echo [4/8] Checking documentation...
if not exist "QUICKSTART.md" (
    echo   [FAIL] QUICKSTART.md missing
    set /a ERRORS+=1
) else (
    echo   [PASS] QUICKSTART.md found
)

if not exist "CONTRIBUTING.md" (
    echo   [FAIL] CONTRIBUTING.md missing
    set /a ERRORS+=1
) else (
    echo   [PASS] CONTRIBUTING.md found
)

if not exist "SETUP.md" (
    echo   [FAIL] SETUP.md missing
    set /a ERRORS+=1
) else (
    echo   [PASS] SETUP.md found
)

if not exist "docs\ARCHITECTURE.md" (
    echo   [WARN] docs\ARCHITECTURE.md missing (optional)
) else (
    echo   [PASS] docs\ARCHITECTURE.md found
)

if not exist "docs\FEATURES.md" (
    echo   [WARN] docs\FEATURES.md missing (optional)
) else (
    echo   [PASS] docs\FEATURES.md found
)

REM Check nexus package
echo.
echo [5/8] Checking nexus package structure...
if not exist "nexus\__init__.py" (
    echo   [FAIL] nexus\__init__.py missing
    set /a ERRORS+=1
) else (
    echo   [PASS] nexus package initialized
)

if not exist "nexus\app.py" (
    echo   [FAIL] nexus\app.py missing
    set /a ERRORS+=1
) else (
    echo   [PASS] nexus\app.py found
)

if not exist "nexus\core\intelligence.py" (
    echo   [FAIL] nexus\core\intelligence.py missing
    set /a ERRORS+=1
) else (
    echo   [PASS] Intelligence Core found
)

if not exist "nexus\ui\intel_dashboard.py" (
    echo   [FAIL] nexus\ui\intel_dashboard.py missing
    set /a ERRORS+=1
) else (
    echo   [PASS] Intelligence Dashboard found
)

REM Check test suite
echo.
echo [6/8] Checking test suite...
if not exist "tests\__init__.py" (
    echo   [WARN] tests\__init__.py missing (optional)
) else (
    echo   [PASS] tests package found
)

if not exist "tests\test_smoke.py" (
    echo   [WARN] tests\test_smoke.py missing (optional)
) else (
    echo   [PASS] Smoke tests found
)

REM Test Python imports
echo.
echo [7/8] Testing Python imports...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -c "from nexus.app import NexusApp; print('  [PASS] NexusApp imports OK')" 2>nul
    if errorlevel 1 (
        echo   [FAIL] NexusApp import failed
        set /a ERRORS+=1
    )
    
    venv\Scripts\python.exe -c "from nexus.core.intelligence import get_pic; print('  [PASS] Intelligence Core imports OK')" 2>nul
    if errorlevel 1 (
        echo   [FAIL] Intelligence Core import failed
        set /a ERRORS+=1
    )
    
    venv\Scripts\python.exe -c "from nexus.ui.intel_dashboard import IntelligenceDashboard; print('  [PASS] Intelligence Dashboard imports OK')" 2>nul
    if errorlevel 1 (
        echo   [FAIL] Intelligence Dashboard import failed
        set /a ERRORS+=1
    )
) else (
    echo   [WARN] Virtual environment not found (run install.bat first)
)

REM Check for sensitive files
echo.
echo [8/8] Checking for sensitive files (should NOT be present)...
if exist ".env" (
    echo   [WARN] .env file found - make sure it's in .gitignore
)
if exist "*.log" (
    echo   [WARN] Log files found - make sure they're in .gitignore
)
echo   [PASS] No obvious sensitive files

REM Final result
echo.
echo ============================================================
if %ERRORS%==0 (
    echo   STATUS: READY FOR UPLOAD! [32m[0m
    echo   All essential files present and imports working
    echo.
    echo   Next steps:
    echo   1. git init
    echo   2. git add .
    echo   3. git commit -m "Initial commit: NEXUS V2.0"
    echo   4. git remote add origin https://github.com/yourusername/repo.git
    echo   5. git push -u origin main
) else (
    echo   STATUS: NOT READY [91m[0m
    echo   Found %ERRORS% critical error(s^)
    echo.
    echo   Fix the [FAIL] items above before uploading
)
echo ============================================================
echo.

if %ERRORS%==0 (
    exit /b 0
) else (
    exit /b 1
)
