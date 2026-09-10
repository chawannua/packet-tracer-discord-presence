@echo off
taskkill /F /IM pythonw.exe >nul 2>&1
echo Packet Tracer Presence background process stopped.
timeout /t 2 >nul
