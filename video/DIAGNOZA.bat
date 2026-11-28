@echo off
setlocal EnableExtensions EnableDelayedExpansion
title DIAGNOZA - fac un log pe care mi-l trimiti
cd /d "%~dp0"
color 0F
set "LOG=%~dp0diagnoza.txt"
> "%LOG%" echo === DIAGNOZA %DATE% %TIME% ===

>>"%LOG%" echo --- ver ---
ver >>"%LOG%" 2>&1
>>"%LOG%" echo --- unde sunt ---
>>"%LOG%" echo %CD%
>>"%LOG%" echo --- python ---
where python >>"%LOG%" 2>&1
if exist "%LOCALAPPDATA%\py312\python.exe" (
  >>"%LOG%" echo PORTABIL: %LOCALAPPDATA%\py312\python.exe
  "%LOCALAPPDATA%\py312\python.exe" --version >>"%LOG%" 2>&1
) else (
  >>"%LOG%" echo NU exista %LOCALAPPDATA%\py312\python.exe
)
>>"%LOG%" echo --- ffmpeg ---
if exist "%LOCALAPPDATA%\ffbin\ffmpeg.exe" (
  "%LOCALAPPDATA%\ffbin\ffmpeg.exe" -version 2>&1 | findstr /C:"version" >>"%LOG%" 2>&1
  >>"%LOG%" echo FFMPEG OK
) else (
  >>"%LOG%" echo NU exista %LOCALAPPDATA%\ffbin\ffmpeg.exe
)
>>"%LOG%" echo --- ffprobe ---
if exist "%LOCALAPPDATA%\ffbin\ffprobe.exe" (
  "%LOCALAPPDATA%\ffbin\ffprobe.exe" -version 2>&1 | findstr /C:"version" >>"%LOG%" 2>&1
  >>"%LOG%" echo FFPROBE OK
) else (
  >>"%LOG%" echo NU exista ffprobe
)
>>"%LOG%" echo --- rea-video ---
if exist "%LOCALAPPDATA%\rea-src\pyproject.toml" (
  >>"%LOG%" echo SURSA OK: %LOCALAPPDATA%\rea-src
) else (
  >>"%LOG%" echo NU exista sursa rea-video
)
if exist "%LOCALAPPDATA%\py312\python.exe" (
  "%LOCALAPPDATA%\py312\python.exe" -c "import rea_video;print('MODUL OK')" >>"%LOG%" 2>&1
)
>>"%LOG%" echo --- yt-dlp ---
if exist "%LOCALAPPDATA%\ffbin\yt-dlp.exe" (
  "%LOCALAPPDATA%\ffbin\yt-dlp.exe" --version >>"%LOG%" 2>&1
) else (
  >>"%LOG%" echo NU exista yt-dlp
)
>>"%LOG%" echo --- internet ---
curl -s -o nul -w "github: %{http_code}" https://github.com >>"%LOG%" 2>&1
>>"%LOG%" echo --- gata ---

echo.
echo  Log scris in: %LOG%
echo  Se deschide acum. Da Ctrl+A, Ctrl+C, trimite-mi.
echo.
start "" notepad "%LOG%"
pause>nul
exit /b 0
