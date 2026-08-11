@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo   APP Demo - http://localhost:3000
echo   Press Ctrl+C to stop
echo ========================================
echo.
start "" http://localhost:3000
python -m http.server 3000
pause
