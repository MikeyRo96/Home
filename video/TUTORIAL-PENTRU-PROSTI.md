# O SINGURĂ APLICAȚIE — dublu-click și gata

Un singur fișier de dublu-click: **`RULEAZA.bat`**. El își instalează singur tot (Python, ffmpeg, yt-dlp, rea-video) și apoi îți face analiza.

---

## Ce o să se întâmple, în ordine

1. Descarci un ZIP (43 KB)
2. Îl dezarhivezi
3. Dublu-click pe `RULEAZA.bat`
4. Lipești linkul de YouTube
5. Aștepți 10–20 min (prima dată; apoi 2–5 min)
6. Se deschide un raport în browser
7. Iei fișierul `.xml` și îl pui în FilmCraft

**Atât. Nu instalezi nimic manual. Fără winget. Fără Store. Fără Python instalat de tine.**

---

## Placa video (GTX 1660 Super) — se folosește singură

La primul run, dacă ai placă NVIDIA, `RULEAZA.bat` își instalează **singur**
`onnxruntime-gpu` + bibliotecile CUDA (ca pachete pip, ~2 GB, o singură dată) și
**verifică dacă CUDA chiar merge** — nu se uită doar la o listă.

Ce merge pe placa video: **separarea sunetului** (voce / muzică / efecte) — asta
era 31 din 46 de minute la videoul tău de 19 minute. Restul (tăiatul planurilor,
raportul, proiectul) rămâne pe procesor, pentru că acolo nu ajută GPU-ul.

Trei lucruri care fac diferența la viteză:

| Ce | Înainte | Acum |
|---|---|---|
| Segmente deodată pe placă | 1 (placa pe jumate goală) | **8**; dacă nu încap în 6 GB, scade singur la 4, 2, 1 |
| Al doilea model (efecte, 149 MB) | pe procesor | **pe placă** |
| Citirea textului de pe ecran (OCR) | pe procesor | **pe placă** |
| Thread-uri procesor când merge placa | 8 (furau din analiză) | 1 (normal, placa face treaba) |

Dacă nu ai placă NVIDIA sau driverul e vechi: cade **singur** pe procesor, fără
să te întrebe nimic și fără să se strice. Forțezi CPU din variabilă: `set REA_GPU=0`.

---

## PASUL 1 — Descarcă

Buton direct:

**https://raw.githubusercontent.com/MikeyRo96/Home/arena/5ca47aec-home/video/PACHET-VIDEO-ANALIZA.zip**

Dacă butonul nu merge, deschide:

**https://github.com/MikeyRo96/Home/blob/arena/5ca47aec-home/video/PACHET-VIDEO-ANALIZA.zip** → click pe **Download**

**CE TREBUIE SĂ VEZI:** un fișier `PACHET-VIDEO-ANALIZA.zip` de **23 KB** în folderul `Downloads`.

---

## PASUL 2 — Deblochează și dezarhivează

1. Click dreapta pe ZIP → **Properties**
2. Jos, bifează **Unblock** → **OK**
3. Click dreapta → **Extract All…**
4. Scrie `D:\video` → **Extract**

**CE TREBUIE SĂ VEZI:** în `D:\video` ai `RULEAZA.bat`, `ANALIZA.py` și alte ~11 fișiere.

> De ce Unblock: Windows blochează fișierele venite din internet. Dacă sari pasul, `.bat`-ul poate fi refuzat.

> **Merge din orice disc.** `D:\video`, `C:\VIDEO`, `E:\orice` — codul folosește folderul unde e batu-ul, nu o cale fixă.

---

## PASUL 3 — Dublu-click pe `RULEAZA.bat`

Se deschide o fereastră neagră. Scrie singur:

```
[1/6] Python 3.12 (o singura data, 47 MB)
[2/6] ffmpeg + ffprobe (o singura data, 40 MB)
[3/6] yt-dlp
[4/6] rea-video
[5/6] videoul
[6/6] taieturile
```

**CE TREBUIE SĂ VEZI:** bara de progres în MB la fiecare descărcare.

**Cât durează prima dată:** 10–20 min (descarcă ~150 MB).
**A doua oară:** 2–5 min (nu mai descarcă nimic).

> Nu închide fereastra. Dacă o închizi, o ia de la capăt (dar nu re-descarcă ce are deja).

---

## PASUL 4 — Lipește linkul

Când vezi:

```
  Lipeste linkul YouTube (sau calea unui fisier .mp4)
  si apasa Enter.

  Link/fisier:
```

→ click dreapta în fereastră (lipește automat) → **Enter**.

Exemplu: `https://youtu.be/CI6Iendt0BM`

**CE TREBUIE SĂ VEZI:** `[5/6] videoul` → `descarc de pe YouTube (max 1080p)...` → procente.

---

## PASUL 5 — Rezultatul

La final scrie:

```
==================================================================
  GATA
==================================================================
  RAPORT (shot cu shot) : D:\video\video\analiza-<nume>\report.html
  PROIECT FilmCraft         : D:\video\video\analiza-<nume>\PROIECT.xml
  TAIETURI simple           : D:\video\<nume>.xml
  RAPORT taieturi           : D:\video\<nume>-raport.html
```

Se deschide automat raportul în browser.

