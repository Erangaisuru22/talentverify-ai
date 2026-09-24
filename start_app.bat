@echo off
title TalentVerifyAI Launcher
echo ===================================================
echo           Starting TalentVerifyAI Application
echo ===================================================
echo.

cd /d "%~dp0"

:: 1. Check MongoDB Status
echo [1/3] Checking MongoDB connection...
netstat -ano | findstr :27017 >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] MongoDB does not seem to be running on port 27017.
    echo If you use local MongoDB, please make sure the MongoDB Windows Service is started.
    echo.
) else (
    echo [OK] MongoDB is active on port 27017.
)

:: 2. Start FastAPI Backend in a separate window
echo [2/3] Starting Backend (FastAPI on http://127.0.0.1:8000)...
start "TalentVerifyAI - Backend (Port 8000)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: 3. Start React Frontend in a separate window
echo [3/3] Starting Frontend (React Vite on http://localhost:5173)...
start "TalentVerifyAI - Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

:: Wait a moment for Vite & Uvicorn to boot up
echo.
echo Initializing servers, opening browser in 3 seconds...
timeout /t 3 /nobreak >nul

:: Automatically open default web browser to the app
start http://localhost:5173

echo.
echo ===================================================
echo  TalentVerifyAI is now up and running!
echo  - Frontend Web App: http://localhost:5173
echo  - Backend API:      http://127.0.0.1:8000
echo  - API Swagger Docs: http://127.0.0.1:8000/docs
echo ===================================================
echo Note: Keep the two server windows open while using the app.
echo.
pause
