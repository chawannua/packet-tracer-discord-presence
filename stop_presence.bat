@echo off
setlocal enabledelayedexpansion
set LOCKFILE=%~dp0.daemon.lock

if exist "%LOCKFILE%" (
    set /p PID=<"%LOCKFILE%"
    set IMAGE=

    for /f "tokens=1 delims=," %%A in ('tasklist /FI "PID eq !PID!" /NH /FO CSV 2^>nul ^| findstr /V /C:"INFO:"') do set IMAGE=%%~A

    echo !IMAGE! | findstr /I "python packettracerpresence" >nul
    if !errorlevel! equ 0 (
        taskkill /F /PID !PID! >nul 2>&1
        if !errorlevel! equ 0 (
            echo Packet Tracer Presence stopped ^(PID !PID!, !IMAGE!^).
            del "%LOCKFILE%" >nul 2>&1
            goto :done
        )
    ) else (
        if "!IMAGE!"=="" (
            echo Stale lock file ^(PID !PID! is not running^); cleaning up.
        ) else (
            echo Ignoring lock file: PID !PID! is !IMAGE!, not this daemon.
        )
        del "%LOCKFILE%" >nul 2>&1
    )
)

echo Falling back to stopping the daemon by image name.
taskkill /F /IM "pythonw*.exe" >nul 2>&1
taskkill /F /IM "PacketTracerPresence.exe" >nul 2>&1
echo Packet Tracer Presence background process stopped.

:done
timeout /t 2 >nul
