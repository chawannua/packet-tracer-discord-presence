@echo off
setlocal enabledelayedexpansion
set LOCKFILE=%~dp0.daemon.lock

if exist "%LOCKFILE%" (
    set /p PID=<"%LOCKFILE%"
    taskkill /F /PID !PID! >nul 2>&1
    if !errorlevel! equ 0 (
        echo Packet Tracer Presence stopped (PID !PID!).
        del "%LOCKFILE%" >nul 2>&1
        goto :done
    )
)

echo No lock file or stale PID; falling back to killing all pythonw.exe.
taskkill /F /IM pythonw.exe >nul 2>&1
echo Packet Tracer Presence background process stopped.

:done
timeout /t 2 >nul
