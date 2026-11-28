@echo off
setlocal EnableExtensions
title ANALIZEAZA VIDEO - YouTube sau fisier local
cd /d "%~dp0"

echo.
echo  ============================================================
echo   ANALIZA UNUI VIDEO - cum a fost facut, shot cu shot
echo  ============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  where py >nul 2>&1
  if errorlevel 1 (
    echo  [!] Python lipseste.
    echo      Deschid magazinul Microsoft. Instaleaza "Python 3.12",
    echo      bifeaza "Add python.exe to PATH", apoi ruleaza din nou.
    start ms-windows-store://search/?query=Python%203.12
    pause
    exit /b 1
  )
  set "PY=py -3"
) else (
  set "PY=python"
)

set "ARG="
if not "%~1"=="" (
  set "ARG=%~1"
) else (
  echo  Lipeste linkul YouTube in fereastra asta si apasa Enter.
  echo  ^(sau inchide si trage un fisier .mp4 peste acest .bat^)
  echo.
  set /p "ARG=  Link: "
)

if "%ARG%"=="" (
  echo  Nimic introdus.
  pause
  exit /b 1
)

echo.
%PY% "%~dp0analizeaza.py" "%ARG%"

echo.
echo  ============================================================
echo   Gata. Raportul s-a deschis in browser.
echo  ============================================================
pause
