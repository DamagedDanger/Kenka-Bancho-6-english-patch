@echo off
title Kenka Bancho 6 English patch
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag your game file ^(.3ds / .cia^) or the extracted RomFS folder onto this file.
  echo.
  pause
  exit /b 1
)
set PYCMD=
where py >nul 2>nul && set PYCMD=py -3
if not defined PYCMD (
  where python >nul 2>nul && set PYCMD=python
)
if not defined PYCMD (
  echo Python was not found. Install Python 3 from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" in the installer, then try again.
  echo.
  pause
  exit /b 1
)
%PYCMD% kb6_patcher.py %*
echo.
pause
