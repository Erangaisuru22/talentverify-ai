@echo off
title TalentVerifyAI Stopper
echo ===================================================
echo           Stopping TalentVerifyAI Servers
echo ===================================================
echo.

echo Stopping FastAPI Backend on Port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Stopping React Vite Frontend on Port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [OK] Backend and Frontend have been stopped.
echo ===================================================
timeout /t 2 /nobreak >nul
exit
