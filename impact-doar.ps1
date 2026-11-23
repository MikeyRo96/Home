# impact-doar.ps1 - gaseste si instaleaza DOAR fontul Impact (per-utilizator, fara admin).
# Nu repara Windows, nu modifica C:\Windows. Doar copiaza fontul in profilul tau.

$ErrorActionPreference = 'SilentlyContinue'
$RegKey  = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$DestDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$Target  = Join-Path $DestDir 'impact.ttf'

Write-Host "=== Impact: cautare + instalare ===" -ForegroundColor Cyan

# 1) curata eventuala intrare din registru care arata spre un fisier inexistent
$existing = (Get-ItemProperty -Path $RegKey -Name 'Impact (TrueType)').'Impact (TrueType)'
if ($existing -and -not (Test-Path $existing)) {
    Remove-ItemProperty -Path $RegKey -Name 'Impact (TrueType)' -Force
    Write-Host "[curatat] intrare invalida din registru: $existing" -ForegroundColor Yellow
}

# 2) cauta fisierul in locurile probabile
Write-Host "Caut impact.ttf ..."
$candidates = @(
    "C:\Windows\Fonts\impact.ttf",
    "C:\Windows\old\Fonts\impact.ttf",
    "C:\Windows.old\Windows\Fonts\impact.ttf",
    "$env:ProgramFiles\Microsoft Office\root\vfs\Fonts\private\impact.ttf",
    "$env:LOCALAPPDATA\Microsoft\Windows\Fonts\impact.ttf"
)

# WinSxS (component store) - acolo sta copia originala a fonturilor de Windows
Get-ChildItem -Path 'C:\Windows\WinSxS' -Directory -Force -Filter '*impact*' |
    ForEach-Object { $candidates += (Join-Path $_.FullName 'impact.ttf') }

$found = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

# 3) daca nu e nici acolo, scaneaza discurile (poate fi pe stick / alt folder)
if (-not $found) {
    Write-Host "Nu e in locurile standard. Scanez discurile (poate dura 1-3 minute)..." -ForegroundColor Yellow
    $drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Used -gt 0 } | Select-Object -ExpandProperty Root
    foreach ($d in $drives) {
        $found = Get-ChildItem -Path $d -Filter 'impact.ttf' -Recurse -Force |
            Select-Object -First 1 -ExpandProperty FullName
        if ($found) { break }
    }
}

if (-not $found) {
    Write-Host ""
    Write-Host "impact.ttf NU exista pe acest PC." -ForegroundColor Red
    Write-Host "Il iei (exact acelasi fisier) dintr-o singura sursa legitima:"
    Write-Host "  - alt PC cu Windows:  C:\Windows\Fonts\impact.ttf  -> copiezi pe stick"
    Write-Host "  - ISO oficial Windows -> deschizi install.wim cu 7-Zip -> Windows\Fonts\impact.ttf"
    Write-Host "Dupa ce ai fisierul, ruleaza din nou acest script (sau dublu-click pe el)."
    Write-Host ""
    Write-Host "Apasa Enter pentru a inchide..."
    [void](Read-Host)
    exit 1
}

Write-Host "[gasit] $found" -ForegroundColor Green

# 4) instaleaza per-utilizator
New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
Copy-Item -Path $found -Destination $Target -Force
New-Item -Path $RegKey -Force | Out-Null
New-ItemProperty -Path $RegKey -Name 'Impact (TrueType)' -Value $Target -PropertyType String -Force | Out-Null

# 5) incarca fontul in sesiunea curenta, fara logout
Add-Type -Namespace Win32 -Name FontApi -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode)] public static extern int AddFontResourceExW(string f, uint fl, System.IntPtr p);
[DllImport("user32.dll")] public static extern System.IntPtr SendMessageTimeout(System.IntPtr h, uint m, System.UIntPtr w, System.IntPtr l, uint fl, uint t, out System.UIntPtr r);
'@
[void][Win32.FontApi]::AddFontResourceExW($Target, 0, [IntPtr]::Zero)
$res = [UIntPtr]::Zero
[void][Win32.FontApi]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [UIntPtr]::Zero, [IntPtr]::Zero, 0x2, 1000, [ref]$res)

$size = (Get-Item $Target).Length
Write-Host ("[OK] Impact instalat: {0} ({1:N0} KB)" -f $Target, ($size / 1KB)) -ForegroundColor Green
Write-Host "Inchide si redeschide aplicatia (Photoshop / editorul PSD)." -ForegroundColor Cyan
Write-Host ""
Write-Host "Apasa Enter pentru a inchide..."
[void](Read-Host)
