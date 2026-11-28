# -*- coding: utf-8 -*-
# Instaleaza Python 3.12 portabil (fara winget, fara Store, fara admin)
$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

$dir = Join-Path $env:LOCALAPPDATA 'py312'
$exe = Join-Path $dir 'python.exe'

if (Test-Path $exe) {
    Write-Host "Python deja instalat: $exe" -ForegroundColor Green
    & $exe --version
    exit 0
}

$url = 'https://github.com/astral-sh/python-build-standalone/releases/download/20261124/cpython-3.12.16+20261124-x86_64-pc-windows-msvc-install_only.tar.gz'
$tgz = Join-Path $env:TEMP 'py312.tgz'
$tmp = Join-Path $env:TEMP 'py312x'

Write-Host "[1/3] Descarc Python 3.12 (47 MB)..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $url -OutFile $tgz
Write-Host "      descarcat: $((Get-Item $tgz).Length) bytes"

Write-Host "[2/3] Dezarhivez..." -ForegroundColor Cyan
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
tar.exe -xzf $tgz -C $tmp

Write-Host "[3/3] Instalez in $dir ..." -ForegroundColor Cyan
if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Copy-Item -Recurse -Force (Join-Path $tmp 'python\*') $dir
Remove-Item -Recurse -Force $tmp
Remove-Item -Force $tgz

Write-Host ""
Write-Host "GATA. Python 3.12:" -ForegroundColor Green
& $exe --version
Write-Host "Loc: $exe"
Write-Host ""
Write-Host "Python e gata. Aplicatia isi instaleaza singura restul." -ForegroundColor Yellow
