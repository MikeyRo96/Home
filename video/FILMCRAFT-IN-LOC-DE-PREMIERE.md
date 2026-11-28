# FILMCRAFT în loc de Premiere — + tăieturile scoase din orice video

Verificat 26 nov 2026. Comenzile și flag-urile sunt luate din cod, nu din memorie.

## 1. Decizia

| | Premiere | **FilmCraft** |
|---|---|---|
| Preț | abonament | **0** |
| Editor | da | da |
| Agent | nu | **650+ comenzi + MCP** |
| Import EDL / XML / OTIO / AAF | da | **da** |
| Deschide `.prproj` | da | **NU** |
| Plugin-uri VST3 / OpenFX | da | **NU** |
| Export H.265 | da | doar cu NVIDIA |
| Stabilitate | matur | **alpha, 56% gata de producție** |
| Windows testat | mult | **puțin** |

**Verdict: da, folosește FilmCraft — dar ține Premiere instalat până treci de cele 8 teste din `EDITEZI-CU-AGENTUL.md`.**

## 2. Lanțul complet — de la YouTube la timeline

```
[1] ANALIZEAZA-VIDEO.bat        link YouTube -> video.mp4 + rea-video report.html
[2] python inspecteaza.py video.mp4
        -> video.edl           (tăieturi, CMX3600)
        -> video.xml           (FCP7 XML, xmeml v4)
        -> video-markere.csv
        -> video-capitole.txt  (pentru descrierea YouTube)
[3] FilmCraft -> File > Import -> video.xml
        -> 4 planuri pe timeline, cu nume plan_001..plan_00N
[4] tai, gradez, export H.264
```

## 3. Ce am schimbat în `inspecteaza.py`

Acele 4 fișiere se scriu **automat** la fiecare rulare. Nu mai trebuie flag.

| Fișier | Format | Intră în |
|---|---|---|
| `NUME.edl` | CMX 3600, 25 fps non-drop | Premiere, Resolve, FilmCraft |
| `NUME.xml` | FCP7 XML (xmeml v4) | **FilmCraft**, Premiere, Resolve |
| `NUME-markere.csv` | `time_seconds,score` | Excel / scripturi |
| `NUME-capitole.txt` | `0:00 Plan 1` | descrierea YouTube |

Flag-uri noi (opționale): `--edl` `--fcpxml` `--markere` `--capitole`.

**Testat:** generatoarele rulate cu date de probă → EDL valid, XML valid (`xml.dom.minidom` OK), 4 planuri.

**Limita EDL/XML:** sunt **planuri pe axa goală**, nu filmările originale. Pentru relink la surse ai nevoie de fișierele originale. FilmCraft importă XML ca atare; dacă vrei să înlocuiești planul cu filmarea ta, tragi fișierul peste el.

## 4. Cum imporți în FilmCraft (exact)

1. Deschide FilmCraft (`EDITEZI-CU-AGENTUL.bat`)
2. `File ▸ Import ▸ …` → alege `NUME.xml` **sau** `NUME.edl`
3. secvența apare în bin
4. dublu-click pe secvență → timeline
5. înlocuiești planurile cu filmările tale (drag peste)

**Nu** folosi `Open Project` — `.fcproj` e altceva. Import, nu Open.

## 5. Ce NU face FilmCraft (verificat în README)

| Nu face | Alternativă |
|---|---|
| deschide `.prproj` | exportă din Premiere **FCP7 XML** / **AAF** / **OTIO** |
| plugin-uri | efectele interne |
| AV1 export | — |
| H.265 fără GPU NVIDIA | H.264 |
| scene detection nativ | **`inspecteaza.py`** (îl faci tu, în 10 s) |

## 6. Alternativa la FilmCraft, dacă alpha te enervează

| Program | ★ | De ce |
|---|---|---|
| **mltframework/shotcut** | 15.798 | **cel mai testat**, GPLv3, importă EDL/XML |
| **KDE/kdenlive** | 6.191 | matur, Linux/Windows |
| **WeftCut/WeftCut** | 401 | agent MCP, activ |
| **pireel/pireel** | 1.495 | export timeline **în Premiere** |
| **storytold/filmcraft** | 19.057 | cel mai ambițios, alpha |

## 7. Ce faci azi, concret

1. `EDITEZI-CU-AGENTUL.bat` → instalează FilmCraft
2. testează 8 pași din `EDITEZI-CU-AGENTUL.md` §2
3. ia un video de pe YouTube → `ANALIZEAZA-VIDEO.bat`
4. `python inspecteaza.py video.mp4` → iese `.xml`
5. FilmCraft → `File ▸ Import` → `.xml`
6. spune-mi la ce pas s-a rupt
