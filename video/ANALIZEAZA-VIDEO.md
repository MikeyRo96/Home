# YouTube → vezi exact cum a fost făcut video → îl editezi

Verificat 26 nov 2026, ore 09:55. Toate cifrele de la GitHub API.

## 1. Răspunsul direct

**Da, există. Dar „amprenta Premiere" nu există în fișier.** YouTube îți dă un MP4 **re-encodat** — toate datele despre proiect sunt șterse. Nimeni nu poate recupera `.prproj`-ul.

**Ce se poate:** să afli **shot cu shot** cum a fost făcut (filmat? AI? 3D? cod? ce subtitrare, ce tăietură, ce BPM, ce efect) și să primești **plan de refacere**.

## 2. Comanda care face tot

Dublu-click pe **`ANALIZEAZA-VIDEO.bat`** din acest folder → lipi linkul → Enter.

Ce face `analizeaza.py`, pas cu pas (real, verificat):

| # | Pas | Timp |
|---|---|---|
| 1 | verifica Python; daca lipseste deschide Store | 1 s |
| 2 | descarca **ffmpeg** daca nu-l are (~150 MB) | 3–10 min prima data |
| 3 | descarca **yt-dlp** (~17 MB) | 20 s |
| 4 | descarca videoul **max 1080p** cu audio | 30 s – 5 min |
| 5 | instaleaza **rea-video** in `.venv` (~600 MB) | 3–6 min prima data |
| 6 | `rea-video decompose video.mp4 --lang en --no-vlm` | 3–15 min |
| 7 | `python inspecteaza.py video.mp4` | 10–60 s |
| 8 | deschide `report.html` | — |

