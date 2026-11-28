@echo off
setlocal EnableExtensions
title ANALIZA VIDEO
cd /d "%~dp0"
color 0F

rem ---------- gasesc un Python ca sa pornesc scriptul ----------
set "PY="
if exist "%LOCALAPPDATA%\AnalizaVideo\python\python.exe" set "PY=%LOCALAPPDATA%\AnalizaVideo\python\python.exe"
if not defined PY if exist "%LOCALAPPDATA%\py312\python.exe" set "PY=%LOCALAPPDATA%\py312\python.exe"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  where py >nul 2>&1 && set "PY=py -3"
)

if not defined PY (
  echo.
  echo   Nu am Python pe PC. Il descarc acum ^(47 MB, o singura data^).
  echo.
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALARE-1-PYTHON.ps1"
  if exist "%LOCALAPPDATA%\py312\python.exe" set "PY=%LOCALAPPDATA%\py312\python.exe"
)

if not defined PY (
  echo.
  echo   [!] Nu am putut porni. Ruleaza DIAGNOZA.bat si trimite-mi diagnoza.txt
  pause>nul
  exit /b 1
)

%PY% "%~dp0ANALIZA.py" %*
exit /b %ERRORLEVEL%
