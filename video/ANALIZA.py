#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
O SINGURA APLICATIE - analiza un video de pe YouTube
====================================================
Dublu-click pe RULEAZA.bat. Nu trebuie sa stii nimic altceva.

Face, in ordine:
  1. isi instaleaza tot ce ii trebuie (Python, ffmpeg, ffprobe, yt-dlp, rea-video)
  2. descarca videoul de pe YouTube (sau primeste un fisier local)
  3. descarca de pe YouTube
  4. ruleaza rea-video  -> report.html  (shot cu shot: filmat / AI / 3D / cod)
  5. scoate taieturi   -> .edl .xml .csv .txt  (pentru FilmCraft / Premiere)
  6. deschide raportul in browser

Totul sta in %LOCALAPPDATA%\\AnalizaVideo . Nu atinge nimic altceva.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

# ------------------------------------------------------------------ constante
PY_URL = ("https://github.com/astral-sh/python-build-standalone/releases/download/"
          "20261124/cpython-3.12.16+20261124-x86_64-pc-windows-msvc-install_only.tar.gz")
YT_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
REA_URL = "https://codeload.github.com/JuneYaooo/rea-video/zip/refs/heads/main"

AICI = Path(__file__).resolve().parent
sys.path.insert(0, str(AICI))
CACHE = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "AnalizaVideo"
PYDIR = CACHE / "python"
FFBIN = CACHE / "bin"
YTDLP = FFBIN / "yt-dlp.exe"
REASRC = CACHE / "rea-src"
FCDIR = CACHE / "filmcraft"
DL = CACHE / "download"

if os.name != "nt":
    CACHE = Path.home() / ".cache" / "AnalizaVideo"
    PYDIR, FFBIN, YTDLP, REASRC, DL = (CACHE / "python", CACHE / "bin",
                                      CACHE / "bin" / "yt-dlp", CACHE / "rea-src",
                                      CACHE / "download")

WIN = os.name == "nt"
PYEXE = PYDIR / ("python.exe" if WIN else "bin/python3")


PAUZA = True
_GPU_OK = False


def log(t=""):
    print(t, flush=True)


def asteapta():
    if not PAUZA:
        return
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\n  Enter ca sa inchizi...")
    except Exception:
        pass


def setari_viteza():
    """Foloseste TOATE nucleele si prioritate maxima. Intoarce (nuclee, thread-uri)."""
    nuclee = os.cpu_count() or 4
    # variabilele citite de numpy / onnxruntime / opencv / torch
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
              "OMP_WAIT_POLICY", "KMP_BLOCKTIME"):
        if k == "OMP_WAIT_POLICY":
            os.environ[k] = "PASSIVE"
        elif k == "KMP_BLOCKTIME":
            os.environ[k] = "0"
        else:
            os.environ[k] = str(nuclee)
    # NU fortez REA_VIDEO_THREADS. rea-video isi alege singur nucleele FIZICE
    # (util.model_threads -> _fast_cores, plafonat la MAX_MODEL_THREADS=8).
    # Cand am fortat eu (toate nucleele, apoi ///2) modelele s-au batut cu analiza
    # cadrelor pe aceleasi nuclee si a iesit OutOfMemory. Il las pe el.
    os.environ.pop("REA_VIDEO_THREADS", None)
    # prioritate maxima: procesul si copiii lui
    if WIN:
        try:
            import ctypes
            from ctypes import wintypes

            HIGH_PRIORITY_CLASS = 0x00000080
            h = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(h, HIGH_PRIORITY_CLASS)
            # si pentru copii: creez un Job Object? simplu: seteaza la fiecare Popen cu creationflags
        except Exception:
            pass
    else:
        try:
            os.nice(-10)
        except (OSError, PermissionError):
            pass
    return nuclee


def cflags_prioritate():
    """Flag-uri pentru subprocess: prioritate mare pe Windows."""
    if not WIN:
        return 0
    try:
        # BELOW_NORMAL=0x4000, NORMAL=0x20, ABOVE_NORMAL=0x8000, HIGH=0x80
        return 0x00000080  # HIGH_PRIORITY_CLASS
    except Exception:
        return 0


