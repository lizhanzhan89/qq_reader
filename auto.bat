@echo off
REM 切换到指定目录
cd /d "I:\qq_reader(3)\qq_reader"

REM 后台运行 python app.py
start /b python app.py

REM 等待几秒确保 Flask 服务器启动
timeout /t 3 /nobreak >nul

REM 使用默认浏览器打开指定 URL
start "" "http://127.0.0.1:5001/#"