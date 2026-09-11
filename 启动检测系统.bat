@echo off
chcp 65001 >nul
title 汽车零部件表面缺陷智能检测系统
cd /d "%~dp0"
echo ================================================
echo    汽车零部件表面缺陷智能检测系统
echo    正在启动，浏览器将自动打开...
echo    停止服务请直接关闭本窗口
echo ================================================
python start.py
if errorlevel 1 (
  echo.
  echo [启动失败] 若提示缺少依赖，请先执行：
  echo     pip install -r requirements.txt
  pause
)