def nume_gpu():
    """Ce placa video am. Pe Windows intreb sistemul; altfel None."""
    if not WIN:
        return None
    try:
        import subprocess as _sp
        r = _sp.run(["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True, text=True, timeout=30)
        nume = [l.strip() for l in r.stdout.splitlines()
                if l.strip() and "Name" not in l]
        if nume:
            return nume[0]
    except Exception:
        pass
    return None


# Verific daca CUDA CHIAR merge, nu doar apare in lista de provideri.
# (get_available_providers() arata CUDA si cand DLL-urile lipsesc -> ai crede ca
#  merge pe placa video, iar de fapt totul ruleaza pe CPU.)
TEST_CUDA = r"""
import glob, os, sys
for baza in sys.path:
    if baza:
        for d in glob.glob(os.path.join(baza, "nvidia", "*", "bin")):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(d)
            except Exception:
                pass
import numpy as np, onnxruntime as o
from onnx import TensorProto, helper
x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 64, 64])
y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 64, 64])
g = helper.make_graph([helper.make_node("MatMul", ["X", "X"], ["Y"])], "t", [x], [y])
m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 13)])
m.ir_version = 9
import tempfile
p = os.path.join(tempfile.gettempdir(), "rea_test_gpu.onnx")
onnx.save(m, p)
s = o.InferenceSession(p, providers=[("CUDAExecutionProvider", {"device_id": 0})])
act = s.get_providers()
if "CUDAExecutionProvider" not in act:
    print("NU"); raise SystemExit(2)
s.run(None, {"X": np.random.rand(1, 64, 64).astype(np.float32)})
print("DA " + act[0])
"""

# verificarea are nevoie de pachetul `onnx` doar ca sa construiasca un model de test
TEST_CUDA = TEST_CUDA.replace(
    "import numpy as np, onnxruntime as o\nfrom onnx import TensorProto, helper",
    "import numpy as np, onnx, onnxruntime as o\ntry:\n    from onnx import TensorProto, helper\n"
    "except ImportError:\n    print('NU - lipseste pachetul onnx'); raise SystemExit(2)")



def asigura_gpu():
    """Instaleaza onnxruntime-gpu daca ai placa NVIDIA. Cade lin pe CPU daca nu."""
    global _GPU_OK
    if PYEXE.exists():
        # deja instalat SI chiar merge?
        try:
            r = py("-c", TEST_CUDA, capture_output=True, text=True, timeout=300)
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            if r.returncode == 0 and out.startswith("DA"):
                log("  GPU: ACTIV - deja instalat si functional")
                _GPU_OK = True
                return True
        except Exception:
            pass

    gpu = nume_gpu()
    if not gpu:
        log("  GPU: nu detectez placa video (sau nu e NVIDIA)")
        return False
    log(f"  GPU: {gpu}")
    if not any(k in gpu.upper() for k in ("NVIDIA", "GEFORCE", "RTX", "GTX", "QUADRO",
                                          "TESLA", "RADEON", "INTEL", "ARC", "UHD")):
        log("  GPU: nu recunosc placa, merg pe CPU")
        return False

    titlu("GPU: instalez onnxruntime-gpu + CUDA 12 (o singura data, ~2 GB)")
    log("  (nu trebuie sa instalezi tu nimic din toolkit-ul NVIDIA)")
    try:
        py("-m", "pip", "install", "-q", "-U", "pip", capture_output=True, timeout=600)
        # 1.24.4 = ultima varianta care cere CUDA 12 (CUDA 13 n-are pachete Windows)
        r = py("-m", "pip", "install", "-q", "onnxruntime-gpu==1.24.4",
               capture_output=True, text=True, timeout=1800)
        if r.returncode != 0:
            log("  [!] onnxruntime-gpu nu s-a instalat, merg pe CPU")
            return False
        log("  acum CUDA + cuDNN (librariile, ca pachete pip)...")
        # versiunile care AU build Windows; cublas 12.9.3.13 nu are
        for pachet in ("onnx",
                       "nvidia-cuda-runtime-cu12==12.9.79",
                       "nvidia-cublas-cu12==12.9.2.10",
                       "nvidia-cufft-cu12==11.4.1.4",
                       "nvidia-cudnn-cu12==9.28.1.4"):
            py("-m", "pip", "install", "-q", pachet,
               capture_output=True, text=True, timeout=1800)
        # nu ma uit doar la lista de provideri - CHIAR rulez ceva pe placa video
        r2 = py("-c", TEST_CUDA, capture_output=True, text=True, timeout=300)
        out = ((r2.stdout or "") + (r2.stderr or "")).strip()
        if r2.returncode == 0 and out.startswith("DA"):
            log(f"  GPU: ACTIV ({out[3:]}) - separea sunetului merge pe placa video")
            _GPU_OK = True
            return True
        log("  [!] CUDA nu s-a activat, merg pe CPU (nu blocheaza nimic)")
        # arat motivul REAL, nu "instaleaza driverul" din reflex
        for linie in out.splitlines():
            if "which is missing" in linie or "Error loading" in linie:
                log("      motiv: " + linie[-120:])
                break
        else:
            log("      motiv: " + (out.splitlines()[-1][:120] if out else "necunoscut"))
        log("      daca vrei GPU: instaleaza driverul NVIDIA, apoi ruleaza din nou")
    except Exception as e:
        log(f"  [!] GPU: {e}")
    return False


def ram_mb():
    """RAM liber in MB. Pe Windows intreb sistemul; pe altceva intorc None."""
    try:
        if WIN:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MEMORYSTATUSEX()
            st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
                return int(st.ullAvailPhys // 1048576), int(st.ullTotalPhys // 1048576)
    except Exception:
        pass
    return None, None


def titlu(t):
    log()
    log("=" * 66)
    log("  " + t)
    log("=" * 66)


def _get(url, timeout=180):
    import ssl
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
    })
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def descarca(url, dest, eticheta):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        log(f"  {eticheta}: deja descarcat")
        return dest
    for incercare in (1, 2, 3):
        try:
            log(f"  {eticheta}: descarc" + (f" (incercarea {incercare})" if incercare > 1 else "") + "...")
            with _get(url) as r, open(dest, "wb") as f:
                total = int(r.headers.get("Content-Length") or 0)
                citit = 0
                ultim = 0
                while True:
                    b = r.read(262144)
                    if not b:
                        break
                    f.write(b)
                    citit += len(b)
                    if total and citit - ultim > 5_000_000:
                        log(f"    {citit/1e6:.0f} / {total/1e6:.0f} MB")
                        ultim = citit
            log(f"    gata: {dest.stat().st_size/1e6:.1f} MB")
            return dest
        except Exception as e:
            log(f"    [!] {type(e).__name__}: {str(e)[:100]}")
            if dest.exists():
                dest.unlink(missing_ok=True)
            if incercare == 3:
                raise
            import time
            time.sleep(3)
    return dest



# ------------------------------------------------------------------ 1. PYTHON
def asigura_python():
    if PYEXE.exists():
        log("  Python: deja instalat")
        return True
    # refolosesc Python-ul pus de instalerele vechi (nu descarc iar 47 MB)
    for vechi in (Path(os.environ.get("LOCALAPPDATA", "")) / "py312",
                  Path(os.environ.get("LOCALAPPDATA", "")) / "AnalizaVideo" / "py312"):
        try:
            if (vechi / ("python.exe" if WIN else "bin/python3")).exists():
                log(f"  Python: il refolosesc pe cel existent ({vechi})")
                if PYDIR.exists():
                    shutil.rmtree(PYDIR, ignore_errors=True)
                shutil.copytree(vechi, PYDIR)
                return PYEXE.exists()
        except Exception:
            pass
    titlu("[1/6] Python 3.12 (o singura data, 47 MB)")
    tgz = CACHE / "py.tgz"
    try:
        descarca(PY_URL, tgz, "python")
        tmp = CACHE / "_pyx"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        with tarfile.open(tgz) as t:
            t.extractall(tmp)
        src = tmp / "python"
        if not src.exists():
            src = next(tmp.iterdir())
        if PYDIR.exists():
            shutil.rmtree(PYDIR)
        shutil.copytree(src, PYDIR)
        shutil.rmtree(tmp, ignore_errors=True)
        tgz.unlink(missing_ok=True)
    except Exception as e:
        log(f"  [!] Python nu s-a instalat: {e}")
        return False
    return PYEXE.exists()


def py(*args, **kw):
    return subprocess.run([str(PYEXE)] + [str(a) for a in args], **kw)


# ------------------------------------------------------------------ 2. FFMPEG
def asigura_ffmpeg():
    if (FFBIN / ("ffmpeg.exe" if WIN else "ffmpeg")).exists():
        log("  ffmpeg: deja instalat")
        return True
    titlu("[2/6] ffmpeg + ffprobe (o singura data, 40 MB)")
    # incerc 1: iau asset-ul REAL din API (URL-ul fix "latest/download" da 404)
    try:
        import json
        tmp = CACHE / "_ff"
        zp = CACHE / "ff.zip"
        api = "https://api.github.com/repos/GyanD/codexffmpeg/releases/latest"
        ureq = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(ureq, timeout=60))
        log(f"  versiune noua: {d.get('tag_name', '?')}")
        # essentials are ffmpeg + ffprobe, ~120 MB
        a = next((x for x in d["assets"] if "essentials_build.zip" in x["name"]), None)
        if not a:
            a = next((x for x in d["assets"] if x["name"].endswith(".zip")), None)
        if not a:
            raise RuntimeError("niciun .zip in release")
        log(f"  iau: {a['name']} ({a['size'] // 1048576} MB)")
        descarca(a["browser_download_url"], zp, "ffmpeg")
        if tmp.exists():
            shutil.rmtree(tmp)
        with zipfile.ZipFile(zp) as z:
            z.extractall(tmp)
        FFBIN.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in tmp.rglob("ff*.exe" if WIN else "ff*"):
            if p.name.lower().startswith(("ffmpeg", "ffprobe")):
                shutil.copy(p, FFBIN / p.name)
                n += 1
        shutil.rmtree(tmp, ignore_errors=True)
        zp.unlink(missing_ok=True)
        log(f"    copiat: {n} binare")
        if n >= 2:
            return True
    except Exception as e:
        log(f"  [!] ffmpeg complet a esuat: {e}")


    # plan B: imageio-ffmpeg prin pip (doar ffmpeg, fara ffprobe)
    log("  plan B: ffmpeg prin pip...")
    try:
        py("-m", "ensurepip", "--upgrade")
        py("-m", "pip", "install", "-q", "--upgrade", "imageio-ffmpeg")
        py("-c", ("import imageio_ffmpeg,os,shutil,pathlib;"
                  "p=imageio_ffmpeg.get_ffmpeg_exe();"
                  f"d=pathlib.Path(r'{FFBIN}');d.mkdir(parents=True,exist_ok=True);"
                  "shutil.copy(p,d/'ffmpeg.exe' if os.name=='nt' else d/'ffmpeg')"))
        log("    ffmpeg prin pip: gata (fara ffprobe - scriptul are plan B)")
        return (FFBIN / ("ffmpeg.exe" if WIN else "ffmpeg")).exists()
    except Exception as e:
        log(f"  [!] si planul B a esuat: {e}")
        return False


