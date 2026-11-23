# ia-impact.ps1 - descarca si instaleaza DOAR fontul Impact (Windows 10/11, fara admin).
# Sursa: Microsoft TrueType core fonts for the Web (impact32.exe, redistribuibil gratuit).
# Nu repara Windows si nu scrie nimic in C:\Windows - instaleaza per-utilizator.

$ErrorActionPreference = 'Stop'
$Url     = 'https://downloads.sourceforge.net/project/corefonts/the%20fonts/final/impact32.exe'
$Work    = Join-Path $env:TEMP 'impact-setup'
$DestDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$RegKey  = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'

Write-Host "=== Impact: download + instalare (per-utilizator) ===" -ForegroundColor Cyan

# 0) curata intrarea invalida din registru, daca a ramas de la o incercare anterioara
$cur = (Get-ItemProperty -Path $RegKey -Name 'Impact (TrueType)' -ErrorAction SilentlyContinue).'Impact (TrueType)'
if ($cur -and -not (Test-Path $cur)) {
    Remove-ItemProperty -Path $RegKey -Name 'Impact (TrueType)' -Force -ErrorAction SilentlyContinue
    Write-Host "[curatat] intrare invalida in registru: $cur" -ForegroundColor Yellow
}

# 1) descarca impact32.exe
New-Item -ItemType Directory -Force -Path $Work | Out-Null
$exe = Join-Path $Work 'impact32.exe'
if (-not (Test-Path $exe)) {
    Write-Host "Descarc impact32.exe de la SourceForge (Microsoft core fonts)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $Url -OutFile $exe -UseBasicParsing
}
Write-Host ("[ok] {0} ({1:N0} KB)" -f $exe, ((Get-Item $exe).Length / 1KB))

# 2) taie arhiva CAB din interiorul self-extractorului (semnatura 'MSCF')
$bytes = [IO.File]::ReadAllBytes($exe)
$idx = -1
for ($i = 0; $i -le $bytes.Length - 4; $i++) {
    if ($bytes[$i] -eq 0x4D -and $bytes[$i+1] -eq 0x53 -and $bytes[$i+2] -eq 0x43 -and $bytes[$i+3] -eq 0x46) { $idx = $i; break }
}
if ($idx -lt 0) { throw "Nu am gasit arhiva CAB (MSCF) in impact32.exe." }

$cab = Join-Path $Work 'impact.cab'
$fs = [IO.File]::Create($cab)
$fs.Write($bytes, $idx, $bytes.Length - $idx)
$fs.Close()
Write-Host ("[ok] CAB extras la offset {0}" -f $idx)

# 3) extrage TTF-ul cu expand.exe (built-in)
$outDir = Join-Path $Work 'fonts'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
& expand.exe $cab -F:* $outDir | Out-Null
$ttf = Get-ChildItem $outDir -Filter '*.ttf' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ttf) { throw "expand.exe nu a produs niciun .ttf. Incearca 7-Zip pe impact32.exe (Extract Here)." }
Write-Host ("[ok] {0} ({1:N0} KB)" -f $ttf.Name, ($ttf.Length / 1KB))

# 4) instaleaza per-utilizator
New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
$target = Join-Path $DestDir 'impact.ttf'
Copy-Item $ttf.FullName $target -Force
New-Item -Path $RegKey -Force | Out-Null
New-ItemProperty -Path $RegKey -Name 'Impact (TrueType)' -Value $target -PropertyType String -Force | Out-Null

# 5) anunta aplicatiile ca lista de fonturi s-a schimbat
Add-Type -Namespace Win32 -Name FontApi -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode)] public static extern int AddFontResourceExW(string f, uint fl, System.IntPtr p);
[DllImport("user32.dll")] public static extern System.IntPtr SendMessageTimeout(System.IntPtr h, uint m, System.UIntPtr w, System.IntPtr l, uint fl, uint t, out System.UIntPtr r);
'@
[void][Win32.FontApi]::AddFontResourceExW($target, 0, [IntPtr]::Zero)
$res = [UIntPtr]::Zero
[void][Win32.FontApi]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [UIntPtr]::Zero, [IntPtr]::Zero, 0x2, 1000, [ref]$res)

Write-Host ""
Write-Host ("[OK] Impact instalat: {0}" -f $target) -ForegroundColor Green
Write-Host "Inchide complet aplicatia (Photoshop / editorul PSD) si redeschide-o." -ForegroundColor Cyan
Write-Host ""
Write-Host "Apasa Enter pentru a inchide..."
[void](Read-Host)
