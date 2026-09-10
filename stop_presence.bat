@echo off
setlocal enabledelayedexpansion
set LOCKFILE=%~dp0.daemon.lock

if exist "%LOCKFILE%" (
    set /p PID=<"%LOCKFILE%"
    set IMAGE=

    rem Resolve the PID's image name before killing anything. A lock file can
    rem outlive a crash, a logoff, or this script's own /F kill, and Windows
    rem recycles PIDs -- an unverified "taskkill /F /PID" can therefore destroy
    rem a completely unrelated process and still report success.
    rem tasklist writes its "No tasks are running" notice to stdout, not stderr,
    rem so it has to be filtered out or it lands in IMAGE as a bogus name.
    for /f "tokens=1 delims=," %%A in ('tasklist /FI "PID eq !PID!" /NH /FO CSV 2^>nul ^| findstr /V /C:"INFO:"') do set IMAGE=%%~A

    rem The daemon runs as the versioned interpreter (pythonw3.13.exe), not the
    rem pythonw.exe launcher stub that spawns it, so match on a substring rather
    rem than an exact image name. Frozen builds run as PacketTracerPresence.exe.
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