# ------------------------------------------------------------------ 3. YT-DLP
def asigura_ytdlp():
    if YTDLP.exists():
        log("  yt-dlp: deja instalat")
        return True
    titlu("[3/6] yt-dlp (o singura data, 23 MB)")
    try:
        descarca(YT_URL, YTDLP, "yt-dlp")
        if not WIN:
            os.chmod(YTDLP, 0o755)
        return True
    except Exception as e:
        log(f"  [!] yt-dlp nu s-a descarcat: {e}")
        return False


# ------------------------------------------------------------------ 4. REA
def asigura_rea():
    marker = REASRC / "pyproject.toml"
    if marker.exists():
        log("  rea-video: deja instalat")
        return True
    titlu("[4/6] rea-video (o singura data, 5-10 min, ~600 MB)")
    try:
        zp = CACHE / "rea.zip"
        descarca(REA_URL, zp, "rea-video")
        tmp = CACHE / "_rea"
        if tmp.exists():
            shutil.rmtree(tmp)
        with zipfile.ZipFile(zp) as z:
            z.extractall(tmp)
        inner = next(p for p in tmp.iterdir() if (p / "pyproject.toml").exists())
        if REASRC.exists():
            shutil.rmtree(REASRC)
        shutil.move(str(inner), str(REASRC))
        shutil.rmtree(tmp, ignore_errors=True)
        zp.unlink(missing_ok=True)
        log("    sursa dezarhivata")
        log("    instalez pachetele (dureaza)...")
        py("-m", "ensurepip", "--upgrade", capture_output=True)
        py("-m", "pip", "install", "-q", "--upgrade", "pip", capture_output=True)
        r = py("-m", "pip", "install", "-q", "-e", f"{REASRC}[ocr]")
        if r.returncode != 0:
            log("  [!] pip install a esuat")
            return False
        log("    rea-video instalat")
        return True
    except Exception as e:
        log(f"  [!] rea-video nu s-a instalat: {e}")
        return False


