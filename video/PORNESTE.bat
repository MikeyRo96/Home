@echo off
setlocal EnableDelayedExpansion
title Analiza video - ce e in el si cum a fost facut
cd /d "%~dp0"

echo.
echo  ================================================================
echo    INSPECTEAZA UN VIDEO
echo  ================================================================
echo.

REM --- 1. Python prezent ---
set "PY="
for %%P in (py python python3) do (
  if not defined PY (
    %%P --version >nul 2>&1
    if not errorlevel 1 set "PY=%%P"
  )
)
if not defined PY (
  echo  LIPSA PYTHON. Instaleaza-l:
  echo.
  echo    winget install Python.Python.3.12
  echo.
  echo  Sau de pe python.org - bifeaza "Add python.exe to PATH".
  echo.
  pause
  exit /b
)
echo  Python: OK

REM --- 2. ffmpeg prezent ---
ffmpeg -version >nul 2>&1
if errorlevel 1 (
  echo  LIPSESTE ffmpeg. Se instaleaza automat acum...
  echo.
  winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
  echo.
  echo  Daca s-a instalat, INCHIDE fereastra asta si ruleaza din nou.
  echo  Daca nu, descarca manual: https://www.gyan.dev/ffmpeg/builds/
  echo  si pune bin\ffmpeg.exe in PATH.
  echo.
  pause
  exit /b
)
echo  ffmpeg: OK
echo.

REM --- 3. fisiere video in folder ---
set /a N=0
for %%F in (*.mp4 *.mkv *.mov *.webm *.avi *.m4v *.flv *.ts *.wmv *.mpg) do (
  set /a N+=1
  set "F_!N!=%%F"
)

if %N%==0 (
  echo  Nu e niciun video in folderul asta.
  echo.
  echo  Pune fisierul .mp4 langa PORNESTE.bat si ruleaza din nou.
  echo  Sau trage fisierul cu mouse-ul peste PORNESTE.bat.
  echo.
  pause
  exit /b
)

REM --- daca ai tras un fisier peste .bat ---
if not "%~1"=="" (
  echo  Analizez: %~nx1
  echo.
  %PY% inspecteaza.py "%~1"
  goto SFARSIT
)

REM --- meniu ---
echo  Fisiere gasite:
for /l %%i in (1,1,%N%) do echo     %%i . !F_%%i!
echo.
echo     0 . toate
echo.
set /p "ALEG=Alege numarul: "

if "%ALEG%"=="0" (
  for /l %%i in (1,1,%N%) do (
    echo.
    echo  ------------------------------------------------
    %PY% inspecteaza.py "!F_%%i!"
  )
) else (
  set "TINTA=!F_%ALEG%!"
  if not defined TINTA (
    echo  Numar invalid.
    pause
    exit /b
  )
  %PY% inspecteaza.py "!TINTA!"
)

:SFARSIT
echo.
echo  Raportul HTML s-a deschis Daca nu, il gasesti langa video,
echo  cu numele  NUMELE-VIDEO-raport.html
echo.
choice /c YN /n /m "  Deschid raportul acum [Y/N]: "
if errorlevel 2 exit /b
for %%R in (*-raport.html) do start "" "%%R"
exit /b
