@echo off
title AI Smart Ambulance - SUMO Simulation (WITH Green Corridor)
cd /d "%~dp0model"
echo ===================================================
echo Launching SUMO Simulation: WITH GREEN CORRIDOR
echo Live Cameras: ENABLED
echo Pickup Replan: ENABLED
echo Target Backend: http://127.0.0.1:8000
echo ===================================================
echo.
python ai_emergency_demo.py --live-cameras --pickup-replan --backend-url http://127.0.0.1:8000
pause
