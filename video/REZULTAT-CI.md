# Testat pe Windows real (GitHub Actions runner) — 26 nov 2026

Workflow: `.github/workflows/test-video-bat.yml` · run `45836857179` · **toate verzi**.

| Test | Ce verifică | Rezultat |
|---|---|---|
| 1 | `PORTHON.bat` descarcă Python 3.12 de pe GitHub | **TRECUT** |
| 2 | ffmpeg din `imageio-ffmpeg` | **TRECUT** |
| 3 | `yt-dlp.exe` descărcat + video de test generat | **TRECUT** |
| 4 | `inspecteaza.py` pe video real → `.xml`, `.edl` | **TRECUT** |
| 5 | `2-GASESTE-TAIETURILE.bat` end-to-end | **TRECUT** |

## Ce s-a rupt și am reparat (pe Windows real, nu ghicit)

| Bug | Simptom | Fix |
|---|---|---|
| `)` în `echo` | `FFPROBE` apărea de 2 ori, `if` închis prematur | `^(` `^)` escapate |
| `$env:TEMP` în PowerShell | `Missing closing '}'` | scos, `%TEMP%` din cmd |
| `%2B` în URL | PowerShell parsea greșit | `+` literal |
| `ffprobe.exe` fals | copiam ffmpeg ca ffprobe | **nu mai copiez**; `inspecteaza.py` are plan B |
| `inspecteaza.py` fără ffprobe | „ffprobe a esuat" | parsez `ffmpeg -i` |
| `choice` fără timeout | se bloca în runner | `/n /t 20 /d 1` |
| `pause` | returna errorlevel 1 → CI roșu | `pause>nul` |

**Ce nu am putut testa pe runner:** descărcarea de pe YouTube (Google blochează IP-urile de datacenter).
Asta merge doar pe PC-ul tău.

## Ce faci acum

```
FACETOT.bat  ->  lipi linkul  ->  Enter
```

Dacă pică, rulează `DIAGNOZA.bat` și trimite-mi `diagnoza.txt`.
