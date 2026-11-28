@echo off
setlocal
title FilmCraft - descarc si deschid
echo.
echo  FilmCraft 0.20.1 - portabil, fara instalare
echo  Descarc 113 MB... (o singura data)
echo.

set "DIR=%LOCALAPPDATA%\FilmCraft-portabil"
set "ZIP=%TEMP%\filmcraft-win64.zip"
set "URL=https://github.com/storytold/filmcraft/releases/download/v0.20.1/filmcraft-0.20.1-windows-x64-portable.zip"

if exist "%DIR%\filmcraft.exe" goto RUN

powershell -NoProfile -WindowStyle Hidden -Command ^
  "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIP%'; New-Item -ItemType Directory -Force -Path '%DIR%' | Out-Null; Expand-Archive -Path '%ZIP%' -DestinationPath '%DIR%' -Force; Remove-Item '%ZIP%' -Force"

if not exist "%DIR%\filmcraft.exe" (
  echo  EROARE: descarcarea a esuat. Verifica internetul si ruleaza din nou.
  pause
  exit /b 1
)

:RUN
set "WGPU_BACKEND=vulkan"
for /r "%DIR%" %%F in (filmcraft.exe) do (
  start "" "%%F"
  goto DONE
)
echo  Nu am gasit filmcraft.exe in %DIR%
pause
exit /b 1

:DONE
echo  Pornit. Fereastra apare in cateva secunde.
timeout /t 3 >nul
