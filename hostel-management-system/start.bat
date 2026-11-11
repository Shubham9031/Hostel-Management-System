@echo off
title Hostel Management System
echo ===================================================
echo     Starting Hostel Management System (Flask + MongoDB)
echo ===================================================
echo.
cd /d "%~dp0"
echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b
)

echo Starting Flask Application...
echo Access in browser: http://127.0.0.1:5000
echo.
python run.py
pause

