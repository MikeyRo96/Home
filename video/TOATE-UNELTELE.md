# Toate uneltele care analizează un video și spun cum a fost făcut

Verificat pe GitHub API și Reddit, 26 noiembrie 2026. Stele = la data verificării.

## Nivelul 1 — deja pe PC-ul tău, gratis, 10 secunde

| Unealtă | Ce face | Cum |
|---|---|---|
| **Premiere: Scene Edit Detection** | pune un cut la fiecare schimbare de plan | importi → click dreapta → Scene Edit Detection |
| **DaVinci Resolve: Scene Cut Detection** | la fel, în Resolve | click dreapta pe clip → Scene Cut Detection |
| **Premiere: EDL / XML export** | scoate toate tăieturile ca fișier | File → Export → EDL / Final Cut Pro XML |

Nu are nevoie de nimic instalat. Limitarea: nu vede cross dissolves, fade-uri, J-cut, L-cut.

## Nivelul 2 — cel mai bun din lume, open source

| Repo | ★ | Licență | Ce face | Verdict |
|---|---|---|---|---|
| **benjiyaya/ComfyUI-ReaVideoBreakdown** | 157★ | MIT | versiunea **rea-video pt. ComfyUI**: breakdown shot cu shot (VIDEO.md) cu modele VL native, local, fără API | pentru cine are deja ComfyUI |
| **taoufik123-collab/claude-watch** | **1.228★** | MIT | îi dă agentului **ochi pe orice video**: cadre la tăieturi + transcript + raport structurat | cel mai popular „fă-l pe Claude să vadă video" |
| **Vincentwei1021/video-shotcraft** | **22.682★** | Apache-2.0 | **124 rețete de plan** + Remotion: reconstruiește promo/produs cinematic, editabil | cel mai mare ca stele; orientat reclame |
| **ALBEDO-TABAI/video-expert-analyzer** | 247★ | - | analiză după **cele 6 reguli Walter Murch** (montaj) | singurul care judecă *montajul*, nu pixelii |
| **Mharis-code/videoanalyzer** | 20★ | MIT | skill Claude Code: orice video social → **intelligence structurat** (hook, structură, CTA) | mic, dar fix pe „cum a fost făcut" |
| **whaoijie797-design/video-reverse-engineering** | 12★ | MIT | skill agent: keyframes/subtitles/audio reale → schema de producție | mic |
| **ronak-create/FableCut** | **823★** | - | „**edit blueprint**": tăieturi + BPM + curbă de energie + drop + muzica extrasă, apoi **reface reelu' cu filmările tale**; zero dependențe, MCP pt. agenți | copiază ritmul, nu doar îl măsoară |
| **ChatCut-Inc/viral-video-cloner** | 2★ | Apache-2.0 | refacere virală cu păstrarea mișcărilor, camerei și fiecărei tăieturi; schimbi oamenii/produsul | nou |
| **TheEvanX/video-remake-kit** | nou | - | link/fașier → **shot list + primul/ultimul cadru per plan** + joburi AI pe plan; dry-run 0 lei, poartă de dovezi | frate bun cu rea-video |
| **masonmosen/remake-depth-breakdown** | nou | - | kit de refacere: **depth video** pt. Seedance + breakdown cadru cu cadru | local, fără API plătit |
| **mage-space/skills → mage-video-remake** | - | - | skill care **instalează rea-video la commit fix**, descompune, apoi reface pe Mage cu personajele tale, tăiat pe timing-ul original | necesită cont Mage |
| **yzsp-studio/reference-video-recreation-workflow** | - | - | workflow refacere video de referință → shot breakdown | mic |
| **juneyaooo/capsule-cinema** | - | - | „video ca șablon": **o rețetă → infinite videouri** | de la autorul rea-video |
| **theygen-com/hyperframes** | **90.423★** | - | editează filmări proprii **sau** creează/reface video; agent AI | cel mai mare proiect de acest tip din GitHub |
| **OpenCut-app/OpenCut** | **99.400★** | - | CapCut open-source | cel mai popular editor „de telefon" |
| **jub0t/Concat** | **20.842★** | - | CapCut open-source, alt efort | activ 25 nov |
| **mltframework/shotcut** | 15.798★ | GPL-3.0 | editor NLE clasic, stabil | **cel mai testat**, nu alpha |
| **kajisho5/ffmpeg-skill** | **11.284★** | - | **42 unelte ffmpeg** cu schemă mașină → agentul taie fără editor | headless |
| **openfilm/openfilm** | 9.470★ | - | agentul de cod devine editor video | headless |
| **WeftCut/WeftCut** | 401★ | - | editor AI Win/mac/Linux | alternativă la FilmCraft |
| **kitcut-hq/kitcut** | 46★ | - | Claude Code: **multicam sync** + captions + vlog | singurul care sincronizează |
| **kernelmoonowl/pluraleyes** | 201★ | - | PluralEyes pt Win10/11, sync pe waveform | 2 camere |
| **Ersiter/pr2resolve** | 4★ | - | **`.prproj` → `.drp`** | singura cale reală din `.prproj` |
| **B0yko/tern** | 241★ | - | caută în arhivă după vorbit/ecran | arhivă |
| **DareDev256/fcp-mcp-server** | 161★ | - | Claude → Final Cut Pro | FCP |
| **elliotttate/SpliceKit** | 227★ | - | Command Palette + MCP pentru FCP | FCP |

