@echo off
chcp 65001 >nul
title 汽车零部件表面缺陷智能检测系统
cd /d "%~dp0"

rem 优先使用独立安装的 Python 3.12，找不到再回退到 PATH 中的 python
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo ================================================
echo    汽车零部件表面缺陷智能检测系统
echo    正在启动，浏览器将自动打开...
echo    停止服务请直接关闭本窗口
echo ================================================

"%PYEXE%" start.py
if errorlevel 1 (
  echo.
  echo [启动失败] 若提示缺少依赖，请先执行：
  echo     "%PYEXE%" -m pip install -r requirements.txt
  pause
)
