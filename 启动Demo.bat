@echo off
cd /d "%~dp0"
echo ================================================
echo   ctdz_agent 一键启动 Demo
echo   访问 http://localhost:3000
echo   停止：在本窗口按 Ctrl+C
echo ================================================
echo.
D:\ctdz_agent\.venv\Scripts\python.exe start_demo.py
pause
