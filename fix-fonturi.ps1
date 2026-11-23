# fix-fonturi.ps1 - instaleaza fonturile lipsa pentru PSD-uri (Windows, fara admin)
# Ruleaza: click dreapta pe fix-fonturi.bat -> "Run as administrator" NU e nevoie.
# Instaleaza per-utilizator (nu modifica instalarea Windows) si anunta aplicatiile
# deschise ca s-a schimbat lista de fonturi (WM_FONTCHANGE).

$ErrorActionPreference = 'Stop'

Add-Type -Namespace Win32 -Name FontApi -MemberDefinition @'
[DllImport("gdi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern int AddFontResourceExW(string lpFileName, uint fl, System.IntPtr pdv);

[DllImport("user32.dll", SetLastError = true)]
public static extern System.IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, System.UIntPtr wParam,
    System.IntPtr lParam, uint fuFlags, uint uTimeout, out System.UIntPtr lpdwResult);
'@

$SrcDir  = Join-Path $PSScriptRoot 'fonts'
$UserDir = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$RegKey  = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'

# nume "de familie" pentru fiecare fisier, asa cum trebuie sa apara in registru
$Fonts = @(
    @{ File = 'BowlbyOneSC-Regular.ttf'; Name = 'Bowlby One SC' },
    @{ File = 'Anton-Regular.ttf';       Name = 'Anton' }         # inlocuitor apropiat pentru Impact
)

if (-not (Test-Path $SrcDir)) { throw "Nu gasesc folderul 'fonts' langa script ($SrcDir)." }
New-Item -ItemType Directory -Force -Path $UserDir | Out-Null
New-Item -Path $RegKey -Force | Out-Null

$installed = @()
foreach ($f in $Fonts) {
    $src = Join-Path $SrcDir $f.File
    if (-not (Test-Path $src)) { Write-Warning "Lipseste $($f.File) - sar peste."; continue }

    $dst = Join-Path $UserDir $f.File
    Copy-Item $src $dst -Force

    $valueName = "{0} (TrueType)" -f $f.Name
    New-ItemProperty -Path $RegKey -Name $valueName -Value $dst -PropertyType String -Force | Out-Null

    # incarca fontul in sesiunea curenta (fara logout)
    [void][Win32.FontApi]::AddFontResourceExW($dst, 0, [IntPtr]::Zero)
    $installed += $f.Name
    Write-Host ("[OK] {0,-16} -> {1}" -f $f.Name, $dst) -ForegroundColor Green
}

# anunta toate aplicatiile ca lista de fonturi s-a schimbat
$res = [UIntPtr]::Zero
[void][Win32.FontApi]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [UIntPtr]::Zero, [IntPtr]::Zero, 0x2, 1000, [ref]$res)

Write-Host ""
Write-Host ("Instalate: {0}" -f ($installed -join ', '))

# Impact: font Microsoft, nu se poate descarca legal - trebuie copiat dintr-un Windows/Office
$impact = Join-Path $env:WINDIR 'Fonts\impact.ttf'
$office = @()
foreach ($base in @(${env:ProgramFiles}, ${env:ProgramFiles(x86)})) {
    if ($base) {
        $p = Join-Path $base 'Microsoft Office\root\vfs\Fonts\private\impact.ttf'
        if (Test-Path $p) { $office += $p }
    }
}

if (Test-Path $impact) {
    Write-Host "[OK] Impact este deja instalat ($impact)" -ForegroundColor Green
} elseif ($office) {
    Write-Host "Impact gasit in Office: $($office[0])" -ForegroundColor Yellow
    Write-Host "Copiaza-l in C:\Windows\Fonts (click dreapta -> Install) si reporneste aplicatia."
} else {
    Write-Host "Impact NU este instalat." -ForegroundColor Yellow
    Write-Host "Copiază impact.ttf dintr-un alt PC cu Windows (C:\Windows\Fonts\impact.ttf)"
    Write-Host "sau din ISO-ul original de Windows (vezi README-FONTURI.md, pasul 2)."
    Write-Host "Pana atunci, Anton (instalat mai sus) e cel mai apropiat inlocuitor vizual."
}

Write-Host ""
Write-Host "Inchide si redeschide aplicatia (Photoshop / editorul PSD) ca sa vada fonturile noi." -ForegroundColor Cyan
Write-Host "Apasa Enter pentru a inchide..."
[void](Read-Host)