**CE TREBUIE SĂ VEZI:** o pagină cu storyboard (poze din video) + lista de tăieturi.

---

## PASUL 6 — FilmCraft: PROIECT ca în Premiere

Când apare raportul, în fereastra neagră scrie:

```
  Vrei sa-l vezi in FilmCraft? (proiect multi-track gata)
  [D]a / [n]u :
```

→ scrie **`d`** → **Enter**

FilmCraft se deschide **cu proiectul deja făcut**.

---

## Ce vezi în FilmCraft — 4 track-uri video + 4 audio

```
V4  ██████ TEXT / SUBTITRARI      ← ce scrie pe ecran (OCR)
V3  ██████ OVERLAY / HUD          ← logo, watermark, template
V2  ██████ GRAFICA                ← particule, bare, cifre, stickere
V1  ██████████████████████ GAMEPLAY  ← imaginea de bază, tăiată în planuri

A4  ▪▪▪▪  ▪▪▪▪  ▪▪▪▪  EFEKTE       ← FIECARE sunet separat
A3  ██████████████████ MUZICA      ← melodia
A2  ██████████████████ VOCE        ← vocea
A1  ██████████████████ MIX         ← sunetul complet
```

| Track | Ce e | De unde vine |
|---|---|---|
| **V1** | fiecare plan, tăiat exact | măsurat (detecție de tăieturi) |
| **V2** | grafică desenată peste fundal | măsurat (pixeli) |
| **V3** | HUD / logo / watermark | măsurat (zonă înghețată) |
| **V4** | text ars în video | măsurat (OCR) |
| **A1** | mixul original | extras din MP4 |
| **A2** | vocea | separată de rea-video |
| **A3** | muzica | separată de rea-video |
| **A4** | **fiecare SFX separat** | tăiat la fiecare impact/whoosh/click |

Plus **markere pe fiecare beat** — vezi unde cad tăieturile pe muzică.

---

## Ce înseamnă [M] și [~] pe fiecare clip

| Marcaj | Înseamnă |
|---|---|
| **[M]** | **măsurat** de rea-video — există dovada |
| **[~]** | inferat din date |
| **[V]** | ar trebui VLM (nu e pornit) |

Un track **gol** e mai cinstit decât unul plin de presupuneri. Dacă n-am găsit text, V4 lipsește.

---

## Fișiere produse

```
D:\video\video\analiza-<nume>\
    PROIECT.xml    ← asta îl pui în FilmCraft (multi-track)
    PROIECT.md     ← raport: ce e pe fiecare track
    report.html    ← analiza shot cu shot
    stems\
        original.wav  vocals.wav  music.wav  effects.wav
        sfx\
            sfx_001_impact.wav  sfx_002_whoosh.wav  ...
```

---

## Ce NU pot afla dintr-un MP4 (nimeni nu poate)

- numele exact al presetării din Premiere
- setările de export (bitrate, codec exact)
- **ordinea exactă** a layerelor din proiectul original
- plugin-urile folosite

Ce **pot**: structura — câte planuri, cât durează fiecare, unde sunt overlay-urile, ce sunete se aud, pe ce beat cad tăieturile.

---

## Dacă ceva nu merge

Rulează **`DIAGNOZA.bat`** (dublu-click). Se deschide `diagnoza.txt`. Trimite-mi-l.

| Ce vezi | Ce faci |
|---|---|
| `winget not recognized` | nu contează, aplicația nu folosește winget |
| `[!] descarcarea a esuat` | video privat / cere cont → încearcă alt link |
| Se închide imediat | dublu-click greșit; rulează `DIAGNOZA.bat` |
| Antivirus blochează | `More info` → `Run anyway` |
| `Python nu s-a instalat` | verifică internetul; rulează din nou |

---

## Ce e testat

| Lucru | Stare |
|---|---|
| Instalare Python + ffmpeg + yt-dlp + rea-video | **testat pe Windows real** (GitHub Actions, PATH golit) |
| Analiză fișier local → `.xml` + `.edl` + `report.html` | **testat, 8/8 fișiere, exit 0** |
| Descărcare YouTube | **testat pe PC-ul tău** — 405 MB, 1080p, OK |
| PROIECT multi-track în FilmCraft | **testat pe Windows real** — 4 video + 4 audio, FilmCraft a stat 25s încărcat |
| SFX separate tăiate | **testat** — 3 fișiere .wav reale pe disc, 3 clipuri pe A4 |
| Markere pe beat | **testat** — 6 markere |
| XML are fps corect + calea video | **testat** — `<pathurl>`, `<timebase>60`, 4 track-uri audio |

---

## Linkuri

| Ce | Link |
|---|---|
| Pachet (ZIP) | `https://raw.githubusercontent.com/MikeyRo96/Home/arena/5ca47aec-home/video/PACHET-VIDEO-ANALIZA.zip` |
| Doar `RULEAZA.bat` | `https://raw.githubusercontent.com/MikeyRo96/Home/arena/5ca47aec-home/video/RULEAZA.bat` |
| Doar `ANALIZA.py` | `https://raw.githubusercontent.com/MikeyRo96/Home/arena/5ca47aec-home/video/ANALIZA.py` |
| Butoane | `https://raw.githubusercontent.com/MikeyRo96/Home/arena/5ca47aec-home/video/DESCARCA-BUTOANE.html` |
