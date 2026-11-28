@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "QUIET="
if /i "%~1"=="/quiet" set "QUIET=1"
title INSTALEAZA PYTHON - fara Microsoft Store
color 0F
cd /d "%~dp0"

set "CACHE=%LOCALAPPDATA%\rea-video-tool"
set "PYDIR=%CACHE%\python"
set "PY=%PYDIR%\python.exe"
set "URL=https://github.com/astral-sh/python-build-standalone/releases/download/20261124/cpython-3.12.16+20261124-x86_64-pc-windows-msvc-install_only.tar.gz"

echo.
echo  ===========================================================
echo   INSTALEAZA PYTHON 3.12 - portabil, fara Store
echo  ===========================================================
echo.

if exist "%PY%" (
  echo   Python e deja aici:
  echo   %PY%
  "%PY%" --version
  echo.
  echo   Nu mai e nimic de facut.
  if not defined QUIET pause
  exit /b 0
)

echo   Descarc 47 MB de pe GitHub...
echo   %URL%
echo.

rem ---- 1. descarc cu BITS (cel mai stabil pe Windows) ----
if exist "%TEMP%\py.tgz" del /f /q "%TEMP%\py.tgz" 2>nul
powershell -NoProfile -Command "Start-BitsTransfer -Source '%URL%' -Destination '%TEMP%\py.tgz' -ErrorAction Stop" >nul 2>&1
if not exist "%TEMP%\py.tgz" (
  echo   BITS n-a mers, incerc alt mod...
  powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; (New-Object Net.WebClient).DownloadFile('%URL%','%TEMP%\py.tgz')"
)

if not exist "%TEMP%\py.tgz" (
  echo.
  echo   [!] Descarcarea a esuat.
  echo       Verifica internetul, apoi ruleaza din nou.
  if not defined QUIET pause
  exit /b 1
)

for %%A in ("%TEMP%\py.tgz") do set "SZ=%%~zA"
echo   descarcat: !SZ! bytes
if !SZ! LSS 1000000 (
  echo.
  echo   [!] Fisierul e prea mic - descarcarea s-a rupt.
  del /f /q "%TEMP%\py.tgz" 2>nul
  if not defined QUIET pause
  exit /b 1
)

rem ---- 2. dezarhivez ----
echo   dezarhivez...
mkdir "%TEMP%\pyx" 2>nul
rmdir /s /q "%TEMP%\pyx" 2>nul
mkdir "%TEMP%\pyx"

tar -xzf "%TEMP%\py.tgz" -C "%TEMP%\pyx"
if errorlevel 1 (
  echo.
  echo   [!] tar a esuat. Incerc cu Expand-Archive...
  powershell -NoProfile -Command "Expand-Archive -Path '%TEMP%\py.tgz' -DestinationPath '%TEMP%\pyx' -Force -ErrorAction Stop"
)

if not exist "%TEMP%\pyx\python\python.exe" (
  echo.
  echo   [!] Nu gasesc python.exe dupa dezarhivare.
  echo       Continut:
  dir /b "%TEMP%\pyx"
  if not defined QUIET pause
  exit /b 1
)

rem ---- 3. copiez la locul lui ----
echo   copiez...
mkdir "%PYDIR%" 2>nul
xcopy /e /i /y /q "%TEMP%\pyx\python\*" "%PYDIR%\" >nul
rmdir /s /q "%TEMP%\pyx" 2>nul
del /f /q "%TEMP%\py.tgz" 2>nul

rem ---- 4. verific ----
if not exist "%PY%" (
  echo.
  echo   [!] Copierea a esuat.
  if not defined QUIET pause
  exit /b 1
)

echo.
echo   ===========================================================
echo   GATA
echo   ===========================================================
"%PY%" --version
echo   Loc: %PY%
echo.
echo   Acum poti rula FACETOT.bat.
if not defined QUIET pause
exit /b 0
