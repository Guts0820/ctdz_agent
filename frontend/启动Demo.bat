@echo off
chcp 65001 >nul
echo ========================================
echo   小学生数学知识图谱 - APP Demo 启动
echo ========================================
echo.
echo 正在启动本地服务器...
echo 启动后请访问: http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0"
python -m http.server 3000
pause
