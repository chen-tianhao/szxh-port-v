@echo off
cd /d "%~dp0"
echo 打开 http://127.0.0.1:8765/index.html
python -m http.server 8765
pause
