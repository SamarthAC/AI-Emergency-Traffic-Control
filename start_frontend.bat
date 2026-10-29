@echo off
title AI Smart Ambulance - Frontend Dashboard
cd /d "%~dp0frontend"
echo ===================================================
echo Starting Frontend React Dashboard (Vite)
echo URL: http://localhost:5173
echo ===================================================
echo.
npm run dev
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Frontend encountered an error.
    pause
)
