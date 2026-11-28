@echo off
setlocal EnableExtensions
title INSTALEAZA TOT - fara winget, fara Store, fara admin
cd /d "%~dp0"
color 0F

echo.
echo  ============================================================
echo   INSTALEAZA TOT  (Windows fara winget)
echo  ============================================================
echo.
echo   Nu folosesc winget. Descarc tot de pe GitHub.
echo   Nu am nevoie de drepturi de administrator.
echo.

echo   [1/3] Python 3.12...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALARE-1-PYTHON.ps1"
if errorlevel 1 goto EROARE

echo.
echo   [2/3] ffmpeg + ffprobe...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALARE-2-FFMPEG.ps1"
if errorlevel 1 goto EROARE

echo.
echo   [3/3] rea-video + yt-dlp  (5-10 min)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALARE-3-REA-VIDEO.ps1"
if errorlevel 1 goto EROARE

echo.
echo  ============================================================
echo   GATA. Totul e instalat.
echo  ============================================================
echo.
echo   Acum ruleaza:  ANALIZEAZA-TOT.bat
echo.
pause>nul
exit /b 0

:EROARE
echo.
echo  ============================================================
echo   A PICAT LA PASUL DE MAI SUS
echo  ============================================================
echo.
echo   Ruleaza DIAGNOZA.bat si trimite-mi diagnoza.txt
echo.
pause>nul
exit /b 1
