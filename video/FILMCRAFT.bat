@echo off
setlocal EnableExtensions
title FILMCRAFT - deschide timeline-ul
cd /d "%~dp0"
color 0F

set "PY=%LOCALAPPDATA%\AnalizaVideo\python\python.exe"
if not exist "%PY%" if exist "%LOCALAPPDATA%\py312\python.exe" set "PY=%LOCALAPPDATA%\py312\python.exe"

if not exist "%PY%" (
  echo.
  echo   Nu am gasit Python. Ruleaza intai RULEAZA.bat o data.
  echo.
  pause>nul
  exit /b 1
)

rem caut PROIECT.xml (varianta FilmCraft) inaintea celui -PREMIERE
set "XML=%~1"
if "%XML%"=="" if exist "%~dp0PROIECT.xml" set "XML=%~dp0PROIECT.xml"
if "%XML%"=="" if exist "%~dp0video\PROIECT.xml" set "XML=%~dp0video\PROIECT.xml"
if "%XML%"=="" (
  for /r "%~dp0" %%F in (PROIECT.xml) do if not defined XML set "XML=%%~fF"
)
if "%XML%"=="" (
  for %%F in ("%~dp0*.xml") do if not defined XML set "XML=%%~fF"
)

if "%XML%"=="" (
  echo.
  echo   Nu gasesc niciun .xml in folderul asta.
  echo   Ruleaza RULEAZA.bat intai, apoi revino aici.
  echo.
  pause>nul
  exit /b 1
)

echo.
echo   Timeline: %XML%
echo   Descarc FilmCraft daca nu e deja (108 MB, o singura data)...
echo.

"%PY%" -c "import sys,importlib.util;spec=importlib.util.spec_from_file_location('az',r'%~dp0ANALIZA.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);ok=m.deschide_filmcraft_cu_xml(r'%XML%');sys.exit(0 if ok else 1)"

if errorlevel 1 (
  echo.
  echo   [!] Nu a mers. Ruleaza RULEAZA.bat si alege [D]a la intrebarea cu FilmCraft.
  echo.
)
exit /b 0
