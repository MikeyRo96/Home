@echo off
setlocal EnableExtensions EnableDelayedExpansion
title PAS 2 - taieturi exacte din video -> EDL/XML pentru FilmCraft
cd /d "%~dp0"
color 0F

echo.
echo  ===========================================================
echo   PAS 2 - scot TAIETURILE din video si le pun pe timeline
echo  ===========================================================
echo.
echo  Iti trebuie un fisier video (mp4, mov, mkv).
echo  Daca ai doar link YouTube, ruleaza intai ANALIZEAZA-VIDEO.bat.
echo.

set "VIDEO=%~1"
if "%VIDEO%"=="" (
  echo  Trage fisierul video peste acest .bat,
  echo  sau lipeste calea acum si apasa Enter.
  echo.
  set /p "VIDEO=  Cale video: "
)
set "VIDEO=%VIDEO:"=%"
if "%VIDEO%"=="" ( echo  Nimic. & pause>nul & exit /b 1 )
if not exist "%VIDEO%" ( echo  Nu gasesc fisierul: %VIDEO% & pause>nul & exit /b 1 )

rem ---------- python ----------
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
  echo  [!] Python lipseste. Ruleaza 1-TESTEAZA-ASTA.bat.
  pause>nul & exit /b 1
)

rem ---------- ffmpeg local (fara instalare) ----------
set "FFDIR=%LOCALAPPDATA%\rea-video-tool\bin"
if exist "%FFDIR%\ffmpeg.exe" (
  set "PATH=%FFDIR%;%PATH%"
  echo  ffmpeg: gasit local
) else (
  where ffmpeg >nul 2>&1
  if errorlevel 1 (
    echo.
    echo  Lipseste ffmpeg. Il iau din pachetul Python ^(78 MB, o data^).
    echo.
    %PY% -m pip install --quiet --upgrade imageio-ffmpeg
    if errorlevel 1 (
      echo  [!] Nu am putut instala imageio-ffmpeg.
      pause>nul & exit /b 1
    )
    %PY% -c "import imageio_ffmpeg,os,shutil,pathlib;p=imageio_ffmpeg.get_ffmpeg_exe();d=pathlib.Path(os.environ['LOCALAPPDATA'])/'rea-video-tool'/'bin';d.mkdir(parents=True,exist_ok=True);shutil.copy(p,d/'ffmpeg.exe')"
    set "PATH=%FFDIR%;%PATH%"
  ) else (
    echo  ffmpeg: gasit pe sistem
  )
)

rem ---------- prag: intreaba ----------
echo.
echo  Ce fel de video este
echo.
echo    [1] vlog / gaming / tutorial / talking-head   (recomandat)
echo    [2] slide-uri, text pe fundal uniform, animatii simple
echo.
choice /c 12 /n /t 20 /d 1 /m "  Alege"
if errorlevel 2 ( set "PRAG=0.30" ) else ( set "PRAG=0.45" )
echo.
echo  Prag folosit: %PRAG%

rem ---------- rulare ----------
echo.
echo  Analizez... (10-60 s pentru 20 de minute de video)
echo.
%PY% "%~dp0inspecteaza.py" "%VIDEO%" --prag %PRAG%
if errorlevel 1 (
  echo.
  echo  [!] Analiza a esuat. Vezi mesajul de mai sus.
  pause>nul & exit /b 1
)

set "BAZA=%~dpn1"
if "%BAZA%"=="" for %%F in ("%VIDEO%") do set "BAZA=%%~dpnF"

echo.
echo  ===========================================================
echo   GATA. Ai acum:
echo  ===========================================================
echo.
echo    %BAZA%.xml      ^<- asta il importi in FilmCraft
echo    %BAZA%.edl      ^<- alternativa (Premiere, Resolve)
echo    %BAZA%-markere.csv
echo    %BAZA%-capitole.txt
echo    %BAZA%-raport.html
echo.
echo  In FilmCraft:  File  -^>  Import  -^>  %BAZA%.xml
echo  Atentie: Import, NU Open Project.
echo.

choice /c YN /n /t 20 /d 1 /m "  Deschid raportul HTML acum"
if errorlevel 2 goto SFARSIT
start "" "%BAZA%-raport.html"

:SFARSIT
echo.
pause>nul
exit /b 0
