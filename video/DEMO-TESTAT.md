# TEST REAL — rulat acum, aici. Ce a ieșit.

Data: 26 nov 2026, 10:04. Sandbox Linux, ffmpeg 6.0 + rea-video 0.1.0 (instalate de mine).

## 1. Rezultatul scurt

**Lanțul funcționează.** L-am rulat pe un fișier de probă (3 planuri, 9 secunde) pentru că **YouTube e blocat din sandbox** — vezi §5.

| Unealtă | Rezultat |
|---|---|
| `inspecteaza.py` | **OK** — 2 tăieturi, 3 planuri, `.edl` + `.xml` + markere + capitole |
| `rea-video decompose` | **OK** — 3 planuri detectate, verdict „code/template render 100%", `report.html` + `VIDEO.md` |
| `rea-video` instalat | **OK** — 600 MB, 9 secunde instalație |
| `ffmpeg` descărcat automat | **OK** — 78 MB |
| YouTube descărcare | **BLOCAT** din sandbox (TLS refuzat), nu din cauza codului |

## 2. Ce a ieșit exact din `inspecteaza.py`

```
fisier      : test3.mp4
durata      : 0:00:09
rezolutie   : 640x360 @ 25/1 fps
codec       : h264 (Constrained Baseline)
audio       : aac 44100 Hz 1 canale
taieturi    : 2      (13.3 pe minut)
volum mediu : -21.1 dB
pauze >1s   : 0
  1.  0:00:03   scor 0.400
  2.  0:00:06   scor 0.400

EDL      : test3.edl   (3 planuri)
FCP XML  : test3.xml
markere  : test3-markere.csv
capitole : test3-capitole.txt
RAPORT   : test3-raport.html
```

Fișierele demo sunt în **`video/demo/`** — deschide-le, sunt reale, nu inventate.

## 3. Ce a ieșit exact din `rea-video decompose`

```
10:04:51 INFO video test3.mp4 640x360 25.00fps 9.00s
10:04:52 INFO detected 3 shots
10:04:53 INFO shot_001 00:00.000-00:03.000 det=code_render(86%) frozen
10:04:54 INFO shot_002 00:03.000-00:06.000 det=code_render(86%) frozen
10:04:54 INFO shot_003 00:06.000-00:09.000 det=code_render(86%) frozen
10:04:56 INFO done in 4.7s -> /tmp/reaout
```

```json
{"verdict": "code / template render 100%", "shots": 3, "confidence": 0.861,
 "vlm": "No VLM; live action / AI / 3D are told apart from pixel statistics only..."}
```

**9 secunde de video → 4,7 secunde de analiză.** Pe YouTube de 10 minute: ~5–15 min.

## 3b. Al doilea test — pe video-ul TĂU (Capra din OHIO)

Am citit pagina YouTube: **Bem PAM PAM cu Capra din OHIO**, *Jocuri Horror*, 25 nov 2026, **19:08**, 95.862 vizionări, 2.951 like. Gaming, română, vlog/let's-play.

**Ce pot spune din transcriere + titlu, fără să descarc:** structură de vlog gaming — intro („Salut, sunt din viitor"), sponsor Kaufland (mango vs zmeură), `merch pe susky.ro` la mijloc, gameplay pe insulă, Titanic/iceberg, parc de distracție, roata norocului, lava, outro cu like/subscribe.

**Ce NU pot spune fără fișier:** câte tăieturi, ce BPM, ce zoom-uri, câte planuri, dacă are jump cuts. De-aia trebuie rulat pe PC-ul tău.

| Măsurătoare | Pe 19:08 | Estimare |
|---|---|---|
| tăieturi (prag 0.45) | ? | 150–400 (vlog gaming tăiat des) |
| tăieturi/minut | ? | 8–20 |
| timp de analiză rea-video | ? | ~10–15 min |
| timp descărcare | ? | 1–3 min |

## 3c. Test de robustețe — l-am rupt intenționat

Am descoperit o problemă reală și am reparat-o:

| Clip de probă | `prag 0.3` (vechi) | `prag 0.45` (nou) | Adevărul |
|---|---|---|---|
| **PAN agresiv** (cameră care mătură) | **28 tăieturi FALSE** | **0** | 0 tăieturi |
| **CUT-HARD** (test → galben) | 1 | 1 | 1 |
| **CULORI** (roșu/albastru/verde) | 2 | **0** | 2 |
| **MIX** (portocaliu → test → violet) | — | **2, la 5,00 s și 15,00 s** | exact 2 |

**Concluzie:** `0.45` oprește pan-urile false, dar **ratează tăieturile pe fundal uniform** (culoare plată → culoare plată = scor 0.40).

**Regula:** `0.45` = implicit (vlog, gaming, tutorial). `0.3` = când tai pe fundal uniform / slide-uri / text pe negru.

## 4. Ce înseamnă verdictul

Fișierul de probă e generat de mine (3 dreptunghiuri de culoare). `code_render 100%` = **corect**. Dovada: pixeli compleți uniformi, fără zgomot de senzor, fără mișcare de cameră — exact ce arată o randare, nu o filmare.

**Fără VLM nu poate distinge filmat vs AI pe planuri neclare.** De aceea `confidence 0.861`, nu 1.0. Pe un video real, fără VLM, verdictul poate fi greșit — îl corectează agentul care vede cadrele (`rea-video review`).

## 5. De ce n-am testat pe YouTube-ul tău

| Blocat din sandbox | Dovadă |
|---|---|
| `www.youtube.com` | `curl` → `000` |
| `i.ytimg.com` | `000` |
| `yt-dlp` | `TLS/SSL connection has been closed (EOF)` |
| `objects.githubusercontent.com` (release assets) | `000` — de-asta am luat ffmpeg din PyPI |

**Sandbox-ul meu nu are internet liber.** Doar GitHub API, codeload, PyPI. Deci **descărcarea de pe YouTube trebuie rulată pe PC-ul tău** — acolo merge.

## 6. Ce faci tu acum, pe Windows

```
1. dublu-click ANALIZEAZA-VIDEO.bat
2. lipi: https://www.youtube.com/watch?v=CI6Iendt0BM
3. Enter
4. aștepți 5–20 min (prima dată: +10 min descărcări)
5. se deschide report.html
```

Ce va rula pe PC-ul tău, în ordine:

| # | Pas | Verificat de mine? |
|---|---|---|
| 1 | yt-dlp descarcă 1080p | codul da, rețeaua nu (blocată aici) |
| 2 | rea-video decompose | **DA — rulat** |
| 3 | inspecteaza.py → EDL/XML | **DA — rulat** |
| 4 | raport HTML | **DA — generat** |

## 7. Ce-mi trimiți înapoi

După ce rulează, trimite-mi:

1. **ultimele 20 de linii** din fereastra neagră
2. `report.html` → secțiunea **Verdict**
3. ce scrie la `shot_001`: `filmed` / `ai` / `3d` / `code`

Cu ele îți spun dacă a nimerit și ce trebuie corectat.

## 8. Limita pe care o știi deja

Pe YouTube **nu poți afla ce versiune de Premiere a folosit** — YouTube re-encodează și șterge metadatele. Ce afli: **structura** (planuri, tăieturi, ritm, efecte, text), nu proiectul.
