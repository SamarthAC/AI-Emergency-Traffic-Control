@echo off
title AI Smart Ambulance - Backend Server
cd /d "%~dp0backend"
echo ===================================================
echo Starting AI Smart Ambulance Backend (FastAPI / Uvicorn)
echo URL: http://127.0.0.1:8000
echo WebSocket: ws://127.0.0.1:8000/ws
echo ===================================================
echo.
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Backend crashed or encountered an error.
    pause
)