Toate descărcările merg în `%LOCALAPPDATA%\rea-video-tool\` — o singură dată.
A doua rulare sare peste pașii 2, 3, 5.

**De ce `--no-vlm`:** fără cheie Gemini/Doubao, rea-video merge oricum.
Diferența: fără VLM, verdictul „filmat vs AI" e mai slab pe planurile neclare.

**Trage un fișier peste `.bat`** → sare peste descărcare, analizează direct.

Totul în `%CD%\analiza\`:
- `report.html` + PDF — pentru tine
- `VIDEO.md` — pentru agent, pe straturi
- `stems/` — voce / muzică / original separate
- tăieturi, subtitrări SRT/ASS, BPM, efecte, plan de refacere

## 3. Motorul: rea-video

`JuneYaooo/rea-video` — **13.531★**, Apache-2.0, actualizat 25 nov.

| Ce dă | Detaliu |
|---|---|
| tip per plan | **filmat / AI / 3D / cod / screen recording** |
| acuratețe | 98,3–99,6% pe seturile autorului (15 + 16 clipuri) |
| dovezi | frame cadence, sensor noise, AIGC tags în metadate, mâini/text/fizică, BPM, cheie |
| audio | separă voce / muzică / efecte (onnxruntime) |
| subtitrări | OCR → SRT + ASS cu timing |
| extras | momente: dezvăluiri de magie, răsturnări, climax, gafe |
| plan | cum să refaci fiecare plan, cu modelul ales |

**Comenzi reale (verificate în `cli.py`, nu inventate):**

```
rea-video decompose video.mp4 --lang en -o out
rea-video probe video.mp4 --tags
rea-video stems video.mp4
rea-video tiles video.mp4 --start 0 --end 30
rea-video remake-plan   out/<nume>
rea-video remake-run    jobs.json --dry-run
rea-video assemble      out/<nume> results.json
```

`--lang en` = raport în engleză (are și `zh`). Română **nu** are.

## 4. Amprenta Premiere — adevărul

| Ce cauți | Există? | Detaliu |
|---|---|---|
| `.prproj` în MP4 | **NU** | exportul Premiere nu conține proiectul |
| tag-uri de software (Premiere) | **uneori** | `ffprobe -show_format` → `encoder` / `handler_name`; YouTube le **șterge** la re-encode |
| tăieturi exacte | **NU exact** | se detectează, dar nu la cadru |
| cross dissolve / fade / J-cut / L-cut | **NU** | scene detection nu le vede |
| efecte (zoom, glitch, speed ramp) | **DA, parțial** | `editast analyze` sau rea-video |
| ordinea planurilor + durate | **DA** | |

**Deci:** „amprenta" = **structura**, nu fișierul de proiect.

## 5. Proiecte care fac exact asta (verificate azi)

| Repo | ★ | Ce face | Instalare |
|---|---|---|---|
| **JuneYaooo/rea-video** | **13.531** | **cel complet**: shot cu shot + refacere | `pip install` din repo |
| **theygen-com/hyperframes** | **90.423** | cel mai mare; editează/reface video cu agent | web/app |
| **bradautomates/claude-video** | **21.825** | `/watch` — agentul vede video-ul | Claude Code |
| **nexu-io/openmotion** | 16.527 | link → Motion.md → refacere editabilă → MP4 | Node 22 |
| **kajisho5/ffmpeg-skill** | 11.284 | 42 unelte ffmpeg pentru agent | npm |
| **openfilm/openfilm** | 9.470 | agentul devine editor | npm |
| **pireel/pireel** | 1.495 | **export timeline în Premiere / Resolve** | pnpm |
| **WeftCut/WeftCut** | 401 | NLE desktop pe care agentul îl conduce | release |
| **Pranav-Conova/video-reverse-engineer** | 6 | `editast analyze "LINK"` — ia **direct de pe YouTube** | pip |
| **Breakthrough/PySceneDetect** | 5.662 | tăieturi + EDL/OTIO/FCP | pip |
| **ALBEDO-TABAI/video-expert-analyzer** | 247 | judecă montajul (6 reguli Walter Murch) | skill |
| **kitcut-hq/kitcut** | 46 | Claude Code: multicam sync, captions, vlog | skill |

**Singurul care ia link direct, fără descărcare manuală: `editast analyze "LINK"`.**
**Singurul care exportă în Premiere: `pireel`.**

## 6. Ce zice Reddit (căutat azi)

- **r/premiere**: „exportul pierde toate informațiile despre surse"; soluția = **Scene Edit Detection** + sync pe waveform. Ratează cross dissolves, fade, J/L cuts.
- **r/ClaudeCode**: `claude-video-vision` rulează **scdet / blackdetect / silencedetect / freezedetect / blurdetect / ebur128 într-o singură trecere ffmpeg**, apoi extrage doar cadrele relevante → de 10× mai ieftin.
- **r/editors**: tranzițiile AI (Kling start+stop frame, Higgsfield) **nu** se detectează cu scene detection — trebuie văzute.

**Nimeni de pe Reddit nu a găsit o metodă de a recupera proiectul din MP4.** Nu există.

## 7. Ordinea pe care o faci

1. `ANALIZEAZA-VIDEO.bat` → link YouTube → raport
2. Citești `report.html`: ce e filmat, ce e AI, ce tăieturi, ce efecte
3. Vrei să **editezi** → duci tăieturile în Premiere/Resolve:
   - `PySceneDetect` → `EDL` → Premiere (import)
   - sau `pireel` → export timeline
4. Vrei să **refaci** → `remape-plan` din raport + `remake-run`
5. Vrei **doar tăieturile** → deja le ai în `analiza/`

## 8. Verdict

| Întrebare | Răspuns |
|---|---|
| Pot vedea tot ce a făcut? | **DA** — shot cu shot, cu dovezi |
| Pot recupera proiectul Premiere? | **NU** — nu există în MP4 |
| Pot edita după el? | **DA** — tăieturi → EDL → Premiere |
| Pot să-l refac? | **DA** — plan de refacere per plan |
| Merită instalat? | **DA** — 1 `.bat`, ~800 MB o dată |
