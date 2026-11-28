@echo off
setlocal EnableExtensions EnableDelayedExpansion
title FACETOT - instalez Python + analizez video de pe YouTube
cd /d "%~dp0"
color 0F

set "CACHE=%LOCALAPPDATA%\rea-video-tool"
set "PYDIR=%CACHE%\python"
set "PY=%PYDIR%\python.exe"

echo.
echo  ===========================================================
echo   FACETOT - un singur dublu-click
echo  ===========================================================
echo.
echo   Nu am nevoie de Microsoft Store. Descarc tot de pe GitHub.
echo.

rem ============ 0. ce facem ============
set "ARG=%~1"
if "%ARG%"=="" (
  echo   Lipeste linkul YouTube si apasa Enter.
  echo   ^(sau trage un fisier .mp4 peste acest .bat^)
  echo.
  set /p "ARG=  Link/fisier: "
)
set "ARG=%ARG:"=%"
if "%ARG%"=="" ( echo   Nimic introdus. & pause>nul & exit /b 1 )

rem ============ 1. PYTHON ============
if not exist "%PY%" (
  where python >nul 2>&1
  if not errorlevel 1 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PV=%%v"
    echo   Python gasit pe sistem: !PV! - il folosesc pe acela.
    set "PY=python"
  ) else (
    echo   [1/5] Descarc Python 3.12 portabil ^(47 MB, fara instalare^)...
    mkdir "%CACHE%" 2>nul
    call "%~dp0PORTHON.bat"
    if not exist "%PY%" (
      echo.
      echo   [!] Nu am putut lua Python portabil din GitHub.
      echo       Incearca din nou. Daca pica iar, spune-mi.
      pause>nul & exit /b 1
    )
    echo        Python 3.12 gata.
  )
) else (
  echo   [1/5] Python portabil: deja instalat.
)

"%PY%" --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo   [!] Python portabil nu porneste pe PC-ul asta.
  echo       Incearca asta in loc ^(o singura data^):
  echo           winget install Python.Python.3.12
  echo       Apoi ruleaza din nou acest .bat.
  pause>nul & exit /b 1
)

rem ============ 2. FFPROBE / FFMPEG ============
if exist "%CACHE%\bin\ffmpeg.exe" (
  echo   [2/5] ffmpeg: deja instalat.
  set "PATH=%CACHE%\bin;%PATH%"
) else (
  where ffmpeg >nul 2>&1
  if not errorlevel 1 (
    echo   [2/5] ffmpeg: gasit pe sistem.
  ) else (
    echo   [2/5] Descarc ffmpeg ^(78 MB, o data^)...
    "%PY%" -m ensurepip --upgrade >nul 2>&1
    "%PY%" -m pip install --quiet --upgrade imageio-ffmpeg
    if errorlevel 1 (
      echo   [!] Nu am putut instala imageio-ffmpeg.
      pause>nul & exit /b 1
    )
    "%PY%" -c "import imageio_ffmpeg,os,shutil,pathlib;p=imageio_ffmpeg.get_ffmpeg_exe();d=pathlib.Path(os.environ['LOCALAPPDATA'])/'rea-video-tool'/'bin';d.mkdir(parents=True,exist_ok=True);shutil.copy(p,d/'ffmpeg.exe')"
    set "PATH=%CACHE%\bin;%PATH%"
  )
)

rem ============ 3. YT-DLP ============
if exist "%CACHE%\yt-dlp.exe" (
  echo   [3/5] yt-dlp: deja instalat.
) else (
  where yt-dlp >nul 2>&1
  if not errorlevel 1 (
    echo   [3/5] yt-dlp: gasit pe sistem.
  ) else (
    echo   [3/5] Descarc yt-dlp ^(17 MB^)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile '%CACHE%\yt-dlp.exe'"
    if not exist "%CACHE%\yt-dlp.exe" (
      echo   [!] Nu am putut descarca yt-dlp.
      pause>nul & exit /b 1
    )
  )
)
set "YTDLP=%CACHE%\yt-dlp.exe"
if not exist "%YTDLP%" set "YTDLP=yt-dlp"

rem ============ 4. VIDEO ============
set "VIDEO=%ARG%"
set "EFISIER="
if exist "%ARG%" set "EFISIER=1"

if defined EFISIER (
  echo   [4/5] Fisier local - nu descarc nimic de pe net.
  set "VIDEO=%~f1"
  if "%VIDEO%"=="" set "VIDEO=%ARG%"
) else (
  echo   [4/5] Descarc videoul de pe YouTube ^(max 1080p^)...
  mkdir "%CACHE%\dl" 2>nul
  "%YTDLP%" -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 -o "%CACHE%\dl\%(title).70s.%(ext)s" "%ARG%"
  if errorlevel 1 (
    echo.
    echo   [!] Descarcarea a esuat. Verifica linkul sau daca videoul e privat.
    pause>nul & exit /b 1
  )
  for /f "delims=" %%F in ('dir /b /o-d "%CACHE%\dl\*.mp4" 2^>nul') do (
    set "VIDEO=%CACHE%\dl\%%F"
    goto GOTVIDEO
  )
)
:GOTVIDEO
if not exist "%VIDEO%" (
  echo   [!] Nu gasesc videoul descarcat.
  pause>nul & exit /b 1
)

rem ============ 5. ANALIZA ============
set "OUT=%~dp0analiza"
if not exist "%OUT%" mkdir "%OUT%"

echo.
echo   [5/5] Scot taieturile + raportul ^(1-3 min^)...
echo.
"%PY%" "%~dp0inspecteaza.py" "%VIDEO%"
if errorlevel 1 (
  echo   [!] Analiza a esuat.
  pause>nul & exit /b 1
)

echo.
echo  ===========================================================
echo   GATA
echo  ===========================================================
echo.
for %%E in ("%VIDEO%") do set "BAZA=%%~dpnE"
echo    VIDEO   : %VIDEO%
echo    XML     : %BAZA%.xml      ^<- importi in FilmCraft ^(File ^> Import^)
echo    EDL     : %BAZA%.edl
echo    RAPORT  : %BAZA%-raport.html
echo.
choice /c YN /n /t 20 /d 1 /m "  Deschid raportul acum"
if errorlevel 2 goto SFARSIT
start "" "%BAZA%-raport.html"

:SFARSIT
echo.
echo   Vrei si descompunerea shot-cu-shot ^(rea-video, 10-15 min^)
choice /c YN /n /t 20 /d 1 /m "  Da sau nu"
if errorlevel 2 goto END

echo.
echo   Instalez rea-video ^(prima data: 5-10 min^)...
"%PY%" -m pip install --quiet --upgrade pip
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest 'https://codeload.github.com/JuneYaooo/rea-video/zip/refs/heads/main' -OutFile \"$env:TEMP\rea.zip\"; Expand-Archive \"$env:TEMP\rea.zip\" '%CACHE%' -Force"
for /d %%D in ("%CACHE%\rea-video-*") do (
  echo   instalez in %%D
  "%PY%" -m pip install --quiet -e "%%D"
  echo   rulez descompunerea...
  "%PY%" -m rea_video decompose "%VIDEO%" -o "%OUT%" --lang en --no-vlm
)
echo.
echo   Rezultatul: %OUT%\report.html
start "" "%OUT%\report.html"

:END
echo.
pause>nul
exit /b 0
