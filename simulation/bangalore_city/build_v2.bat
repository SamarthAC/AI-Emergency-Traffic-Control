@echo off
echo ============================================================
echo Building Bengaluru-inspired realistic V2 SUMO network
echo ============================================================
netconvert ^
 --node-files bengaluru_v2.nod.xml ^
 --edge-files bengaluru_v2.edg.xml ^
 --type-files bengaluru_v2.typ.xml ^
 --output-file bengaluru_v2.net.xml ^
 --no-turnarounds true ^
 --junctions.corner-detail 8 ^
 --geometry.remove false ^
 --roundabouts.guess true ^
 --tls.guess false

if %ERRORLEVEL% NEQ 0 (
 echo.
 echo BUILD FAILED - copy the full error back to ChatGPT.
 pause
 exit /b %ERRORLEVEL%
)
echo.
echo SUCCESS: bengaluru_v2.net.xml created.
echo Opening NETEDIT...
netedit bengaluru_v2.net.xml
