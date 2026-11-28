# Ce faci, în ordine. 3 dublu-click-uri.

## Pasul 1 — 20 secunde

**`1-TESTEAZA-ASTA.bat`** — dublu-click.

Nu descarcă nimic. Îți scrie:

```
REZULTAT: X OK / Y lipsă
```

- `PYTHON` — dacă lipsește, îți deschide magazinul Microsoft. **Singurul pe care îl pui de mână.**
- `FFPROBE`, `YT-DLP` — le descarcă pasul 2 singur.
- `INTERNET` — dacă pică, nu continuăm.

## Pasul 2 — 15–25 minute

**`ANALIZEAZA-VIDEO.bat`** — dublu-click → lipi linkul YouTube → Enter.

Îți spune cum e făcut video-ul, plan cu plan. Iese `report.html`.

## Pasul 3 — 60 secunde → FilmCraft

**`2-GASESTE-TAIETURILE.bat`** — tragi peste el fișierul `.mp4` (îl descarcă pasul 2).

Întreabă ce tip de video e:
- `[1]` vlog / gaming / tutorial
- `[2]` slide-uri / fundal uniform

Iese:

```
video.xml      <- importi in FilmCraft
video.edl      <- alternativa
video-raport.html
```

Apoi în FilmCraft: **File → Import → video.xml**. Nu `Open Project`.

## Ce obții la final

| Fișier | Ce e |
|---|---|
| `report.html` (pas 2) | cum e făcut fiecare plan + plan de refacere |
| `video.xml` (pas 3) | **tăieturile lui, pe timeline, la cadru** |
| `video.edl` | același lucru pentru Premiere/Resolve |
| `video-capitole.txt` | capitole pentru descrierea YouTube |

## Ce NU se poate

**Nu poți scoate proiectul Premiere din MP4.** Nu există. Ce ai: structura, nu fișierul.

**Nu poți face 1:1 conținutul** — jocul, fața, vocea lui nu sunt în MP4. Ai 1:1 **structura**.

## Dacă ceva pică

Trimite-mi:

1. ce scrie la `REZULTAT` (pasul 1)
2. ultimele 20 de linii din fereastra neagră (pasul 2 sau 3)

Eu îți spun exact ce e rupt.
