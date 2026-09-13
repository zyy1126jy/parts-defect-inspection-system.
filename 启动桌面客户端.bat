@echo off
chcp 65001 >nul
title Parts Defect Inspection - C/S Desktop Client
cd /d "%~dp0"

rem Prefer standalone Python 3.12, fallback to python on PATH
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

echo ================================================
echo    C/S Desktop Client (tkinter GUI)
echo    If not connected, start the server first:
echo       double-click "start the server" bat,
echo       or click "Start Local Server" in the GUI.
echo ================================================

"%PYEXE%" client\desktop_client.py
if errorlevel 1 (
  echo.
  echo [FAILED] If dependencies are missing, run:
  echo     "%PYEXE%" -m pip install -r requirements.txt
  pause
)
