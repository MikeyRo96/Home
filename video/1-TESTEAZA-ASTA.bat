@echo off
setlocal EnableExtensions EnableDelayedExpansion
title TEST 1 - verifica ce ai pe PC
cd /d "%~dp0"
color 0F

echo.
echo  ===========================================================
echo   TESTUL 1 - ce ai deja pe PC
echo   Dureaza 20 de secunde. Nu descarca nimic.
echo  ===========================================================
echo.

set "OK=0"
set "LIPSA=0"

rem ---------------- PYTHON ----------------
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY (
  where py >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
  echo  [X] PYTHON      - lipseste
  set /a LIPSA+=1
) else (
  for /f "tokens=*" %%v in ('%PY% --version 2^>^&1') do set "PYV=%%v"
  echo  [OK] PYTHON     - !PYV!
  set /a OK+=1
)

rem ---------------- FFPROBE ----------------
where ffprobe >nul 2>&1
if errorlevel 1 (
  echo  [X] FFPROBE     - lipseste ^(il descarca .bat-ul urmator singur^)
  set /a LIPSA+=1
) else (
  echo  [OK] FFPROBE    - instalat
  set /a OK+=1
)

rem ---------------- YT-DLP ----------------
where yt-dlp >nul 2>&1
if errorlevel 1 (
  echo  [X] YT-DLP      - lipseste ^(il descarca .bat-ul urmator singur^)
  set /a LIPSA+=1
) else (
  echo  [OK] YT-DLP     - instalat
  set /a OK+=1
)

rem ---------------- INTERNET ----------------
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'https://api.github.com' -UseBasicParsing -TimeoutSec 8; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo  [X] INTERNET    - nu merge / blocat
  set /a LIPSA+=1
) else (
  echo  [OK] INTERNET    - merge
  set /a OK+=1
)

rem ---------------- SPATIU DISC ----------------
for /f "tokens=3" %%a in ('dir /-c "%LOCALAPPDATA%" ^| findstr /C:"bytes free"') do set "LIBER=%%a"
if defined LIBER (
  echo  [i] SPATIU      - %LIBER% bytes liberi in LOCALAPPDATA
  echo                   ^(ai nevoie de ~2 GB^)
)

echo.
echo  -----------------------------------------------------------
echo   REZULTAT: %OK% OK / %LIPSA% lipsa
echo  -----------------------------------------------------------
echo.

if %LIPSA%==0 (
  echo   TOTUL E GATA. Treci la pasul 2:
  echo   dublu-click pe ANALIZEAZA-VIDEO.bat si lipeste linkul YouTube.
) else (
  echo   Nu e nimic rupt. ANALIZEAZA-VIDEO.bat descarca singur
  echo   ffmpeg si yt-dlp. Doar PYTHON trebuie pus de mana:
  echo.
  echo   Deschide magazinul Microsoft si instaleaza "Python 3.12".
  echo   BIFEZA "Add python.exe to PATH" la instalare.
  echo.
  choice /c YN /n /t 20 /d 1 /m "Deschid magazinul Microsoft acum"
  if errorlevel 2 goto GATA
  start ms-windows-store://search/?query=Python%203.12
)

:GATA
echo.
echo  -----------------------------------------------------------
echo   Trimite-mi ce scrie mai sus (screenshot sau copy-paste).
echo  -----------------------------------------------------------
echo.
pause>nul
exit /b 0