# ------------------------------------------------------------------ 5. VIDEO
def nume_sigur(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9 _.-]+", "", s).strip()
    return (s[:60] or "video").replace(" ", "-")


def e_fisier(s):
    """True daca s e o cale de fisier care exista (accepta ghilimele, spatii, backslash)."""
    s = str(s).strip().strip('"').strip("'")
    if s.lower().startswith("file://"):
        s = s[7:]
    if not s:
        return None
    try:
        p = Path(s).expanduser()
        if p.exists() and p.is_file():
            return p.resolve()
    except (OSError, ValueError):
        pass
    return None


def ia_videoul(sursa):
    titlu("[5/6] videoul")
    local = e_fisier(sursa)
    if local:
        log(f"  fisier local: {local}")
        return local
    sursa = str(sursa).strip().strip('"').strip("'")
    if not re.match(r"^https?://", sursa, re.I):
        log(f"  [!] nu e link si nu e fisier existent: {sursa}")
        log("      verifica daca ai lipit corect (fara ghilimele, cu .mp4 la final)")
        return None

    DL.mkdir(parents=True, exist_ok=True)
    inainte = set(DL.glob("*.mp4"))
    # VITEZA: YouTube da AV1 pe 1080p, iar GTX 1660 Super NU are decodor AV1
    # (AV1 a aparut in NVDEC abia la RTX 30). Cu AV1, ffmpeg decodifica DOAR pe CPU,
    # pe 1-2 nuclee: ~82 cadre/s la 1080p60 -> 14 min doar taierea scenelor.
    # H.264 (avc1) se decodeaza in hardware pe orice GTX 16xx -> de cateva ori mai repede.
    log("  descarc de pe YouTube (max 1080p, H.264 ca sa mearga pe placa video)...")
    cmd = [str(YTDLP),
           "-f", "bv*[height<=1080][vcodec^=avc1]+ba/bv*[height<=1080][vcodec^=avc1]+ba/b[height<=1080]/b",
           "--merge-output-format", "mp4", "-o", str(DL / "%(title).80s.%(ext)s"),
           "--no-playlist", sursa]
    env = os.environ.copy()
    env["PATH"] = str(FFBIN) + os.pathsep + env.get("PATH", "")
    r = subprocess.run(cmd, env=env)
    if r.returncode != 0:
        log("  [!] descarcarea a esuat")
        log("      daca YouTube cere verificare, incearca:")
        log(f'      "{YTDLP}" --cookies-from-browser chrome "{sursa}"')
        return None
    noi = sorted(set(DL.glob("*.mp4")) - inainte, key=lambda p: p.stat().st_mtime, reverse=True)
    if not noi:
        noi = sorted(DL.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not noi:
        log("  [!] nu gasesc mp4 descarcat")
        return None
    log(f"  gata: {noi[0].name}")
    return noi[0]


def pregateste_pentru_gpu(video):
    """Daca videoul e AV1, il convertesc o singura data in H.264.

    GTX 1660 Super nu are decodor AV1 in hardware. AV1 se decodifica doar pe CPU,
    pe 1-2 nuclee, deci taierea scenelor dureaza de cateva ori mai mult.
    Conversia se face cu av1 -> h264 pe GPU (NVENC), o singura data, si se pastreaza
    langa original cu sufixul -.h264.mp4. La a doua rulare pe acelasi film: 0 secunde.
    """
    if not video or not Path(video).exists():
        return video
    try:
        env = os.environ.copy()
        env["PATH"] = str(FFBIN) + os.pathsep + env.get("PATH", "")
        r = subprocess.run([str(FFBIN / "ffprobe"),
                            "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True, env=env)
        codec = (r.stdout or "").strip().split()[0].lower() if r.stdout.strip() else ""
    except Exception:
        return video
    if codec != "av1":
        return video

    din = Path(video)
    in_cache = din.with_name(din.stem + "-h264.mp4")
    if in_cache.exists() and in_cache.stat().st_size > 1000:
        log("  filmul e AV1 (placa video nu stie AV1) - folosesc copia H.264 deja facuta")
        return in_cache

    # SPUNE CLAR ce e activ - altfel nu stiu de ce e lent sau de ce a crapat
    try:
        import proiect as _P
        _au = (REASRC / "rea_video" / "audio.py")
        _me = (REASRC / "rea_video" / "media.py")
        if _au.exists() and _me.exists():
            _t_au = _au.read_text(encoding="utf-8", errors="replace")
            _t_me = _me.read_text(encoding="utf-8", errors="replace")
            log(f"  patch memorie  : {'ACTIV' if '_nv_patch_median' in _t_au else 'INACTIV (!)'}")
            log(f"  patch viteza   : {'ACTIV' if '_nv_patch_ffmpeg' in _t_me else 'INACTIV'}")
            log(f"  patch cadre    : {'ACTIV' if 'class _LazyFrames' in (REASRC / 'rea_video' / 'features.py').read_text(encoding='utf-8', errors='replace') else 'INACTIV'}")
    except Exception:
        pass

    liber, tot = ram_mb()
    if liber and liber < 500:
        log("  [!] film AV1 si RAM putin - sar peste conversie, merg pe procesor")
        return video

    log("  filmul e AV1. Placa video NU stie AV1 (abia RTX 30 stie).")
    log("  il convertesc o singura data in H.264 ca sa mearga pe placa video...")
    cmd = [str(FFBIN / "ffmpeg"), "-v", "error", "-y", "-i", str(din),
           "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "19", "-bf", "3",
           "-c:a", "copy", "-movflags", "+faststart", str(in_cache)]
    try:
        r = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if r.returncode != 0 or not in_cache.exists():
            # fara NVENC pe acest PC: incerc pe CPU, mai lent dar merge
            log("  (NVENC nu a mers, convertesc pe procesor - dureaza cateva minute)")
            cmd[cmd.index("h264_nvenc")] = "libx264"
            cmd[cmd.index("-preset") + 1] = "veryfast"
            cmd[cmd.index("-cq")] = "-crf"
            cmd[cmd.index("-crf") + 1] = "20"
            r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    except Exception as e:
        log(f"  [!] conversia a esuat: {e}")
        return video
    if in_cache.exists() and in_cache.stat().st_size > 1000:
        log(f"  gata conversia: {in_cache.name} (o singura data per film)")
        return in_cache
    log("  [!] conversia a esuat - merg pe procesor cu AV1-ul original")
    return video


# ------------------------------------------------------------------ 7. FILMCRAFT
def asigura_filmcraft():
    """FilmCraft portable (108 MB, fara instalare, fara admin)."""
    exe = None
    if FCDIR.exists():
        for c in FCDIR.rglob("filmcraft*.exe"):
            if c.is_file() and c.parent != FCDIR:
                exe = c
                break
        if not exe:
            for c in FCDIR.rglob("FilmCraft*.exe"):
                exe = c
                break
    if exe:
        log(f"  FilmCraft: deja instalat ({exe.name})")
        return exe

    titlu("[7/7] FilmCraft portable (108 MB, fara instalare)")
    try:
        import json
        api = "https://api.github.com/repos/storytold/filmcraft/releases/latest"
        ureq = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(ureq, timeout=60))
        a = next((x for x in d["assets"] if "windows-x64-portable.zip" in x["name"]), None)
        if not a:
            log("  [!] nu gasesc versiunea Windows portable")
            return None
        log(f"  versiunea: {d.get('tag_name', '?')} ({a['size'] // 1048576} MB)")
        zp = CACHE / "filmcraft.zip"
        descarca(a["browser_download_url"], zp, "FilmCraft")
        if FCDIR.exists():
            shutil.rmtree(FCDIR, ignore_errors=True)
        FCDIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zp) as z:
            z.extractall(FCDIR)
        zp.unlink(missing_ok=True)
        for c in FCDIR.rglob("*.exe"):
            if c.is_file():
                exe = c
                break
        if exe:
            log(f"    gata: {exe}")
            return exe
        log("  [!] zip dezarhivat dar nu gasesc .exe")
        return None
    except Exception as e:
        log(f"  [!] FilmCraft nu s-a instalat: {e}")
        return None


def alege_proiect(p):
    """Dintre mai multe .xml, prefer 'PROIECT.xml' (varianta pentru FilmCraft)."""
    p = Path(p)
    if p.is_file():
        return p
    if p.is_dir():
        cand = sorted(p.glob("PROIECT*.xml"))
        for c in cand:
            if "PREMIERE" not in c.name.upper():
                return c
        cand = sorted(p.glob("*.xml"))
        if cand:
            return cand[0]
    return None


def deschide_filmcraft_cu_xml(xml):
    """Porneste FilmCraft si incarca timeline-ul din XML."""
    if not xml or not Path(xml).exists():
        return False
    exe = asigura_filmcraft()
    if not exe:
        return False
    try:
        log("  pornesc FilmCraft cu timeline-ul tau...")
        if WIN:
            subprocess.Popen([str(exe), str(xml)], cwd=str(Path(exe).parent))
        else:
            subprocess.Popen([str(exe), str(xml)])
        return True
    except Exception as e:
        log(f"  [!] FilmCraft nu a pornit: {e}")
        log(f"      deschide-l manual: {exe}")
        return False


# ------------------------------------------------------------------ 6. ANALIZA
def descompune(video, out, durata_video=None):
    titlu("[6/6] descompunere shot cu shot (5-15 min)")
    # REPARATIE: rea-video cere 3+ GB de RAM la videouri lungi (bug lor).
    # Patch-ul face aceeasi matematica in 48 MB. Aplicat o singura data.
    try:
        import proiect as P
        P.patch_rea_video(REASRC)
    except Exception as e:
        log(f"  [!] patch-ul de memorie nu s-a putut aplica: {e}")
    env = os.environ.copy()
    env["PATH"] = str(FFBIN) + os.pathsep + env.get("PATH", "")
    # arat ca merge: scanez folderul de iesire si raportez la fiecare 20s
    import threading
    import time as _t

    oprit = threading.Event()

    # ---------- bara de procent ----------
    # Etapele reale din rea_video/pipeline.py, cu ponderea pe durata masurata:
    #   video/ffprobe   2%   detect_shots (imaginea)  30%
    #   analyze_audio   35%  stems (voce/muzica)     10%
    #   shots/sample    20%  impachetare/raport       3%
    ETAPE = [
        (r"INFO video ", "citesc video-ul", 2),
        (r"detected \d+ shots", "taie planurile", 30),
        (r"separating stems", "analizez sunetul", 35),
        (r"separating speakers|transcribing speech", "separ separat vocea", 10),
        (r"packaging layer", "impachetez rezultatul", 20),
        (r"rendered shots|special moments|done in", "fac raportul", 3),
    ]

    st = {"pct": 0, "etapa": "pornesc", "t0": _t.time()}

    def _bara(pct, etapa, extra=""):
        pct = max(0, min(100, int(pct)))
        umplut = int(pct * 30 // 100)
        bara = "#" * umplut + "." * (30 - umplut)
        scurs = _t.time() - st["t0"]
        # estimare: daca stim cat la suta am facut, extrapolam
        ramas = ""
        if pct >= 5:
            total_est = scurs * 100.0 / pct
            r = max(0.0, total_est - scurs)
            ramas = "  ~%d min ramase" % max(1, int(r // 60)) if r > 90 else "  aproape gata"
        log("    [%s] %3d%%  %s%s %s" % (bara, pct, etapa, ramas, extra))

    oprit = threading.Event()
    # procentul "de umplut" intre doua etape: avanseaza lin, ca sa vezi ca merge
    tic = {"pornit": _t.time(), "de_la": 0, "pana_la": 0}
    _gpu_activ = globals().get("_GPU_OK", False)

    def _ticuri():
        while not oprit.wait(15):
            if tic["pana_la"] > tic["de_la"]:
                # estimez cat din etapa a trecut dupa timp (aproximativ)
                scurs = _t.time() - tic["pornit"]
                # presupun ca etapa ia cam 8 min; dupa 8 min ajunge la 85% din etapa
                fractie = min(0.9, scurs / 480.0)
                pct = tic["de_la"] + (tic["pana_la"] - tic["de_la"]) * fractie
                if pct > st["pct"]:
                    st["pct"] = pct
                    _bara(int(pct), st["etapa"])

    erori = []  # ultimele linii, ca sa pot spune MOTIVUL, nu "a esuat"

    def urmaresc(flux):
        """Citeste iesirea rea-video linie cu linie si actualizeaza procentul."""
        for linie in iter(flux.readline, ""):
            linie = linie.rstrip()
            if not linie:
                continue
            # scriu linia originala doar daca e IMPORTANTA (nu zgomot numpy)
            if "RuntimeWarning" not in linie and "c /=" not in linie and "numpy" not in linie:
                if linie.startswith(("INFO", "WARNING", "ERROR")) or "Traceback" in linie:
                    print("      " + linie[:150], flush=True)
            # tin minte tot ce arata o eroare (nu doar "INFO")
            if linie.strip():
                erori.append(linie.rstrip())
                if len(erori) > 60:
                    del erori[0]
            for model, eticheta, pondere in ETAPE:
                if re.search(model, linie):
                    # procentul = suma ponderilor etapelor terminate
                    idx = [m for m, _, _ in ETAPE].index(model)
                    dinainte = sum(w for _, _, w in ETAPE[:idx])
                    urmator = dinainte + (ETAPE[idx][2] if idx < len(ETAPE) else 0)
                    st["pct"] = max(st["pct"], dinainte)
                    st["etapa"] = eticheta
                    tic.update({"pornit": _t.time(), "de_la": dinainte, "pana_la": urmator})
                    _bara(st["pct"], eticheta)
                    break
        oprit.set()

    log("    (fisierele apar abia la final - nu e blocat)")
    _bara(0, "pornesc descompunerea")
    cod = 1
    try:
        proc = subprocess.Popen(
            [str(PYEXE), "-m", "rea_video", "decompose", str(video),
             "-o", str(out), "--lang", "en", "--no-vlm"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, encoding="utf-8", errors="replace",
            creationflags=cflags_prioritate())
        fir = threading.Thread(target=urmaresc, args=(proc.stdout,), daemon=True)
        fir.start()
        threading.Thread(target=_ticuri, daemon=True).start()
        cod = proc.wait()
        fir.join(timeout=5)
    finally:
        oprit.set()

    if _gpu_activ:
        log("    (separea sunetului a rulat pe PLACA VIDEO; restul pe procesor, ca acolo nu ajuta GPU-ul)")
    else:
        log("    (totul pe procesor - placa video nu a fost folosita)")
    _bara(100, "gata descompunerea")
    if cod != 0:
        log()
        log("  [!] descompunerea a esuat (codul de iesire %s). Motivul:" % cod)
        arat = [l for l in erori if any(k in l for k in
                ("Error", "error", "Traceback", "Exception", "FAILED", "Killed", "MemoryError",
                 "_ is not defined", "File \""))]
        for linie in (arat[-14:] if arat else erori[-8:]):
            log("      " + linie[:160])
        if any("is not defined" in l for l in erori):
            log("      -> e un PATCH STRICAT. Repornesc aplicatia: o reface singura.")
            log("         (daca tot pica, sterge C:\\Users\\Admin\\AppData\\Local\\AnalizaVideo\\rea-video)")
        elif any("MemoryError" in l or "OutOfMemory" in l or "alloc" in l for l in erori):
            log("      -> memorie. Inchide Chrome-ul si ruleaza din nou.")
        log("      trimite-mi randul de mai sus daca pica iar.")
        log()
        return False
    return True


def stems_rezerva(video, out):
    """Plan B cand decompose esueaza: scot stem-urile audio direct, ca sa ai sunetele separate.

    rea-video stems nu are nevoie de analiza shot cu shot, doar de modelul de 67 MB.
    """
    log()
    log("  plan B: separ sunetul (voce / muzica / efecte) direct...")
    env = os.environ.copy()
    env["PATH"] = str(FFBIN) + os.pathsep + env.get("PATH", "")
    try:
        r = subprocess.run([str(PYEXE), "-m", "rea_video", "stems", str(video), "-o", str(out)],
                           env=env, timeout=3600, creationflags=cflags_prioritate())
        if r.returncode == 0:
            st = out / "stems"
            n = len(list(st.glob("*.wav"))) if st.exists() else 0
            if n:
                log(f"    gata: {n} fisiere audio separate")
                return True
        log("    nu a mers nici planul B")
    except (OSError, subprocess.SubprocessError) as e:
        log(f"    [!] stems: {e}")
    return False


def taieturi(video):
    log()
    _o = time.time()
    log("  scot taieturi (EDL / XML / markere)...")
    script = AICI / "inspecteaza.py"
    if not script.exists():
        log("  [!] lipseste inspecteaza.py")
        return
    env = os.environ.copy()
    env["PATH"] = str(FFBIN) + os.pathsep + env.get("PATH", "")
    subprocess.run([str(PYEXE), str(script), str(video)], env=env,
                   creationflags=cflags_prioritate())
    log("    gata in %d s" % int(time.time() - _o))


def deschide(p):
    if not p or not Path(p).exists():
        return
    log(f"  deschid: {p}")
    try:
        if WIN:
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(p)])
        else:
            subprocess.run(["xdg-open", str(p)])
    except Exception:
        pass


# ------------------------------------------------------------------ MAIN
def main():
    global PAUZA
    if "--no-pause" in sys.argv:
        PAUZA = False
        sys.argv.remove("--no-pause")
    log()
    log("  ==========================================================")
    log("   ANALIZA VIDEO - o singura aplicatie")
    log("  ==========================================================")
    log()
    nuclee = setari_viteza()
    log(f"  Tot ce descarc sta in: {CACHE}")
    log(f"  Procesoare: {nuclee} logice | modelele folosesc pana la 8 | prioritate: mare")

    # patch-ul de memorie se aplica devreme, pe orice instalare deja existenta
    try:
        import proiect as P
        if REASRC.exists():
            P.patch_rea_video(REASRC, tacut=True)
            # PATCH-URILE CHIAR MERG? Un patch care nu compileaza omoara toata analiza
            # (asa a crapat cu "name _LazyFrames is not defined"). Verific ACUM, nu dupa 40 min.
            rele = P.verifica_patchuri(REASRC, pyexe=PYEXE)
            if rele:
                log(f"  [!] patch rupt in: {', '.join(rele)} - refac din copia .bak")
                P.reface_din_bak(REASRC, rele)
                P.patch_rea_video(REASRC, tacut=True)
                rele = P.verifica_patchuri(REASRC, pyexe=PYEXE)
                if rele:
                    log(f"  [!!] tot rupt: {', '.join(rele)} - rulez FARA patch (mai bine lent decat deloc)")
                    P.dezactiveaza_patchuri(REASRC, rele)
    except Exception as e:
        log(f"  [!] verificarea patch-urilor: {e}")
    liber, tot = ram_mb()
    if liber and tot:
        log(f"  RAM liber: {liber} MB din {tot} MB")
        if liber < 1200:
            log("  [i] RAM liber putin - tot merg, patch-ul de memorie strange cadrele la ~200 MB.")

    if not WIN:
        log("  (rulez pe Linux - pentru Windows e RULEAZA.bat)")

    ok = asigura_python()
    if not ok:
        log()
        log("  [!] NU pot continua fara Python.")
        log("      Trimite-mi ce scrie mai sus.")
        asteapta()
        return 1

    ok = asigura_ffmpeg()
    if not ok:
        log("  [!] ffmpeg lipseste - analiza nu poate rula.")
        asteapta()
        return 1

    asigura_ytdlp()
    asigura_rea()

    log()
    sursa = sys.argv[1] if len(sys.argv) > 1 else ""
    if not sursa:
        log("  Lipeste linkul YouTube (sau calea unui fisier .mp4)")
        log("  si apasa Enter.")
        log()
        sursa = input("  Link/fisier: ").strip().strip('"')
    if not sursa:
        return 1

    video = ia_videoul(sursa)
    if not video:
        asteapta()
        return 1

    out = AICI / ("analiza-" + nume_sigur(video.stem))
    out.mkdir(parents=True, exist_ok=True)
    _dur = 0.0
    try:
        _r = subprocess.run([str(FFBIN / ("ffprobe.exe" if WIN else "ffprobe")),
                             "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=nw=1:nk=1", str(video)],
                            capture_output=True, text=True, timeout=60)
        _dur = float(_r.stdout.strip())
    except Exception:
        pass
    # GPU: instalat o singura data, inainte de partea lunga
    try:
        asigura_gpu()
    except Exception as e:
        log(f"  [!] GPU: {e}")

    # AV1 nu are decodor hardware pe GTX 1660 (doar RTX 30+). Il fac H.264 o data.
    try:
        video = pregateste_pentru_gpu(video)
    except Exception as e:
        log(f"  [!] pregatirea pentru GPU: {e}")

    ok_descompunere = descompune(video, out, durata_video=_dur)
    if not ok_descompunere:
        stems_rezerva(video, out)
    taieturi(video)

    # ---- PROIECT MULTI-TRACK (ca in Premiere: gameplay / overlay / text / 4 track-uri audio)
    proiect_xml = None
    try:
        import proiect as P
        titlu("PROIECT multi-track (ca in Premiere)")
        meta = {}
        try:
            r = subprocess.run([str(FFBIN / ("ffprobe.exe" if WIN else "ffprobe")),
                                "-v", "error", "-select_streams", "v:0",
                                "-show_entries", "stream=width,height,r_frame_rate",
                                "-of", "json", str(video)],
                               capture_output=True, text=True, timeout=60,
                               env={**os.environ, "PATH": str(FFBIN) + os.pathsep + os.environ.get("PATH", "")})
            meta = json.loads(r.stdout)["streams"][0]
        except Exception:
            pass
        durata = 0.0
        try:
            r = subprocess.run([str(FFBIN / ("ffprobe.exe" if WIN else "ffprobe")),
                                "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=nw=1:nk=1", str(video)],
                               capture_output=True, text=True, timeout=60)
            durata = float(r.stdout.strip())
        except Exception:
            pass
        proiect_xml, proiect_md, stats = P.construieste(
            out, video,
            iesire=out / "PROIECT.xml",
            ffprobe=str(FFBIN / ("ffprobe.exe" if WIN else "ffprobe")),
            latime=int(meta.get("width") or 1920),
            inaltime=int(meta.get("height") or 1080),
            fps=meta.get("r_frame_rate") or "25/1",
            durata=durata,
            ffmpeg=str(FFBIN / ("ffmpeg.exe" if WIN else "ffmpeg")))
        log(f"  track-uri: {stats['trackuri_video']} video + {stats['trackuri_audio']} audio")
    except Exception as e:
        log(f"  [!] proiectul multi-track a esuat: {e}")

    titlu("GATA" if ok_descompunere else "GATA (partial - vezi mai jos)")
    raport = out / "report.html"
    xml = video.with_suffix(".xml")
    if ok_descompunere:
        log(f"  RAPORT (shot cu shot) : {raport}")
    else:
        log("  [!] analiza shot cu shot NU s-a facut (memorie / eroare).")
        log("      Ai totusi: taieturi exacte, sunete separate, proiect FilmCraft.")
    if proiect_xml and proiect_xml.exists():
        log(f"  PROIECT FilmCraft         : {proiect_xml}")
        log("     (4 track-uri video + 4 audio; V2-V4 sunt stinse ca sa se vada gameplay-ul)")
        if stats.get("xml_premiere"):
            log(f"  PROIECT Premiere          : {stats['xml_premiere']}")
            log("     (acelasi proiect, cu V2-V4 APRINSE - pentru Premiere)")
    log(f"  TAIETURI simple           : {xml}")
    log(f"  EDL (Premiere/Resolve)    : {video.with_suffix('.edl')}")
    log(f"  RAPORT taieturi           : {Path(str(video.with_suffix('')) + '-raport.html')}")
    log()
    deschide(raport if raport.exists() else xml)
    log()
    if sys.stdin and sys.stdin.isatty():
        log("  Vrei sa-l vezi in FilmCraft? (proiect multi-track gata)")
        try:
            rasp = input("  [D]a / [n]u : ").strip().lower()
        except Exception:
            rasp = "n"
        if rasp in ("", "d", "da", "y", "yes"):
            deschide_filmcraft_cu_xml(proiect_xml or xml)
    log()
    asteapta()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n  oprit.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n  [!] EROARE: {e}")
        asteapta()
