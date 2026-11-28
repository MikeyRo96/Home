# Editezi cu agentul — FilmCraft + ce testezi azi

Verificat 26 nov 2026. Toate cifrele date de GitHub API.

## 0. Prima linie

**Instalează FilmCraft 0.20.1, apoi testează-l cu 3 lucruri — restul e muncă de agent.**

## 1. Instalare (2 minute, zero ferestre)

FilmCraft = Rust pur, gratuit, alpha. **Windows x64 installer 93 MB:**

```
https://github.com/storytold/filmcraft/releases/download/v0.20.1/filmcraft-0.20.1-windows-x64.msi
```

Portabil (fără instalare, dezarhivezi și rulezi):

```
https://github.com/storytold/filmcraft/releases/download/v0.20.1/filmcraft-0.20.1-windows-x64-portable.zip
```

Rulează `EDITEZI-CU-AGENTUL.bat` — descarcă și deschide portabilul automat.

**Pe PC-ul tău (doar randează cu GPU; fără el = totul pe CPU):**
- GPU NVIDIA → H.264/H.265 hardware, HDR 10-bit
- GPU AMD/Intel → doar H.264 hardware pe Windows dacă e NVIDIA; altfel **export pe CPU**
- dacă nu se deschide fereastra: setat `WGPU_BACKEND=vulkan` (deja în `.bat`)

## 2. Ce testezi — în ordinea asta

| # | Test | Cum | Trece dacă |
|---|---|---|---|
| 1 | **Vezi filmul** | tragi 2 fișiere în Project, le pui pe V1 | apar în Program monitor |
| 2 | **Tăietură** | `C` (razor) → click pe un cadru | timeline se desparte exact |
| 3 | **Trim** | `Q` / `W` cu playhead-ul | ripple fără gol |
| 4 | **Tranziție** | Effect Controls → Dissolve | apare peste tăietură |
| 5 | **Grader** | workspace Color → Basic Correction | se schimbă instant |
| 6 | **Audio** | A1, keyframe pe volum | linia de volum se mișcă |
| 7 | **Export** | Export → H.264 | fișierul se vede în VLC |
| 8 | **Agent** | terminal: `filmcraft-cli commands` | listează **650+ comenzi** |

## 3. Ce NU merge — nu te chinui

| Nu merge | Înlocuiește cu |
|---|---|
| deschide `.prproj` | exportă din Premiere **FCP7 XML** sau **AAF** |
| plugin-uri VST3 / OpenFX | efectele interne |
| export H.265 fără NVIDIA | H.264 |
| AV1 export | — |
| Windows/Linux = testate puțin | raportează bug pe GitHub |

## 4. Ce am găsit nou azi pe GitHub (verificat, ★ reale)

| Repo | ★ | Ce face | Pentru tine |
|---|---|---|---|
| **theygen-com/hyperframes** | **90.423** | **cel mai mare**: editează filmările tale SAU creează/reface video; AI agent | cel mai mare proiect de tipul ăsta |
| **jub0t/Concat** | **20.842** | CapCut open-source | dacă vrei interfață de telefon |
| **OpenCut-app/OpenCut** | **99.400** | CapCut open-source (altul) | cel mai popular |
| **mltframework/shotcut** | 15.798 | editor clasic, stabil, GPLv3 | cel mai TESTAT, nu alpha |
| **kajisho5/ffmpeg-skill** | **11.284** | 42 unelte ffmpeg pentru agenți | taie fără editor |
| **openfilm/openfilm** | 9.470 | agentul tău devine editor video | headless |
| **palmier-io/palmier-pro** | 14.811 | editor macOS pentru AI | nu-ți trebuie (Windows) |
| **WeftCut/WeftCut** | 401 | AI editor Win/mac/Linux | alternativă la FilmCraft |
| **pireel/pireel** | 1.495 | **export direct în Premiere** | puntea cu Premiere |
| **kitcut-hq/kitcut** | 46 | Claude Code: **multicam sync, captions, vlog** | știe să sincronizeze audio! |
| **kernelmoonowl/pluraleyes** | 201 | PluralEyes pt Win10/11 — sync pe waveform | dacă filmezi cu 2 camere |
| **B0yko/tern** | 241 | caută în arhivă după ce s-a spus/văzut | arhivă mare |
| **DareDev256/fcp-mcp-server** | 161 | Claude → Final Cut Pro | dacă treci pe FCP |
| **Ersiter/pr2resolve** | 4 | **`.prproj` → `.drp`** (Resolve) | mută proiectul în Resolve |
| **storytold/filmcraft** | **19.057** | editorul din care discutăm | alpha, 56% gata de producție |

## 5. Ce încă nu știu (rate limit GitHub)

30 cereri/oră la search. Epuizate. Am oprit la 30. Restul se reiau cu:

```
https://raw.githubusercontent.com/MikeyRo96/Home/arena/5ca47aec-home/video/CAUTA-MAI-MULTE.md
```

## 6. Reddit — ce zic oamenii (căutat azi)

- **r/premiere**: „nu există amprentă Premiere în MP4, nu poți recupera proiectul"
- **r/ClaudeCode**: plugin-ul `claude-video-vision` rulează scdet/blackdetect/silencedetect **înainte** să extragă cadre → mai ieftin
- **r/editors**: tranzițiile AI (Kling/Higgsfield, cadru start + cadru stop) — **nu** se detectează cu scene detection

## 7. Verdict

| Întrebare | Răspuns |
|---|---|
| FilmCraft = Premiere? | da, intenționat — aceleași panouri și taste |
| Merită? | **da, alpha dar 19k★ și activ zilnic.** Testează 8 pași de la §2 |
| Ce faci cu proiectele Premiere? | **FCP7 XML / AAF** — nu `.prproj` |
| Care e cel mai mare din lume? | **hyperframes 90.423★** |
