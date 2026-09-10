@echo off
setlocal enabledelayedexpansion

title Cisco Packet Tracer Presence - Installer
echo ========================================================
echo   Cisco Packet Tracer - Discord Rich Presence Installer
echo ========================================================
echo.

:: 1. Check Python installation
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH!
    echo Please install Python 3.9 or newer from https://www.python.org/
    pause
    exit /b 1
)

echo [*] Python detected. Checking virtual environment...

:: 2. Create virtual environment if it does not exist
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Install/upgrade dependencies
echo [*] Installing required dependencies (pypresence, psutil, pygetwindow)...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\pip.exe" install --quiet -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: 4. Install Windows Autostart shortcut
echo [*] Setting up silent background autostart...
".venv\Scripts\python.exe" install_autostart.py

:: 5. Launch the service silently right now
echo [*] Starting Packet Tracer Presence in the background...
wscript.exe start_silently.vbs

echo.
echo ========================================================
echo   SUCCESS! Installation Complete!
echo ========================================================
echo - The presence service is now running silently in the background.
echo - It will automatically activate whenever you open Cisco Packet Tracer.
echo - It will automatically start up on Windows boot.
echo.
echo Press any key to exit this installer...
pause >nul
