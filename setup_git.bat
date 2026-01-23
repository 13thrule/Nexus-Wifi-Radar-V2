@echo off
REM ============================================================
REM  NEXUS V2.0 - Git Repository Setup Helper
REM  This script helps you create a new GitHub repository
REM ============================================================
echo.
echo ============================================================
echo   NEXUS V2.0 - GitHub Repository Setup
echo ============================================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo [1] Git is installed
echo.

REM Check if already a git repository
if exist ".git" (
    echo [WARN] This directory is already a git repository!
    echo.
    choice /C YN /M "Do you want to continue anyway"
    if errorlevel 2 exit /b 0
    echo.
)

REM Initialize repository
echo [2] Initializing git repository...
git init
if errorlevel 1 (
    echo [ERROR] Failed to initialize repository
    pause
    exit /b 1
)
echo    Done!
echo.

REM Add all files
echo [3] Adding all files to git...
git add .
if errorlevel 1 (
    echo [ERROR] Failed to add files
    pause
    exit /b 1
)
echo    Done!
echo.

REM Create initial commit
echo [4] Creating initial commit...
git commit -m "Initial commit: NEXUS WiFi Radar V2.0 - Intelligence Edition"
if errorlevel 1 (
    echo [ERROR] Failed to create commit
    pause
    exit /b 1
)
echo    Done!
echo.

echo ============================================================
echo   Local Git Repository Created Successfully!
echo ============================================================
echo.
echo NEXT STEPS:
echo.
echo 1. Create a new repository on GitHub:
echo    - Go to https://github.com/new
echo    - Name: Nexus-Wifi-Radar-V2 (or your preferred name)
echo    - Description: Next-generation WiFi threat detection with AI-powered intelligence
echo    - Public or Private: Your choice
echo    - DO NOT initialize with README, .gitignore, or license
echo.
echo 2. Copy the repository URL from GitHub
echo    (looks like: https://github.com/yourusername/Nexus-Wifi-Radar-V2.git)
echo.
echo 3. Run these commands (replace URL with yours):
echo.
echo    git remote add origin https://github.com/yourusername/Nexus-Wifi-Radar-V2.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo ============================================================
echo.
echo TIP: If you want to change the commit message:
echo      git commit --amend -m "Your new message"
echo.
pause
