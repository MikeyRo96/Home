# -*- coding: utf-8 -*-
# descarca videoul de pe YouTube si il analizeaza
param([string]$Link)
$ErrorActionPreference = 'Stop'

$py  = Join-Path $env:LOCALAPPDATA 'py312\python.exe'
$ffb = Join-Path $env:LOCALAPPDATA 'ffbin'
$env:PATH = "$ffb;$env:PATH"

if (-not $Link) {
    $Link = Read-Host "Lipeste linkul YouTube"
}
$Link = $Link.Trim().Trim('"')

Write-Host "[1/2] Descarc videoul..." -ForegroundColor Cyan
& (Join-Path $ffb 'yt-dlp.exe') -f "bv*[height<=1080]+ba" --merge-output-format mp4 -o "%(title).80s.%(ext)s" $Link
$video = Get-ChildItem -Filter *.mp4 | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $video) { Write-Host "Descarcarea a esuat." -ForegroundColor Red; exit 1 }
Write-Host "      $($video.Name)" -ForegroundColor Green

Write-Host "[2/2] Analizez (10-15 min)..." -ForegroundColor Cyan
& $py -m rea_video decompose $video.FullName --lang en -o out

Write-Host ""
Write-Host "GATA. Deschid raportul..." -ForegroundColor Green
if (Test-Path 'out\report.html') { Start-Process 'out\report.html' } else { Write-Host "Nu gasesc out\report.html" -ForegroundColor Red }
