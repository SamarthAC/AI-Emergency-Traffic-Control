@echo off
echo ===========================================================
echo Building structured Bengaluru-inspired SUMO network
echo ===========================================================
netconvert ^
  --node-files bengaluru_structured.nod.xml ^
  --edge-files bengaluru_structured.edg.xml ^
  --type-files bengaluru_structured.typ.xml ^
  --output-file bengaluru_structured.net.xml ^
  --junctions.corner-detail 8 ^
  --geometry.remove false ^
  --roundabouts.guess true ^
  --tls.guess false ^
  --no-turnarounds true

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo NETWORK BUILD FAILED.
  pause
  exit /b %ERRORLEVEL%
)

echo.
echo SUCCESS: bengaluru_structured.net.xml created.
echo Opening SUMO-GUI with routes and presentation zones...
sumo-gui -c bengaluru_structured.sumocfg
