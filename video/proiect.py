"""
PROIECT FILMCRAFT - ca un proiect deschis in Premiere Pro.

Ia rezultatele reale (breakdown.json de la rea-video + stem-urile audio + taieturile
detectate) si le aseaza pe TRACK-URI SEPARATE, exact cum ar sta un montaj adevarat:

  V4  TEXT / SUBTITRARI      text ars in video (OCR) - doar cand exista
  V3  OVERLAY / HUD          zona inghetata peste gameplay (logo, watermark, template)
  V2  GRAFICA                elemente desenate peste fundal (particule, bare, cifre)
  V1  GAMEPLAY               imaginea de baza, taiata in planuri

  A4  EFEKTE / SFX           impact, whoosh, click, typing
  A3  MUZICA                 melodia de fundal
  A2  VOCE                   voce usor / naratiune
  A1  MIX ORIGINAL           sunetul complet, asa cum e pe YouTube

Ce e MASURAT si ce e INFERAT e marcat pe fiecare clip:
  [M]  = masurat de rea-video (OCR, pixeli inghetati, separare audio, onset-uri)
  [~]  = inferat din date (ordinea layerelor, durata)
  [V]  = are nevoie de VLM ca sa fie sigur (nu e pornit)

Fara date reale, NU inventez track-uri. Un track gol e mai cinstit decat unul plin de minciuni.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

# ---------------------------------------------------------------- constante
FPS_DEFAULT = 25.0

# ordinea track-urilor video, de la baza la varf
V_TRACKS = [
    ("V1", "GAMEPLAY", "imaginea de baza"),
    ("V2", "GRAFICA", "elemente desenate peste fundal"),
    ("V3", "OVERLAY / HUD", "zona inghetata peste gameplay"),
    ("V4", "TEXT / SUBTITRARI", "text ars in video (OCR)"),
]
A_TRACKS = [
    ("A1", "MIX ORIGINAL", "sunetul complet"),
    ("A2", "VOCE", "voce / naratiune"),
    ("A3", "MUZICA", "melodia de fundal"),
    ("A4", "EFEKTE / SFX", "impact, whoosh, click"),
]


# ---------------------------------------------------------------- utilitare
def _fps(text, implicit=FPS_DEFAULT):
    """'60/1' -> 60.0 ; '30000/1001' -> 29.97 ; orice altceva -> implicit"""
    try:
        s = str(text)
        if "/" in s:
            a, b = s.split("/")[:2]
            v = float(a) / float(b) if float(b) else implicit
        else:
            v = float(s)
        return v if 1.0 <= v <= 240.0 else implicit
    except (TypeError, ValueError, ZeroDivisionError):
        return implicit


def _sec(t):
    """Scoate secunde dintr-un timestamp rea-video: '00:01.375', 1.375, '1.375s'."""
    if t is None:
        return None
    if isinstance(t, (int, float)):
        return float(t)
    s = str(t).strip().rstrip("s")
    if not s:
        return None
    if ":" in s:
        parts = s.split(":")
        try:
            v = 0.0
            for p in parts:
                v = v * 60 + float(p)
            return v
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def _pathurl(p):
    """Calea absoluta in format FCP7 (file://localhost/...), corect pe Windows si Linux."""
    try:
        ap = Path(p).resolve()
    except (OSError, ValueError):
        return ""
    cale = str(ap).replace("\\", "/")
    if len(cale) > 1 and cale[1] == ":":
        return "file://localhost/" + urllib.parse.quote(cale)
    return "file://localhost" + urllib.parse.quote(cale)


def _tc(sec, fps):
    """Timp lizibil: 00:01:23 (hh:mm:ss)."""
    if sec is None:
        return "-"
    f = int(round(max(0.0, sec) * fps))
    s = f / fps
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    return "%02d:%02d:%06.3f" % (h, m, s % 60)


# ---------------------------------------------------------------- citire surse
def citeste_breakdown(analiza_dir):
    """Cauta breakdown.json in folderul de analiza rea-video. Returneaza dict sau {}."""
    p = Path(analiza_dir)
    for c in (p / "breakdown.json", p / "out" / "breakdown.json"):
        if c.exists():
            try:
                return json.loads(c.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass
    for c in p.rglob("breakdown.json"):
        try:
            return json.loads(c.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return {}


def gaseste_stems(analiza_dir):
    """Stem-urile audio reale: original / vocals / music / effects."""
    d = Path(analiza_dir) / "stems"
    out = {}
    if not d.exists():
        return out
    for nume in ("original", "vocals", "music", "effects"):
        for ext in (".wav", ".flac", ".mp3"):
            c = d / (nume + ext)
            if c.exists():
                out[nume] = c
                break
    return out


def durata_audio(p, ffprobe="ffprobe"):
    """Durata unui fisier audio/video, prin ffprobe. None daca nu se poate."""
    try:
        r = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(p)],
            capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


# ---------------------------------------------------------------- detectie layere
def layere_din_breakdown(bd):
    """Scoate din breakdown.json: (planuri, layere pe plan, tranzitii).

    Returneaza
      planuri : [{'start','end','eticheta','sigur'}]
      layere  : {'V2': [...], 'V3': [...], 'V4': [...]} - fiecare clip cu start/end/text/sigur
    """
    planuri, layere = [], {"V2": [], "V3": [], "V4": []}
    if not isinstance(bd, dict):
        return planuri, layere

    shots = bd.get("shots") or bd.get("unit_split") or []
    if not isinstance(shots, list):
        shots = []

    for i, s in enumerate(shots):
        if not isinstance(s, dict):
            continue
        st = _sec(s.get("start") or s.get("start_time") or s.get("t"))
        en = _sec(s.get("end") or s.get("end_time"))
        if st is None:
            continue
        et = (s.get("label") or s.get("made") or s.get("kind")
              or s.get("production") or "plan")
        # caracteristicile masurate: camera, framing, material
        feat = s.get("features") or {}
        camera = str(feat.get("camera") or "").strip()
        framing = str(feat.get("framing") or feat.get("shot_size") or "").strip()
        material = str(feat.get("material") or "").strip()
        planuri.append({
            "start": st, "end": en, "eticheta": str(et),
            "sigur": bool(s.get("vlm") or s.get("confidence")),
            "index": i + 1,
            "camera": camera,
            "framing": framing,
            "material": material,
        })

        # overlay-urile reale: text OCR, zone inghetate, elemente desenate
        ov = s.get("overlays") or s.get("overlay") or []
        if isinstance(ov, dict):
            ov = [ov]
        for o in ov if isinstance(ov, list) else []:
            if not isinstance(o, dict):
                continue
            tip = str(o.get("type") or o.get("kind") or "").lower()
            txt = str(o.get("text") or o.get("content") or "").strip()

            # clasificare pe TIP intai; "or txt" doar ca ultima solutie,
            # altfel orice overlay cu text ajunge pe V4
            if any(k in tip for k in ("subtitle", "caption", "title", "sub",
                                      "text", "label", "chat")):
                tr = "V4"
            elif any(k in tip for k in ("static", "frozen", "watermark",
                                        "logo", "hud", "template", "frame", "skin")):
                tr = "V3"
            elif any(k in tip for k in ("graphic", "grafic", "drawn", "shape",
                                        "particle", "bar", "chart", "sticker",
                                        "emoji", "meme", "effect", "filter")):
                tr = "V2"
            elif txt:
                tr = "V4"          # are text, dar tip necunoscut -> subtitrare
            else:
                tr = "V2"          # element vizual fara text

            layere[tr].append({
                "start": st, "end": en,
                "text": txt[:120] or tip,
                "eticheta": tip or ("text" if tr == "V4" else "grafica"),
                "sigur": "M",
            })

        # grafica desenata masurata (layers.py)
        dr = s.get("drawn") or s.get("layers")
        if isinstance(dr, dict) and dr:
            layere["V2"].append({
                "start": st, "end": en,
                "text": "%d elemente desenate" % len(dr) if isinstance(dr, (list, dict)) else "grafica",
                "eticheta": "drawn layer", "sigur": "M",
            })

    # daca planurile n-au 'end', il iau de la urmatorul
    for a, b in zip(planuri, planuri[1:]):
        if a["end"] is None:
            a["end"] = b["start"]
    return planuri, layere


def evenimente_sfx(bd):
    """Evenimente SFX masurate: [{'t','type','strength'}] din breakdown.json."""
    out = []
    if not isinstance(bd, dict):
        return out
    for cheie in ("sfx", "sound_effects"):
        v = bd.get(cheie)
        if isinstance(v, dict):
            v = v.get("events")
        if isinstance(v, list):
            for e in v:
                if not isinstance(e, dict):
                    continue
                t = _sec(e.get("t") or e.get("time") or e.get("start"))
                if t is None:
                    continue
                out.append({"t": t,
                            "type": str(e.get("type") or e.get("kind") or "sfx"),
                            "strength": e.get("strength")})
    for e in out:
        if not isinstance(e, dict):
            continue
    return sorted(out, key=lambda x: x["t"])


def beat_uri(bd):
    """Beat-urile muzicii: [secunde]."""
    if not isinstance(bd, dict):
        return []
    mu = bd.get("music")
    if isinstance(mu, dict):
        b = mu.get("beats")
        if isinstance(b, list):
            return sorted(x for x in (_sec(v) for v in b) if x is not None)
    return []


def taieturi_din_breakdown(bd, dur):
    """Momentul fiecarei taieturi, din breakdown.json."""
    out = []
    if not isinstance(bd, dict):
        return out
    for cheie in ("cuts", "transitions", "boundaries"):
        v = bd.get(cheie)
        if isinstance(v, list):
            for x in v:
                t = _sec(x.get("t") if isinstance(x, dict) else x)
                if t is not None and 0 < t < dur:
                    out.append(t)
    return sorted(set(round(t, 3) for t in out))


def taie_felii(ffmpeg, sursa, evenimente, outdir, pre=0.15, post=0.45, limita=160):
    """Taie cate o felie din stem-ul effects la fiecare eveniment SFX.

    Returneaza [(cale, start, durata, tip, putere)] - doar feliile create cu succes.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    bucati = []
    for i, e in enumerate(evenimente[:limita]):
        t = e["t"]
        a = max(0.0, t - pre)
        d = pre + post
        nume = "sfx_%03d_%s.wav" % (i + 1, re.sub(r"[^a-z0-9]+", "", e["type"].lower())[:12] or "x")
        dest = outdir / nume
        if not dest.exists():
            cmd = [ffmpeg, "-y", "-v", "error", "-ss", "%.3f" % a, "-t", "%.3f" % d,
                   "-i", str(sursa), "-ac", "2", "-ar", "48000", str(dest)]
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=120)
                if r.returncode != 0 or not dest.exists():
                    continue
            except (OSError, subprocess.SubprocessError):
                continue
        bucati.append((dest, a, d, e["type"], e.get("strength")))
    return bucati


# ---------------------------------------------------------------- scriere FCP7
def _clip_v(idx, nume, start_f, end_f, in_f, dur_f, pathurl, extra=""):
    """Un clipitem video pe timeline."""
    f = ""
    if pathurl:
        f = ('<file id="file-%s"><name>%s</name><pathurl>%s</pathurl>'
             '<duration>%d</duration>%s</file>'
             % (idx, html.escape(nume), html.escape(pathurl), dur_f, extra))
    return (
        '<clipitem id="ci-%s">'
        '<name>%s</name><duration>%d</duration>'
        '<start>%d</start><end>%d</end><in>%d</in><out>%d</out>%s'
        '</clipitem>' % (idx, html.escape(nume), end_f - start_f,
                         start_f, end_f, in_f, in_f + (end_f - start_f), f)
    )


def scrie_proiect_fcpxml(
        cale_xml, video, durata, fps,
        planuri, layere, stems, latime=1920, inaltime=1080,
        nume="Proiect gaming", felii_sfx=None, beats=None,
        dezactiveaza_layere=True):
    """Scrie un FCP7 XML cu 4 track-uri video + 4 track-uri audio.

    Fiecare track are propriul <file>. FilmCraft/Premiere/Resolve le incarca pe randuri.
    """
    f = float(fps or FPS_DEFAULT)
    tb = int(round(f))
    ntsc = "TRUE" if abs(f - round(f)) > 0.001 else "FALSE"
    total = int(round(float(durata or 0) * f))
    urls = {}

    vpath = _pathurl(video) if video else ""
    vname = Path(video).name if video else "video.mp4"

    def media_extra(w, h):
        return ('<media><video><samplecharacteristics>'
                '<width>%d</width><height>%d</height>'
                '<rate><timebase>%d</timebase><ntsc>%s</ntsc></rate>'
                '</samplecharacteristics></video></media>' % (w, h, tb, ntsc))

    def media_audio():
        return ('<media><audio><samplecharacteristics><depth>16</depth>'
                '<samplerate>48000</samplerate></samplecharacteristics>'
                '<channelcount>2</channelcount></audio></media>')

    # ---------------- VIDEO
    benzi = {k: [] for k, _, _ in V_TRACKS}

    # V1: toata durata, un singur clip lung (sau pe planuri daca le am)
    if planuri:
        for i, p in enumerate(planuri):
            a = int(round((p["start"] or 0) * f))
            b = int(round((p["end"] or durata) * f))
            if b <= a:
                continue
            benzi["V1"].append(_clip_v(
                "v1-%d" % (i + 1), "plan_%03d" % (i + 1), a, b, a,
                total, vpath, media_extra(latime, inaltime)))
    else:
        benzi["V1"].append(_clip_v(
            "v1-0", "gameplay", 0, total, 0, total, vpath,
            media_extra(latime, inaltime)))

    # V2/V3/V4: layerele reale
    for tr in ("V2", "V3", "V4"):
        for j, L in enumerate(layere.get(tr, [])):
            a = int(round((L.get("start") or 0) * f))
            b = int(round((L.get("end") or durata) * f))
            if b - a < 2:
                continue
            et = L.get("eticheta") or tr
            txt = L.get("text") or ""
            nm = ("[%s] %s" % (L.get("sigur", "~"), et)) + (" - " + txt if txt else "")
            nm = re.sub(r"\s+", " ", nm)[:80]
            benzi[tr].append(_clip_v(
                "%s-%d" % (tr.lower(), j + 1), nm, a, b, a, total, vpath,
                media_extra(latime, inaltime)))

    linii_v = []
    for nume_tr, eticheta, _ in V_TRACKS:
        clips = benzi[nume_tr]
        if not clips:
            continue  # track gol = nu-l scriu deloc (nu mint)
        # V2-V4 arata ACELASI video ca V1. Daca ar fi active, ar acoperi gameplay-ul.
        # Le las pe timeline (le vezi si in Premiere) dar dezactivate = FilmCraft afiseaza V1.
        # In Premiere: click dreapta pe track -> Enable, daca vrei sa le vezi.
        steag = ("<enabled>FALSE</enabled>"
                 if (dezactiveaza_layere and nume_tr != "V1") else "")
        linii_v.append('<track>%s%s</track>' % (steag, "".join(clips)))

    # ---------------- AUDIO
    benzi_a = {k: [] for k, _, _ in A_TRACKS}
    mapare = {"original": "A1", "vocals": "A2", "music": "A3", "effects": "A4"}
    for cheie, cale in stems.items():
        tr = mapare.get(cheie)
        if not tr:
            continue
        d = durata_audio(cale) or durata
        n = int(round((d or durata) * f))
        u = _pathurl(cale)
        benzi_a[tr].append(
            _clip_v(tr.lower() + "-1", cheie, 0, n, 0, n, u, media_audio())
            .replace("</clipitem>",
                     "<sourcetrack><mediatype>audio</mediatype>"
                     "<trackindex>1</trackindex></sourcetrack></clipitem>"))

    # A4: feliile SFX reale (fiecare sunet separat pe timeline)
    if felii_sfx:
        benzi_a["A4"] = []
        for i, (cale, start, d, tip, putere) in enumerate(felii_sfx):
            a = int(round(start * f))
            n = max(1, int(round(d * f)))
            nm = "SFX %02d %s%s" % (i + 1, tip,
                                    (" (%s)" % putere) if putere is not None else "")
            benzi_a["A4"].append(
                _clip_v("a4-%d" % (i + 1), nm, a, a + n, 0, n, _pathurl(cale), media_audio())
                .replace("</clipitem>",
                         "<sourcetrack><mediatype>audio</mediatype>"
                         "<trackindex>1</trackindex></sourcetrack></clipitem>"))

    # daca nu am stems, pun macar sunetul original pe A1 (e in mp4)
    if vpath and not benzi_a["A1"]:
        benzi_a["A1"].append(
            _clip_v("a1-1", vname + " (sunet)", 0, total, 0, total, vpath, media_audio())
            .replace("</clipitem>",
                     "<sourcetrack><mediatype>audio</mediatype>"
                     "<trackindex>1</trackindex></sourcetrack></clipitem>"))

    linii_a = []
    for nume_tr, eticheta, _ in A_TRACKS:
        clips = benzi_a[nume_tr]
        if not clips:
            continue
        linii_a.append('<track>%s</track>' % "".join(clips))

    xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<!DOCTYPE xmeml>\n"
        '<xmeml version="4"><sequence id="seq-1">'
        "<name>%s</name><duration>%d</duration>"
        "<rate><timebase>%d</timebase><ntsc>%s</ntsc></rate>"
        "<media><video>"
        "<format><samplecharacteristics><width>%d</width><height>%d</height>"
        "<rate><timebase>%d</timebase><ntsc>%s</ntsc></rate>"
        "</samplecharacteristics></format>"
        "%s</video>"
        "%s"
        "%s"
        "</media></sequence></xmeml>\n"
        % (html.escape(nume), total, tb, ntsc, latime, inaltime, tb, ntsc,
           "".join(linii_v),
           ("<audio>%s</audio>" % "".join(linii_a)) if linii_a else "",
           _markere_xml(beats, f, total, planuri))
    )
    Path(cale_xml).write_text(xml, encoding="utf-8")
    return len(linii_v), len(linii_a)


def _markere_xml(beats, fps, total_f, planuri=None):
    """Markere pe timeline: fiecare taietura CU DURATA planului + fiecare beat.

    In FilmCraft apar ca repere. Asa vezi ritmul: 0.8s / 2.1s / 0.4s.
    """
    out = []
    if planuri:
        for i, p in enumerate(planuri[:400]):
            poz = int(round((p.get("start") or 0) * fps))
            dur = (p.get("end") or 0) - (p.get("start") or 0)
            if not (0 <= poz < total_f) or dur <= 0:
                continue
            bucati = ["%d. %.2fs" % (i + 1, dur)]
            if p.get("eticheta"):
                bucati.append(str(p["eticheta"])[:16])
            if p.get("camera"):
                bucati.append(str(p["camera"])[:14])
            if p.get("framing"):
                bucati.append(str(p["framing"])[:12])
            out.append('<marker><name>%s</name><in>%d</in><out>%d</out></marker>'
                       % (' | '.join(bucati), poz, poz))
    if beats:
        for i, b in enumerate(beats[:400]):
            poz = int(round(b * fps))
            if 0 <= poz < total_f:
                out.append('<marker><name>beat %d</name><in>%d</in><out>%d</out></marker>'
                           % (i + 1, poz, poz))
    # FCP7: markerele sunt elemente REPETATE, nu un container
    return "".join(out)



# ---------------------------------------------------------------- patch rea-video
PATCH_MEDIAN = """
_ORIGINAL = None


def _median_filter(a, size, axis, chunk=600):
    # PATCH: varianta originala facea sliding_window_view peste TOT blocul inainte
    # de bucla -> (600, 513, 17) float32 = un temporar urias; np.median mai facea
    # inca unul la fel. Pe 19 min de film: 3.2 GiB -> ArrayMemoryError.
    # Acum fereastra de citire e (chunk, m, size) cu chunk ales dupa RAM: max 32 MB.
    pad = size // 2
    if axis != 0:
        return _median_filter(a.T, size, 0, chunk).T
    n = a.shape[0]
    m = max(1, a.shape[1])
    buget = 32 * 1024 * 1024
    maxim = max(1, int(buget // (m * size * 4)))
    chunk = max(1, min(chunk, maxim))
    padded = np.pad(a, ((pad, pad), (0, 0)), mode="edge")
    out = np.empty_like(a)
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        win = np.lib.stride_tricks.sliding_window_view(padded[s:e + 2 * pad], size, axis=0)
        out[s:e] = np.median(win, axis=-1)
    return out
"""


PATCH_GPU = """
def _gpu_dlls():
    # PATCH: pe Windows onnxruntime NU vede singur DLL-urile venite ca pachete pip.
    # Fara asta: "cublasLt64_12.dll which is missing" -> cade pe CPU fara sa spuna.
    import glob as _g
    import os as _o
    import sys as _s
    gasite = []
    for baza in _s.path:
        if not baza:
            continue
        for d in _g.glob(_o.path.join(baza, "nvidia", "*", "bin")):
            if d not in gasite:
                gasite.append(d)
    if gasite:
        _o.environ["PATH"] = _o.pathsep.join(gasite) + _o.pathsep + _o.environ.get("PATH", "")
        for d in gasite:
            try:
                if hasattr(_o, "add_dll_directory"):
                    _o.add_dll_directory(d)
            except Exception:
                pass
    # metoda oficiala onnxruntime (1.21+): cauta singur CUDA/cuDNN/MSVC in pachetele pip
    try:
        import onnxruntime as _ort
        if hasattr(_ort, "preload_dlls"):
            _ort.preload_dlls()
    except Exception:
        pass
    return gasite


import os as _os2


def _gpu_batch():
    # PATCH: modelul de separea sunetului rula cu batch=1 = placa video pe jumate goala.
    # Pe CUDA merg 8 segmente deodata (aceeasi matematica, altfel asezata).
    # 1660 Super are 6 GB; daca nu incap, _separate_gpu injumatateste pana merge.
    try:
        import onnxruntime as _ort
        if "CUDAExecutionProvider" not in _ort.get_available_providers():
            return 1
        if (_gpu_dlls(), _ort.get_device())[1] != "GPU":
            return 1
        return max(1, int((_os2.getenv("REA_GPU_BATCH") or "8")))
    except Exception:
        return 1


def _separate_gpu(mix):
    # batch mare pe placa video; daca iese din memorie, scad si reincerc (nu crapa)
    b = _gpu_batch()
    while b > 1:
        try:
            return separate(mix, batch=b)
        except Exception as e:
            if "memory" not in str(e).lower() and "alloc" not in str(e).lower():
                break
            b //= 2
    return separate(mix)


def _gpu_providers():
    # PATCH: rea-video avea providers=["CPUExecutionProvider"] scris cu mana.
    # Acum foloseste placa video daca poate; altfel cade lin pe CPU.
    import os as _os
    try:
        import onnxruntime as _ort
        vrut = (_os.getenv("REA_GPU") or "auto").strip().lower()
        if vrut in ("0", "off", "cpu", "no"):
            return ["CPUExecutionProvider"]
        _gpu_dlls()
        have = _ort.get_available_providers()
        if "CUDAExecutionProvider" in have:
            return [("CUDAExecutionProvider", {"device_id": 0,
                                               "arena_extend_strategy": "kSameAsRequested"}),
                    "CPUExecutionProvider"]
        if "DmlExecutionProvider" in have:
            return ["DmlExecutionProvider", "CPUExecutionProvider"]
    except Exception:
        pass
    return ["CPUExecutionProvider"]


def gpu_info():
    # ce GPU a gasit onnxruntime (pt. mesajul de start)
    try:
        import onnxruntime as _ort
        have = _ort.get_available_providers()
        for p in ("CUDAExecutionProvider", "DmlExecutionProvider"):
            if p in have:
                return p
    except Exception:
        pass
    return None
"""


PATCH_FEATURES_LAZY = """
class _LazyFrames(list):
    # PATCH: 274 shoturi x 16 cadre x 380 KB = 1.6 GB de array-uri brute in RAM.
    # Tin cadrele ca PNG in memorie (~10x mai mic) si le decodez cand se cer.
    def append(self, arr):
        try:
            ok, buf = cv2.imencode(".png", arr, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            if ok:
                list.append(self, buf.tobytes())
                return
        except Exception:
            pass
        list.append(self, arr)

    def __getitem__(self, i):
        v = list.__getitem__(self, i)
        if isinstance(v, (bytes, bytearray)):
            import numpy as _np
            f = cv2.imdecode(_np.frombuffer(v, _np.uint8), cv2.IMREAD_COLOR)
            list.__setitem__(self, i, f)
            return f
        return v

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
"""


def patch_gpu(reasrc, tacut=False):
    """Pune placa video la treaba pentru ONNX (stem-uri + OCR). Fallback pe CPU."""
    f = Path(reasrc) / "rea_video" / "stems.py"
    if not f.exists():
        return False
    try:
        txt = f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    if "_gpu_providers()" in txt:
        if not tacut:
            print("  rea-video: GPU deja activat")
        return True

    vechi = 'providers=["CPUExecutionProvider"]'
    if vechi not in txt:
        return False

    bak = f.with_suffix(".py.bak")
    if not bak.exists():
        try:
            bak.write_bytes(f.read_bytes())
        except OSError:
            pass

    txt = txt.replace(vechi, "providers=_gpu_providers()")
    # separea sa mearga cu batch mare pe placa video (de 3-4x mai repede decat batch=1)
    txt = txt.replace("        voc, inst = separate(mix)\n",
                      "        voc, inst = _separate_gpu(mix)\n")
    txt += "\n\n" + PATCH_GPU.strip() + "\n"
    try:
        f.write_text(txt, encoding="utf-8")
    except OSError:
        return False

    # al doilea model (efecte, 149 MB) - tot pe placa video
    fx = Path(reasrc) / "rea_video" / "effects.py"
    if fx.exists():
        try:
            t3 = fx.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            t3 = ""
        if vechi in t3:
            t3 = t3.replace(vechi, "providers=_gpu_providers()")
            if "from .stems import _gpu_providers" not in t3:
                t3 += "\n\nfrom .stems import _gpu_providers\n"
            try:
                fx.write_text(t3, encoding="utf-8")
            except OSError:
                pass

    # OCR-ul (rapidocr) citeste textul cu placa video daca ii spun
    ov = Path(reasrc) / "rea_video" / "overlay.py"
    if ov.exists():
        try:
            t4 = ov.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            t4 = ""
        anc = '            kwargs["intra_op_num_threads"] = MODEL_THREADS\n'
        if anc in t4 and "use_cuda" not in t4:
            # ATENTIE: rapidocr-onnxruntime (2.x) primeste "det_use_cuda";
            # rapidocr 3.x primeste "Det.use_cuda". Daca ii dau cheia gresita,
            # __init__ arunca TypeError si OCR-ul moare COMPLET. Deci: intreb.
            add = anc + ('            try:\n'
                         '                import onnxruntime as _o\n'
                         '                _g = "CUDAExecutionProvider" in _o.get_available_providers()\n'
                         '            except Exception:\n'
                         '                _g = False\n'
                         '            # care rapidocr e instalat: cel vechi vrea "det_use_cuda",\n'
                         '            # rapidocr 3 vrea "Det.use_cuda". Cheia gresita = TypeError = OCR mort.\n'
                         '            try:\n'
                         '                import rapidocr_onnxruntime  # noqa: F401\n'
                         '                _vechi = True\n'
                         '            except ImportError:\n'
                         '                _vechi = False\n'
                         '            if _vechi:\n'
                         '                for _k in ("det_use_cuda", "cls_use_cuda", "rec_use_cuda"):\n'
                         '                    kwargs[_k] = _g\n'
                         '            else:\n'
                         '                for _k in ("Det.use_cuda", "Cls.use_cuda", "Rec.use_cuda"):\n'
                         '                    kwargs[_k] = _g\n')
            t4 = t4.replace(anc, add, 1)
            try:
                ov.write_text(t4, encoding="utf-8")
            except OSError:
                pass

    # si OCR-ul de text foloseste tot GPU-ul, daca are fisierul lui
    for alt in ("overlay.py", "media.py", "vlm.py"):
        g = Path(reasrc) / "rea_video" / alt
        if not g.exists():
            continue
        try:
            t2 = g.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if vechi in t2:
            try:
                g.write_text(t2.replace(vechi, "providers=_gpu_providers()")
                             + "\n\nfrom .stems import _gpu_providers\n", encoding="utf-8")
            except OSError:
                pass

    if not tacut:
        print("  rea-video: PATCH GPU - stem-uri + OCR pe placa video")
    return True


def patch_cadre(reasrc, tacut=False):
    """Tin cadrele comprimate in RAM: 1.6 GB -> ~200 MB. Fara sa schimbe interfata."""
    f = Path(reasrc) / "rea_video" / "features.py"
    if not f.exists():
        return False
    try:
        txt = f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    if "class _LazyFrames(list):" in txt:
        # poate fi varianta RUPTA (clasa dupa @dataclass -> NameError). Verific.
        try:
            compile(txt, str(f), "exec")
        except SyntaxError:
            pass
        idx_cls = txt.find("class _LazyFrames(list):")
        idx_use = txt.find("default_factory=_LazyFrames")
        if idx_use != -1 and idx_cls != -1 and idx_cls < idx_use:
            if not tacut:
                print("  rea-video: patch-ul de cadre e deja aplicat")
            return True
        # RUPT: clasa e definita dupa locul unde e folosita -> o mut in fata
        bloc = txt[idx_cls:]
        txt = txt[:idx_cls].rstrip() + "\n"
        anc = "@dataclass\nclass ShotSamples:"
        if anc not in txt:
            return False
        txt = txt.replace(anc, bloc.strip() + "\n\n\n" + anc, 1)
        txt = txt.replace("frames: list[np.ndarray] = field(default_factory=list)",
                          "frames: list = field(default_factory=_LazyFrames)")
        try:
            compile(txt, str(f), "exec")
        except SyntaxError:
            return False
        try:
            f.write_text(txt, encoding="utf-8")
        except OSError:
            return False
        if not tacut:
            print("  rea-video: PATCH cadre REPARAT (clasa era pusa prea jos)")
        return True

    vechi = "frames: list[np.ndarray] = field(default_factory=list)"
    if vechi not in txt:
        return False

    bak = f.with_suffix(".py.bak")
    if not bak.exists():
        try:
            bak.write_bytes(f.read_bytes())
        except OSError:
            pass

    txt = txt.replace(vechi, "frames: list = field(default_factory=_LazyFrames)")
    # FIX: @dataclass are nevoie de _LazyFrames DEFINIT mai sus. Punand clasa la
    # sfarsitul fisierului iesea NameError si patch-ul nu rula deloc.
    anc = "@dataclass\nclass ShotSamples:"
    if anc not in txt:
        return False
    txt = txt.replace(anc, PATCH_FEATURES_LAZY.strip() + "\n\n\n" + anc, 1)
    try:
        compile(txt, str(f), "exec")  # nu scriu niciodata un fisier care nu se compileaza
    except SyntaxError:
        return False
    try:
        f.write_text(txt, encoding="utf-8")
    except OSError:
        return False

    if not tacut:
        print("  rea-video: PATCH cadre - 1.6 GB -> ~200 MB (compresie in memorie)")
    return True


def verifica_patchuri(reasrc, pyexe=None):
    """Ce fisiere patch-uite sunt STRICATE. Gol = totul e in regula.

    Nu ajunge sa verific sintaxa: un patch poate fi sintaxa corecta si sa cada la
    import ("name _LazyFrames is not defined") - exact asa a crapat analiza dupa
    40 de minute. Deci: (1) verific ordinea definirilor si (2) chiar import modulele.
    """
    reale = []
    surse = {}
    for nume in ("features.py", "audio.py", "stems.py", "effects.py", "overlay.py"):
        f = Path(reasrc) / "rea_video" / nume
        if not f.exists():
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            reale.append(nume)
            continue
        surse[nume] = txt
        try:
            compile(txt, str(f), "exec")
        except SyntaxError:
            reale.append(nume)

    # patch-ul de memorie trebuie sa fie EFECTIV in audio.py, nu doar fisierul-functie
    # sa existe. Daca s-a pierdut (refacere din .bak), analiza crapa la 3.2 GiB.
    au = surse.get("audio.py", "")
    if au and "_nv_patch_median" not in au and "audio.py" not in reale:
        reale.append("audio.py")

    # ordinea definirii: clasa folosita inainte sa existe = NameError la import
    ft = surse.get("features.py", "")
    i_cls, i_use = ft.find("class _LazyFrames(list):"), ft.find("default_factory=_LazyFrames")
    if i_use != -1 and (i_cls == -1 or i_cls > i_use) and "features.py" not in reale:
        reale.append("features.py")

    # testul adevarat: import fiecare modul intr-un proces nou
    if pyexe and Path(pyexe).exists():
        mods = [n[:-3] for n in surse]
        cod = ("import importlib,sys\n"
               "for m in sys.argv[1:]:\n"
               "    try: importlib.import_module('rea_video.'+m)\n"
               "    except Exception: print(m)\n")
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        try:
            r = subprocess.run([str(pyexe), "-c", cod] + mods, cwd=str(reasrc),
                               capture_output=True, text=True, timeout=300, env=env)
            for linie in (r.stdout or "").split():
                nume = linie.strip() + ".py"
                if nume in surse and nume not in reale:
                    reale.append(nume)
        except (OSError, subprocess.SubprocessError):
            pass
    return reale


def reface_din_bak(reasrc, rele):
    """Readuce fisierul original din .bak (patch-ul se poate reaplica curat).

    NU sterge _nv_patch_*.py: alea sunt implementarile patch-urilor. Daca le-as
    sterge, `from ._nv_patch_median import ...` ar da ImportError la importul
    audio.py si analiza ar muri imediat.
    """
    for nume in rele:
        f = Path(reasrc) / "rea_video" / nume
        bak = f.with_suffix(".py.bak")
        if bak.exists():
            try:
                f.write_bytes(bak.read_bytes())
            except OSError:
                pass


def dezactiveaza_patchuri(reasrc, rele):
    """Ultima solutie: lasa fisierele ORIGINALE. Mai lent, dar merge."""
    reface_din_bak(reasrc, rele)


PATCH_MEDIAN_FILE = """# -*- coding: utf-8 -*-
# PATCH (analiza-video): inlocuieste _median_filter din rea_video/audio.py.
# Motiv: varianta originala face sliding_window_view peste tot blocul inainte de
# bucla, deci un temporar (chunk, 513, 17) float32, plus inca unul la fel in
# np.median. Pe 19 minute de film = 3.2 GiB -> ArrayMemoryError, descompunerea moare.
# Aici fereastra de citire e (chunk, m, size) cu chunk ales dupa un buget de 32 MB.
import numpy as np


def _median_filter(a, size, axis, chunk=600):
    pad = size // 2
    if axis != 0:
        return _median_filter(a.T, size, 0, chunk).T
    n = a.shape[0]
    m = max(1, a.shape[1])
    maxim = max(1, int((32 * 1024 * 1024) // (m * size * 4)))
    chunk = max(1, min(chunk, maxim))
    padded = np.pad(a, ((pad, pad), (0, 0)), mode="edge")
    out = np.empty_like(a)
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        win = np.lib.stride_tricks.sliding_window_view(padded[s:e + 2 * pad], size, axis=0)
        out[s:e] = np.median(win, axis=-1)
    return out
"""


def _aplica_patch_median(reasrc, tacut=False):
    """Scrie _nv_patch_median.py si il face sa castige la finalul lui audio.py.

    De ce asa, si nu prin rescrierea functiei din audio.py: `reface_din_bak` readucea
    audio.py la varianta ORIGINALA, iar patch-ul se reaplica doar la urmatoarea
    pornire a analizei. Daca verificarea de patchuri dadea un fals negativ, analiza
    rula NEPATCH-UITA si crapa la 3.2 GiB exact ca inainte (asa s-a intamplat).
    Aici algoritmul greu sta in fisierul lui, iar audio.py primeste o singura linie
    la FINAL, deci numele castiga asupra definitiei de sus."""
    f_audio = Path(reasrc) / "rea_video" / "audio.py"
    f_impl = Path(reasrc) / "rea_video" / "_nv_patch_median.py"
    if not f_audio.exists():
        return False
    try:
        txt = f_audio.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    try:
        f_impl.write_text(PATCH_MEDIAN_FILE, encoding="utf-8")
    except OSError:
        return False

    marcaj = "from ._nv_patch_median import _median_filter"
    if marcaj in txt:
        return True

    if "def _median_filter" not in txt:
        return False

    adauga = ("\n\n# PATCH (analiza-video): varianta cu memorie limitata castiga peste cea de sus\n"
              + marcaj + "  # noqa: E402,F811\n")
    txt2 = txt.rstrip("\n") + "\n" + adauga
    try:
        compile(txt2, str(f_audio), "exec")
    except SyntaxError:
        return False
    try:
        f_audio.write_text(txt2, encoding="utf-8")
    except OSError:
        return False
    if not tacut:
        print("  rea-video: patch memorie audio instalat (_nv_patch_median.py)")
    return True


PATCH_FILTERS = r'''# -*- coding: utf-8 -*-
# PATCH (analiza-video): decodare pe placa video, cand placa stie codecul.
# build_track() decodifica INTREG videoul ca sa taie scenele. Pe AV1 fara ajutor
# hardware, ffmpeg foloseste doar 1-2 nuclee si merge cu ~80-130 cadre/s.
# GTX 1660 Super stie in hardware: H.264, HEVC, VP9. NU stie AV1 (abia RTX 30).
# Deci: daca codecul e suportat, decodam pe GPU. Daca nu, ramane pe CPU.
import os


def _hwaccel_args(cmd):
    """Argumente -hwaccel pentru comanda ffmpeg, sau [] daca nu ajuta."""
    if os.environ.get("ANALIZA_NO_HWACCEL"):
        return []
    try:
        import re
        import subprocess
        v = subprocess.run(["ffmpeg", "-hide_banner", "-version"],
                           capture_output=True, text=True).stdout
        if not re.search(r"--enable-(cuda|ffnvcodec|videotoolbox|d3d11va)", v):
            return []
        inp = None
        for i, a in enumerate(cmd):
            if a == "-i" and i + 1 < len(cmd):
                inp = cmd[i + 1]
                break
        if not inp:
            return []
        info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                               "-show_entries", "stream=codec_name", "-of", "csv=p=0", inp],
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return []
    codec = (info or "").split()[0].lower() if info else ""
    if os.name == "nt":
        # NVDEC stie h264 / hevc / vp9 pe Turing. AV1 doar de la RTX 30 incolo.
        if codec in ("h264", "hevc", "vp9"):
            return ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        return []
    return []


def _cu_hwaccel(cmd):
    """Comanda ffmpeg rescrisa cu -hwaccel inainte de -i si hwdownload inainte de -vf."""
    if "-hwaccel" in cmd:
        return cmd
    if "-i" not in cmd:
        return cmd
    adaug = _hwaccel_args(cmd)
    if not adaug:
        return cmd
    i = cmd.index("-i")
    nou = cmd[:i] + adaug + cmd[i:]
    if "-vf" in nou:
        j = nou.index("-vf")
        if j + 1 < len(nou):
            nou = nou[:j] + ["-vf", "hwdownload,format=nv12," + nou[j + 1]] + nou[j + 2:]
    return nou
'''


def _aplica_patch_viteza(reasrc, tacut=False):
    """Decodare pe GPU in iter_frames, plus fisierul de suport. Nu schimba logica."""
    f_media = Path(reasrc) / "rea_video" / "media.py"
    f_impl = Path(reasrc) / "rea_video" / "_nv_patch_ffmpeg.py"
    if not f_media.exists():
        return False
    try:
        txt = f_media.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    try:
        f_impl.write_text(PATCH_FILTERS, encoding="utf-8")
    except OSError:
        return False
    if "_nv_patch_ffmpeg" in txt:
        return True
    anc = "    frame_bytes = w * h * (1 if gray else 3)"
    if anc not in txt:
        return False
    ins = ("    # PATCH (analiza-video): decodare pe placa video cand codecul e suportat\n"
           "    try:\n"
           "        from ._nv_patch_ffmpeg import _cu_hwaccel\n"
           "        cmd = _cu_hwaccel(cmd)\n"
           "    except Exception:\n"
           "        pass\n")
    txt2 = txt.replace(anc, ins + anc, 1)
    try:
        compile(txt2, str(f_media), "exec")
    except SyntaxError:
        return False
    try:
        f_media.write_text(txt2, encoding="utf-8")
    except OSError:
        return False
    if not tacut:
        print("  rea-video: patch viteza instalat (decodare GPU cand e posibil)")
    return True


def patch_rea_video(reasrc, tacut=False):
    """Repara TREI lucruri din rea-video:
       1. _median_filter       - videouri lungi nu mai cer 3+ GB (audio.py)
       2. cadrele comprimate   - 1.6 GB tinuti in RAM -> ~200 MB (features.py)
       3. decodare pe GPU      - cand codecul e H.264/HEVC/VP9 (media.py)
    Aplicate o singura data. Fac copie .bak.
    """
    ok1 = _aplica_patch_median(reasrc, tacut)
    ok2 = patch_cadre(reasrc, tacut)
    ok3 = patch_gpu(reasrc, tacut)
    ok4 = _aplica_patch_viteza(reasrc, tacut)
    return ok1 and ok2 and ok4


def _patch_median(reasrc, tacut=False):
    """Repara _median_filter din rea-video (versiunea veche a patch-ului)."""
    f = Path(reasrc) / "rea_video" / "audio.py"
    if not f.exists():
        return False
    try:
        txt = f.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False

    if "PATCH: fereastra (chunk, m, size)" in txt:
        if not tacut:
            print("  rea-video: patch-ul de memorie e deja aplicat")
        return True

    # varianta originala are chunk fix si sliding_window_view peste tot blocul
    if "_median_filter" not in txt:
        return False

    import re as _re
    # scot functia veche (de la 'def _median_filter' pana la urmatoarea 'def ' de la nivel 0)
    m = _re.search(r"^def _median_filter\(.*?(?=^def )", txt, _re.S | _re.M)
    if not m:
        return False
    vechi = m.group(0)
    if "np.median(win, axis=-1)" not in vechi:
        return False

    bak = f.with_suffix(".py.bak")
    if not bak.exists():
        try:
            bak.write_bytes(f.read_bytes())
        except OSError:
            pass

    nou = txt[:m.start()] + PATCH_MEDIAN.strip() + "\n\n\n" + txt[m.end():]
    try:
        f.write_text(nou, encoding="utf-8")
    except OSError:
        return False

    if not tacut:
        print("  rea-video: PATCH aplicat - videouri lungi merg fara 3 GB de RAM")
    return True


# ---------------------------------------------------------------- raport markdown
def scrie_raport(cale_md, video, durata, fps, planuri, layere, stems, n_v, n_a):
    """Raport lizibil: ce e pe fiecare track si cat de sigur e."""
    f = float(fps or FPS_DEFAULT)
    L = []
    L.append("# PROIECT - cum a fost facut videoul\n")
    L.append("**Fisier:** `%s`  " % Path(video).name if video else "")
    L.append("**Durata:** %s  " % _tc(durata, f))
    L.append("**FPS:** %.2f  " % f)
    L.append("**Proiect:** `%s`\n" % Path(cale_md).with_suffix(".xml").name)
    L.append("Deschide `.xml` in FilmCraft: **File > Import**. Sau dublu-click pe "
             "`FILMCRAFT.bat`.\n")
    L.append("---\n")
    L.append("## Ce e pe fiecare track\n")
    L.append("| Track | Ce e | Clipuri | Sursa |")
    L.append("|---|---|---|---|")

    total_v = {}
    for tr, et, _ in V_TRACKS:
        if tr == "V1":
            c = len(planuri) or 1
            src = "masurat (detectie de taieturi)"
            sig = "M"
        else:
            c = len(layere.get(tr, []))
            src = "masurat (OCR / pixeli inghetati)" if c else "NIMIC GASIT"
            sig = "M" if c else "-"
        total_v[tr] = c
        L.append("| **%s** %s | %s | %d | %s |" % (tr, et, src, c, sig))

    mapare = {"original": "A1", "vocals": "A2", "music": "A3", "effects": "A4"}
    for tr, et, _ in A_TRACKS:
        gasit = any(mapare.get(k) == tr for k in stems)
        L.append("| **%s** %s | %s | %d | %s |"
                 % (tr, et, "separat de rea-video" if gasit else "n/a",
                    1 if gasit else 0, "M" if gasit else "-"))

    L.append("\nLegendă: **M** = măsurat de rea-video · **~** = inferat · "
             "**V** = ar avea nevoie de VLM (nu e pornit)\n")
    L.append("---\n")
    L.append("## Planurile (V1)\n")
    are_camera = any(p.get("camera") for p in planuri)
    if are_camera:
        L.append("| # | Început | Durată | Ce e | **Cameră** | Cadru |")
        L.append("|---|---|---|---|---|---|")
    else:
        L.append("| # | Început | Sfârșit | Durată | Ce e |")
        L.append("|---|---|---|---|---|")
    for i, p in enumerate(planuri[:60]):
        d = (p["end"] or durata) - (p["start"] or 0)
        if are_camera:
            L.append("| %d | %s | %.2fs | %s | %s | %s |"
                     % (i + 1, _tc(p["start"], f), d, p["eticheta"],
                        p.get("camera") or "-", p.get("framing") or "-"))
        else:
            L.append("| %d | %s | %s | %.2fs | %s |"
                     % (i + 1, _tc(p["start"], f), _tc(p["end"], f), d, p["eticheta"]))
    if len(planuri) > 60:
        L.append("| … | | | | încă %d planuri |" % (len(planuri) - 60))

    for tr, et, _ in V_TRACKS[1:]:
        arr = layere.get(tr, [])
        if not arr:
            continue
        L.append("\n## %s - %s\n" % (tr, et))
        L.append("| Început | Sfârșit | Ce e |")
        L.append("|---|---|---|")
        for c in arr[:40]:
            L.append("| %s | %s | %s |"
                     % (_tc(c.get("start"), f), _tc(c.get("end"), f),
                        (c.get("text") or c.get("eticheta") or "")[:70]))

    # ritmul: distributia duratelor
    if planuri:
        durs = sorted(((p["end"] or durata) - (p["start"] or 0)) for p in planuri)
        n = len(durs)
        med = durs[n // 2]
        L.append("\n## Ritmul (asta e cel mai usor de copiat)\n")
        L.append("| Ce | Valoare |")
        L.append("|---|---|")
        L.append("| planuri | %d |" % n)
        L.append("| planuri pe minut | %.1f |" % (n / (durata / 60.0) if durata else 0))
        L.append("| cel mai scurt | %.2fs |" % (durs[0] if durs else 0))
        L.append("| median | %.2fs |" % med)
        L.append("| cel mai lung | %.2fs |" % (durs[-1] if durs else 0))
        scurte = sum(1 for x in durs if x < 1.0)
        L.append("| sub 1 secunda | %d (%.0f%%) |"
                 % (scurte, 100.0 * scurte / n if n else 0))
        cameras = {}
        for p in planuri:
            c = (p.get("camera") or "").strip()
            if c:
                cameras[c] = cameras.get(c, 0) + 1
        if cameras:
            L.append("\n### Camera\n")
            L.append("| Tip | Cate planuri |")
            L.append("|---|---|")
            for c, k in sorted(cameras.items(), key=lambda x: -x[1]):
                L.append("| %s | %d |" % (c, k))

    L.append("\n---\n")
    L.append("## Ce NU pot afla dintr-un MP4 (nimeni nu poate)\n")
    L.append("- numele exact al presetarii din Premiere")
    L.append("- setarile de export (bitrate, codec) - se pot ghici, nu se pot citi")
    L.append("- ordinea exacta a layerelor din proiectul original")
    L.append("- plugin-urile folosite\n")
    L.append("Ce pot: **structura** - cate planuri, cat dureaza fiecare, "
             "unde sunt overlay-urile, ce sunete se aud, pe ce beat cad taieturile.\n")
    Path(cale_md).write_text("\n".join(L), encoding="utf-8")


# ---------------------------------------------------------------- intrare principala
def construieste(analiza_dir, video, iesire=None, ffprobe="ffprobe",
                 latime=1920, inaltime=1080, fps=None, durata=None, tacut=False,
                 ffmpeg=None):
    """Construieste proiectul multi-track din folderul de analiza.

    Returneaza (cale_xml, cale_md, statistici) sau (None, None, {}).
    """
    analiza_dir = Path(analiza_dir)
    if iesire is None:
        iesire = analiza_dir / "PROIECT.xml"
    iesire = Path(iesire)

    if fps is None:
        # incerc din breakdown, apoi din numele folderului, apoi implicit
        bd0 = citeste_breakdown(analiza_dir)
        fps = (bd0.get("fps") if isinstance(bd0, dict) else None) or FPS_DEFAULT
    fps = _fps(fps)

    if durata is None:
        durata = durata_audio(video, ffprobe) or 0.0

    bd = citeste_breakdown(analiza_dir)
    stems = gaseste_stems(analiza_dir)
    planuri, layere = layere_din_breakdown(bd)
    taieturi = taieturi_din_breakdown(bd, durata)
    sfx = evenimente_sfx(bd)
    beats = beat_uri(bd)

    # taie feliile din stem-ul de efecte - fiecare sunet separat pe A4
    felii = []
    if sfx and ffmpeg and "effects" in stems:
        try:
            felii = taie_felii(ffmpeg, stems["effects"], sfx,
                               Path(analiza_dir) / "stems" / "sfx")
        except Exception:
            felii = []

    # daca breakdown-ul n-a dat planuri, folosesc taieturile
    if not planuri and taieturi:
        marks = [0.0] + taieturi + [durata]
        for i in range(len(marks) - 1):
            if marks[i + 1] - marks[i] < 0.04:
                continue
            planuri.append({"start": marks[i], "end": marks[i + 1],
                            "eticheta": "plan", "sigur": False, "index": i + 1})

    # 1. varianta pentru FilmCraft: V2-V4 dezactivate -> gameplay-ul se vede curat
    n_v, n_a = scrie_proiect_fcpxml(
        iesire, video, durata, fps, planuri, layere, stems,
        latime=latime, inaltime=inaltime,
        nume=Path(video).stem if video else "Proiect",
        felii_sfx=felii, beats=beats, dezactiveaza_layere=True)

    # 2. varianta pentru Premiere: totul activ, ca sa vezi layerele suprapuse
    iesire_pp = iesire.with_name(iesire.stem + "-PREMIERE" + iesire.suffix)
    try:
        scrie_proiect_fcpxml(
            iesire_pp, video, durata, fps, planuri, layere, stems,
            latime=latime, inaltime=inaltime,
            nume=(Path(video).stem if video else "Proiect") + " (Premiere)",
            felii_sfx=felii, beats=beats, dezactiveaza_layere=False)
    except Exception:
        iesire_pp = None

    cale_md = iesire.with_suffix(".md")
    scrie_raport(cale_md, video, durata, fps, planuri, layere, stems, n_v, n_a)

    stats = {
        "planuri": len(planuri),
        "sfx_total": len(sfx),
        "sfx_felii": len(felii),
        "beats": len(beats),
        "V2": len(layere.get("V2", [])),
        "V3": len(layere.get("V3", [])),
        "V4": len(layere.get("V4", [])),
        "stems": list(stems.keys()),
        "trackuri_video": n_v,
        "trackuri_audio": n_a,
        "xml": str(iesire),
        "xml_premiere": str(iesire_pp) if iesire_pp else "",
        "md": str(cale_md),
    }
    if not tacut:
        print("  PROIECT FilmCraft : %s" % iesire)
        if iesire_pp:
            print("  PROIECT Premiere  : %s" % iesire_pp)
        print("  RAPORT  : %s" % cale_md)
        print("  %d planuri | %d track-uri video | %d track-uri audio"
              % (len(planuri), n_v, n_a))
        print("  %d sunete separate pe A4 | %d markere pe beat | stem-uri: %s"
              % (len(felii), len(beats), ", ".join(stems) or "niciunul"))
    return iesire, cale_md, stats


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Proiect FilmCraft multi-track dintr-o analiza rea-video")
    ap.add_argument("analiza", help="folderul cu breakdown.json + stems/")
    ap.add_argument("--video", required=True, help="fisierul .mp4 original")
    ap.add_argument("-o", "--out", default=None, help="unde scriu XML-ul")
    ap.add_argument("--fps", default=None)
    ap.add_argument("--durata", type=float, default=None)
    ap.add_argument("--latime", type=int, default=1920)
    ap.add_argument("--inaltime", type=int, default=1080)
    ap.add_argument("--ffmpeg", default=None, help="ffmpeg.exe (pentru feliile SFX)")
    a = ap.parse_args()
    x, m, s = construieste(a.analiza, a.video, a.out, fps=a.fps,
                           durata=a.durata, latime=a.latime, inaltime=a.inaltime,
                           ffmpeg=a.ffmpeg)
    sys.exit(0 if x else 1)
