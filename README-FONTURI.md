# Fonturi lipsă pentru PSD — rezolvare rapidă (Windows)

Mesajul `Opened Untitled.psd with 2 warnings: font 'Impact' is not installed; ...` nu e o eroare:
PSD-ul s-a deschis, dar layerele de text cer fonturile **Impact** și **Bowlby One SC**, care lipsesc
în Windows-ul tău modificat. Textul e afișat cu un font de rezervă, deci arată diferit.

Rezolvarea completă = instalezi ambele fonturi. Durează ~2 minute.

---

## Pasul 1 — Bowlby One SC (automat, 10 secunde)

1. Descarcă folderul repo-ului (sau doar `fix-fonturi.bat` + `fix-fonturi.ps1` + folderul `fonts/`).
2. Dublu-click pe **`fix-fonturi.bat`**.
3. Gata. Fontul e instalat per-utilizator (în `%LOCALAPPDATA%\Microsoft\Windows\Fonts`),
   fără drepturi de admin, fără să modifici instalarea Windows.
   Scriptul instalează și **Anton** — cel mai apropiat înlocuitor vizual pentru Impact,
   ca PSD-ul să nu mai arate strâmb până faci pasul 2.

Alternativa manuală: click dreapta pe `fonts\BowlbyOneSC-Regular.ttf` → **Install**.

## Pasul 2 — Impact (font Microsoft, trebuie adus din afara)

Impact **nu** e open-source și nu se poate descărca legal de pe site-uri de fonturi.
Ia fișierul `impact.ttf` dintr-o sursă legitimă:

**Varianta A — de pe alt PC cu Windows** (cel mai rapid)
```
C:\Windows\Fonts\impact.ttf
```
Copiază fișierul, apoi click dreapta → **Install** (sau dublu-click → *Install*).

**Varianta B — din Office**, dacă ai Office instalat:
```
C:\Program Files\Microsoft Office\root\vfs\Fonts\private\impact.ttf
```

**Varianta C — din ISO-ul original de Windows** (curat, dacă ai o imagine oficială):
```powershell
# rulează într-un PowerShell deschis ca Administrator
dism /Mount-Wim /WimFile:D:\sources\install.wim /Index:1 /MountDir:C:\mnt
# sau, pentru install.esd:
# dism /Mount-Wim /WimFile:D:\sources\install.esd /Index:1 /MountDir:C:\mnt
copy C:\mnt\Windows\Fonts\impact.ttf C:\Windows\Fonts\
dism /Unmount-Wim /MountDir:C:\mnt /Discard
```

## Pasul 3 — repornește aplicația

Photoshop / editorul PSD ține lista de fonturi în memorie. Închide-l complet și redeschide-l;
apoi redeschide `Untitled.psd`. Warning-urile dispar și textul arată identic cu originalul.

---

## Dacă vrei „exact același" și pe alt PC

Dacă trimiți PSD-ul altcuiva, nu te baza pe fonturi instalate la destinație:

- **Photoshop:** Layer → Type → **Convert to Shape** (sau *Rasterize Type*) pentru layerele cu Impact / Bowlby One SC, apoi salvezi.
- Sau lipește fonturile lângă PSD într-un folder și instalează-le la destinație cu același script.

## Fișiere

| Fișier | Ce e |
|---|---|
| `fix-fonturi.bat` | dublu-click → instalează fonturile |
| `fix-fonturi.ps1` | logica de instalare (per-user + WM_FONTCHANGE) |
| `fonts/BowlbyOneSC-Regular.ttf` | Bowlby One SC (Google Fonts, licență OFL) |
| `fonts/Anton-Regular.ttf` | Anton — înlocuitor pentru Impact (Google Fonts, OFL) |
| `fonts/OFL-*.txt` | licențele fonturilor |

Impact rămâne proprietatea Microsoft — de aceea nu e inclus aici.
