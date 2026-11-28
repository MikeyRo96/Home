# -*- coding: utf-8 -*-
# ffmpeg COMPLET (cu ffprobe real) de pe github, fara winget, fara admin
$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

$bin = Join-Path $env:LOCALAPPDATA 'ffbin'
$exe = Join-Path $bin 'ffmpeg.exe'
if (Test-Path $exe) {
    Write-Host "ffmpeg deja instalat: $exe" -ForegroundColor Green
    exit 0
}

$zip = Join-Path $env:TEMP 'ffmpeg.zip'
$tmp = Join-Path $env:TEMP 'ffx'

Write-Host "[1/3] Descarc ffmpeg (~40 MB)..." -ForegroundColor Cyan
$rel = Invoke-RestMethod 'https://api.github.com/repos/GyanD/codexffmpeg/releases/latest'
$asset = $rel.assets | Where-Object { $_.name -like '*essentials_build.zip' } | Select-Object -First 1
if (-not $asset) { throw "nu gasesc build-ul essentials in ultima versiune" }
Write-Host "      iau: $($asset.name)"
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip
Write-Host "      descarcat: $((Get-Item $zip).Length) bytes"

Write-Host "[2/3] Dezarhivez..." -ForegroundColor Cyan
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
Expand-Archive -Path $zip -DestinationPath $tmp -Force

Write-Host "[3/3] Copiez ffmpeg.exe + ffprobe.exe in $bin ..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $bin | Out-Null
Get-ChildItem -Path $tmp -Recurse -Include ffmpeg.exe, ffprobe.exe | ForEach-Object {
    Copy-Item $_.FullName -Destination $bin -Force
    Write-Host "      $($_.Name)"
}
Remove-Item -Recurse -Force $tmp
Remove-Item -Force $zip

Write-Host ""
Write-Host "GATA." -ForegroundColor Green
& (Join-Path $bin 'ffmpeg.exe') -version | Select-Object -First 1
& (Join-Path $bin 'ffprobe.exe') -version | Select-Object -First 1
Write-Host ""
Write-Host "Acum ruleaza:  .\INSTALARE-3-REA-VIDEO.ps1" -ForegroundColor Yellow