| **JuneYaooo/rea-video** | **13.525★** | Apache-2.0 | spune shot cu shot dacă a fost **filmat / AI / 3D / cod / screen recording**; scoate captions cu timing (SRT/ASS), tăieturi, stickere, BPM, efecte sonore, plan de refacere. Raport HTML cu dovada per shot | **CEL MAI SERIOS PROIECT.** Activ (push 25 nov 2026) |
| **nexu-io/openmotion** | **16.525★** | Apache-2.0 | **cea mai bună unealtă care există azi pt. „văd un video → îl refac"**: îi dai link/fașier, agentul îl descompune în **Motion.md** (ordine planuri, timing, tranziții), îl reconstruiește cu elementele tale și îl exporti MP4 din Studio. **300+ șabloane**, 22 agenți. Actualizat azi | **CEL MAI MARE PROIECT DE REFACERE.** Nu doar analizează — face video nou. Necesită Node 22.18+, chei AI (BYOK) |
| **Pranav-Conova/video-reverse-engineer** | 6★ | MIT | **Edit AST**: tăieturi + tranziții (cut/flash/fade/dissolve/whip/zoom/spin/glitch) + zoom/pan/rotate/shake/speed-ramp/freeze/flash/blur/invert/RGB-split + BPM/beat grid/drops + OCR pe text + pattern-uri. Ia direct de pe YouTube | **cel mai detaliat pe „ce efecte sunt"** |
| **Breakthrough/PySceneDetect** | **5.662★** | BSD-3 | detectorul standard din industrie. CSV + **export EDL/OTIO/FCP** (din 0.7.1, iulie 2026) | **cel mai stabil. Îl folosesc toți.** |
| **Red5d/edlkit** | 48★ | - | creează, modifică și **aplică EDL** pe video | util pentru a tăia după un EDL |
| **BidyutRoy2/shotxray** | 0★ | MIT | raport + „brief de refacere" (cum să refaci fiecare plan) | nou, netestat |
| **AndrewPopesku/video-reverse-engineering** | 3★ | - | pipeline: yt-dlp → PySceneDetect → Whisper → Gemini → **OTIO/FCP XML** | netestat |
| **MaanasTaneja/ShotParser** | 5★ | - | analiză shot-cu-shot, detector custom | mic |
| **material-lab-io/HendrixVideo** | 4★ | MIT | pipeline: shot detection, scene construction | mic, push 2025 |
| **supergeniodelmale/Cinemetrica** | 21★ | Apache-2.0 | **analiză statistică de film**: lungimi de plan, ritm | cercetare |
| **mAE7777/vidistill** | 3★ | MIT | video → fișiere pe care le poate citi un AI (transcript + cadre) | utilitar |

