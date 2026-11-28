# -*- coding: utf-8 -*-
# rea-video (originalul) + yt-dlp, fara admin
$ErrorActionPreference = 'Stop'

$py   = Join-Path $env:LOCALAPPDATA 'py312\python.exe'
$ffb  = Join-Path $env:LOCALAPPDATA 'ffbin'
if (-not (Test-Path $py))  { Write-Host "Ruleaza intai INSTALARE-1-PYTHON.ps1" -ForegroundColor Red; exit 1 }
if (-not (Test-Path "$ffb\ffmpeg.exe")) { Write-Host "Ruleaza intai INSTALARE-2-FFMPEG.ps1" -ForegroundColor Red; exit 1 }
$env:PATH = "$ffb;$env:PATH"

# yt-dlp
$yt = Join-Path $ffb 'yt-dlp.exe'
if (-not (Test-Path $yt)) {
    Write-Host "[1/3] Descarc yt-dlp (~23 MB)..." -ForegroundColor Cyan
    Invoke-WebRequest 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile $yt
}
Write-Host "[1/3] yt-dlp gata" -ForegroundColor Green

# git? daca nu, iau zip-ul
Write-Host "[2/3] Descarc rea-video..." -ForegroundColor Cyan
$src = Join-Path $env:LOCALAPPDATA 'rea-src'
if (-not (Test-Path "$src\pyproject.toml")) {
    $zip = Join-Path $env:TEMP 'rea.zip'
    $tmp = Join-Path $env:TEMP 'reax'
    Invoke-WebRequest 'https://codeload.github.com/JuneYaooo/rea-video/zip/refs/heads/main' -OutFile $zip
    if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $inner = Get-ChildItem $tmp -Directory | Select-Object -First 1
    if (Test-Path $src) { Remove-Item -Recurse -Force $src }
    Move-Item $inner.FullName $src
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
    Remove-Item -Force $zip
}
Write-Host "      sursa: $src"

Write-Host "[3/3] Instalez rea-video (~600 MB, 5-10 min)..." -ForegroundColor Cyan
& $py -m ensurepip --upgrade | Out-Null
& $py -m pip install --quiet --upgrade pip
& $py -m pip install --quiet -e "$src[ocr]"
if ($LASTEXITCODE -ne 0) { Write-Host "Instalarea a esuat. Vezi mesajul de mai sus." -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "GATA." -ForegroundColor Green
& $py -m rea_video --help | Select-Object -First 3
Write-Host ""
Write-Host "Acum ruleaza:  .\ANALIZEAZA.ps1" -ForegroundColor Yellow
