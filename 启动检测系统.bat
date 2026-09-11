@echo off
chcp 65001 >nul
title Parts Defect Inspection System
cd /d "%~dp0"

rem Prefer standalone Python 3.12, fallback to python on PATH
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo ================================================
echo    Parts Defect Inspection System
echo    Starting, browser will open automatically...
echo    Close this window to stop the server.
echo ================================================

"%PYEXE%" start.py
if errorlevel 1 (
  echo.
  echo [FAILED] If dependencies are missing, run:
  echo     "%PYEXE%" -m pip install -r requirements.txt
  pause
)
