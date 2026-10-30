@echo off
title AI Smart Ambulance - SUMO Simulation (WITHOUT Green Corridor - Baseline)
cd /d "%~dp0model"
echo ===================================================
echo Launching SUMO Simulation: BASELINE (WITHOUT CORRIDOR)
echo Green Corridor: DISABLED
echo Live Cameras: ENABLED
echo Pickup Replan: ENABLED
echo Target Backend: http://127.0.0.1:8000
echo ===================================================
echo.
python ai_emergency_demo.py --no-green-corridor --live-cameras --pickup-replan --backend-url http://127.0.0.1:8000
pause