## Nivelul 2b — ce am verificat în plus azi (26 nov 2026, după rate-limit)

| Repo | ★ | Ce face | Verdict |
|---|---|---|---|
| **HKUDS/VideoAgent** | **2.065★** | cadru academic (EMNLP 2026): **înțelegere + editare + refacere video** all-in-one | greu, pt. cercetare |
| **bradautomates/claude-video** | **21.825★** | `/watch` — descarcă, extrage cadre, transcrie, dă agentului memoria video-ului | cel mai folosit pt. „vezi video-ul" |
| **HUANGCHIHHUNGLeo/claude-real-video** | **2.346★** | cadre scene-aware, deduplicate + transcript | mai bun la filme lungi |
| **jordanrendric/claude-video-vision** | **1.539★** | plugin Claude Code: **analiză înainte de extragere** (scdet/blackdetect/silencedetect/freeze/blur/ebur128) → hartă structurală, apoi cadre | are exact filtrele noastre + 6 în plus |
| **0xsline/OpenChatCut** | **3.342★** | editor video conversațional local, timeline multi-track | alternativă la FableCut |
| **MartinDelophy/ai-video-editor** | **1.013★** | editor local unde om + agent editează același timeline real | activ azi |
| **rednote/… doubao2api** | 351★ | API OpenAI-compatibil pt. model chinezesc | nerelevant |
| **TubeLabHQ/youtube-research-skills** | 345★ | skills de research YouTube: **outlier videos, validare nișă** | nu analizează video-ul, analizează piața |

**Ce NU am putut verifica:** API-ul GitHub a dat **rate limit** la ~130 interogări. Restul căutărilor se reiau după reset (1 h) — comanda exactă e în `video/CAUTA-MAI-MULTE.md`.

## Nivelul 3 — formatul de schimb (cheia tehnică)

**OpenTimelineIO** — `AcademySoftwareFoundation/OpenTimelineIO`, **2.120★, Apache-2.0**

Este **formatul standard** prin care trece un timeline dintr-un program în altul. Dacă vrei să duci tăieturile detectate în Premiere/Resolve, **OTIO e puntea**.

**Deci lanțul real:**

```
PySceneDetect → OTIO / EDL / FCP XML → Premiere (importi) → ai tăieturile pe timeline
```

**Premiere importă:** EDL, Final Cut Pro 7 XML, XML.
**Resolve importă:** EDL, FCPXML, OTIO, AAF.

## Nivelul 4 — programe cu plată (ca să știi ce există)

| Program | Ce face | Preț | Merită? |
|---|---|---|---|
| **StoryFolder** | video → XLSX/CSV cu thumbnail per plan + export Selects.edl/xml/fcpxml | free 6 boarduri; exportul e Pro | numai dacă vrei tabel |
| **TwelveLabs** | AI care „se uită" la video, search semantic | per minut | pentru arhive mari |
| **Google Cloud Video Intelligence** | shot detection, obiecte, OCR | per minut | enterprise |
| **Azure Video Indexer** | timeline multi-canal, transcript, OCR, fețe | Azure | enterprise |

## Ce NU există — spus direct

| Nu există | De ce |
|---|---|
| **„amprentă Premiere" în video** | exportul e produs nou, nu arhivă |
| **recuperarea proiectului din MP4** | fără `.prproj` nu se poate |
| **refacerea timeline-ului automat** | ai nevoie de filmările originale pentru relink |
| **citirea efectelor cu precizie 100%** | scene detection compară lumina; dissolve-urile îl păcălesc |

## Rezumat — ce folosești

| Vrei | Folosește |
|---|---|
| **tăieturile, acum** | **Premiere → Scene Edit Detection** |
| **tăieturile + EDL pentru timeline** | **PySceneDetect** (5.662★) |
| **efecte, zoom, beat, OCR** | **Pranav-Conova/video-reverse-engineer** |
| **filmat vs AI vs cod, plan de refacere** | **JuneYaooo/rea-video** (13.525★) |
| **import în Premiere/Resolve** | **OpenTimelineIO** |
