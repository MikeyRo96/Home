#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALIZEAZA UN VIDEO DE PE YOUTUBE - ce e in el si cum a fost facut
==================================================================
Rulezi:
    python analizeaza.py "https://youtube.com/watch?v=..."
    python analizeaza.py C:\\film.mp4

Ce face, in ordine:
    1. descarca videoul (yt-dlp) daca primesti link
    2. instaleaza rea-video o singura data (in .venv, ~600 MB)
    3. ruleaza descompunerea shot-cu-shot  -> report.html
    4. ruleaza inspecteaza.py              -> .edl / .xml / markere / capitole

Rezultatul e in folderul "analiza-<nume>".
"""

import os
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from pathlib import Path

AICI = Path(__file__).resolve().parent
CACHE = Path(os.environ.get("REA_CACHE") or
             (Path(os.environ["LOCALAPPDATA"]) / "rea-video-tool"
              if os.name == "nt" else Path.home() / ".cache" / "rea-video-tool"))
if os.environ.get("REA_CACHE"):
    CACHE.mkdir(parents=True, exist_ok=True)
REA_ZIP = "https://codeload.github.com/JuneYaooo/rea-video/zip/refs/heads/main"


def log(msg=""):
    print(msg, flush=True)


def titlu(t):
    log("\n" + "=" * 66)
    log("  " + t)
    log("=" * 66)


def ruleaza(cmd, **kw):
    log("  > " + " ".join(str(c) for c in cmd)[:160])
    return subprocess.run([str(c) for c in cmd], **kw)


def gaseste(nume):
    """Cauta un executabil pe PATH, apoi in folderul de cache."""
    p = shutil.which(nume)
    if p:
        return p
    for c in CACHE.glob("**/" + nume):
        return str(c)
    return None


def cere_ffmpeg():
    exe = gaseste("ffmpeg")
    if exe:
        return os.path.dirname(exe)
    try:
        import imageio_ffmpeg  # pip install imageio-ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and Path(p).exists():
            for n in ("ffmpeg", "ffprobe"):
                dst = CACHE / "bin" / (n + (".exe" if os.name == "nt" else ""))
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(p, dst)
                os.chmod(dst, 0o755)
            return str(CACHE / "bin")
    except Exception:
        pass
    titlu("Descarc ffmpeg (~150 MB, o singura data)")
    CACHE.mkdir(parents=True, exist_ok=True)
    zp = CACHE / "ff.zip"
    ruleaza([sys.executable, "-c",
             "import urllib.request,sys;"
             "urllib.request.urlretrieve(sys.argv[1], sys.argv[2])",
             "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
             "ffmpeg-master-latest-win64-gpl.zip", str(zp)],
            check=True)
    with zipfile.ZipFile(zp) as z:
        z.extractall(CACHE / "ff")
    zp.unlink(missing_ok=True)
    for d in (CACHE / "ff").glob("ffmpeg-*/bin"):
        return str(d)
    sys.exit("  ffmpeg nu s-a dezarhivat cum trebuie.")


def cere_ytdlp():
    exe = gaseste("yt-dlp")
    if exe and not exe.endswith(".exe"):
        return exe
    dest = CACHE / "yt-dlp.exe"
    if dest.exists():
        return str(dest)
    titlu("Descarc yt-dlp (~17 MB, o singura data)")
    CACHE.mkdir(parents=True, exist_ok=True)
    ruleaza([sys.executable, "-c",
             "import urllib.request,sys;"
             "urllib.request.urlretrieve(sys.argv[1], sys.argv[2])",
             "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe",
             str(dest)], check=True)
    return str(dest)


def nume_sigur(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9 _.-]+", "", s).strip()
    return (s[:60] or "video").replace(" ", "-")


def descarca(url, ytdlp):
    titlu("Descarc videoul (max 1080p)")
    tpl = str(CACHE / "download" / "%(title).70s.%(ext)s")
    (CACHE / "download").mkdir(parents=True, exist_ok=True)
    inainte = set((CACHE / "download").glob("*.mp4"))
    r = ruleaza([ytdlp, "-f", "bv*[height<=1080]+ba/b[height<=1080]",
                 "--merge-output-format", "mp4", "-o", tpl, url])
    if r.returncode != 0:
        sys.exit("  Descarcarea a esuat. Link corect? Videoul e privat?")
    noi = sorted(set((CACHE / "download").glob("*.mp4")) - inainte,
                 key=lambda p: p.stat().st_mtime, reverse=True)
    if not noi:
        toate = sorted((CACHE / "download").glob("*.mp4"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        if not toate:
            sys.exit("  yt-dlp nu a produs niciun mp4.")
        return toate[0]
    return noi[0]


def instaleaza_rea():
    """Returneaza calea catre rea-video.exe (sau None daca nu s-a putut)."""
    exe = CACHE / "src" / ".venv" / "Scripts" / "rea-video.exe"
    if exe.exists():
        return exe
    titlu("Instalez rea-video (prima data, 3-6 min, ~600 MB)")
    src = CACHE / "src"
    if not (src / "rea_video").is_dir():
        src.mkdir(parents=True, exist_ok=True)
        zp = CACHE / "rea.zip"
        log("  descarc sursa...")
        ruleaza([sys.executable, "-c",
                 "import urllib.request,sys;"
                 "urllib.request.urlretrieve(sys.argv[1], sys.argv[2])",
                 REA_ZIP, str(zp)], check=True)
        with zipfile.ZipFile(zp) as z:
            z.extractall(CACHE)
        zp.unlink(missing_ok=True)
        for d in CACHE.glob("rea-video-*"):
            if (d / "pyproject.toml").exists():
                d.rename(src) if not src.exists() else None
                break
    py = src / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        ruleaza([sys.executable, "-m", "venv", src / ".venv"], check=True)
        py = src / ".venv" / "Scripts" / "python.exe"
    ruleaza([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    r = ruleaza([py, "-m", "pip", "install", "-q", "-e", f"{src}[ocr]"])
    if r.returncode != 0:
        log("  [!] instalarea a esuat. Incearca din nou; daca pica iar, "
            "spune-mi ce scrie mai sus.")
        return None
    return exe if exe.exists() else None


def analizeaza(rea, video, out):
    titlu("Descompun shot cu shot (3-15 min)")
    cmd = [rea, "decompose", video, "--lang", "en", "-o", out, "--no-vlm"]
    log("  (fara VLM: verdictul filmat/AI e din statistici de pixeli)");
    r = ruleaza(cmd)
    if r.returncode != 0:
        log("  [!] rea-video a eșuat. Vezi mesajul de mai sus.")


def inspecteaza(video, out):
    titlu("Scot taieturi: EDL / XML / markere / capitole")
    script = AICI / "inspecteaza.py"
    if not script.exists():
        log("  [!] lipseste inspecteaza.py langa analizeaza.py")
        return
    r = ruleaza([sys.executable, str(script), video])
    if r.returncode != 0:
        log("  [!] inspecteaza.py a eșuat (ai ffmpeg pe PATH?)")


def main():
    if len(sys.argv) < 2:
        log("\n  Utilizare:")
        log('    python analizeaza.py "https://youtube.com/watch?v=..."')
        log("    python analizeaza.py C:\\film.mp4")
        log("  (sau trage fisierul peste ANALIZEAZA-VIDEO.bat)\n")
        return 1

    sursa = sys.argv[1].strip().strip('"')

    for exe in ("ffmpeg", "ffprobe"):
        if not gaseste(exe):
            bindir = cere_ffmpeg()
            os.environ["PATH"] = bindir + os.pathsep + os.environ["PATH"]
            break

    if re.match(r"^https?://", sursa):
        video = descarca(sursa, cere_ytdlp())
    else:
        video = Path(sursa)
        if not video.exists():
            sys.exit(f"  Nu exista fisierul: {sursa}")

    video = Path(video).resolve()
    log(f"\n  Fisier: {video}  ({video.stat().st_size/1e6:.0f} MB)")

    out = AICI / ("analiza-" + nume_sigur(video.stem))
    out.mkdir(parents=True, exist_ok=True)

    rea = instaleaza_rea()
    if rea:
        analizeaza(rea, str(video), str(out))
    else:
        log("\n  Sar peste rea-video (instalare nereusita). Rulez doar inspecteaza.py.")

    inspecteaza(str(video), str(out))

    titlu("GATA")
    for f in sorted(out.glob("*")):
        log(f"  {f.name}")
    for f in (out / "report.html", video.with_suffix(".edl"), video.with_suffix(".xml")):
        if f.exists():
            log(f"\n  deschide: {f}")
            if os.name == "nt":
                os.startfile(str(f))  # noqa
            break
    if not any(out.glob("**/report.html")):
        log("\n  Raportul rea-video nu a aparut. Verifica mesajele de mai sus.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit("\n  oprit.")
