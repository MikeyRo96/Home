@echo off
setlocal EnableExtensions
title ANALIZEAZA VIDEO - YouTube
cd /d "%~dp0"
color 0F

set "ARG=%~1"
if "%ARG%"=="" (
  echo.
  echo   Lipeste linkul YouTube si apasa Enter.
  echo.
  set /p "ARG=  Link: "
)
if "%ARG%"=="" ( echo   Nimic. & pause>nul & exit /b 1 )

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ANALIZEAZA.ps1" -Link "%ARG%"
echo.
pause>nul
exit /b 0
