@echo off
echo Building Bengaluru-inspired SUMO network...
netconvert ^
  --node-files bangalore_city.nod.xml ^
  --edge-files bangalore_city.edg.xml ^
  --type-files bangalore_city.typ.xml ^
  --output-file bangalore_city.net.xml ^
  --junctions.join-dist 8 ^
  --roundabouts.guess true ^
  --tls.guess false ^
  --ramps.guess false

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo ERROR: netconvert failed.
  pause
  exit /b %ERRORLEVEL%
)

echo.
echo Network created: bangalore_city.net.xml
echo Open it with:
echo netedit bangalore_city.net.xml
pause
