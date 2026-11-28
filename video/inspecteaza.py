#!/usr/bin/env python3
"""
INSPECTEAZA UN VIDEO - ce e in el si cum a fost facut
=====================================================
Nu are nevoie de nimic instalat in afara de ffmpeg + ffprobe pe PATH.

Ce scoate:
  1. Metadate complete (codec, bitrate, fps, rezolutie, encoder)
  2. TAIETURI: unde se schimba planul, cu timp exact
  3. RITM: cat de repede taie (taieturi/minut)
  4. LUMINA + CULOARE per plan
  5. AUDIO: volum, pauze, peak-uri
  6. RAPORT HTML cu timeline colorat

Utilizare:
  python inspecteaza.py video.mp4
  python inspecteaza.py video.mp4 --prag 0.2      (mai sensibil, prinde taieturi fine)
  python inspecteaza.py video.mp4 --html           (doar raportul HTML)
"""

import argparse, json, os, re, subprocess, sys, html
from datetime import timedelta

def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        if cmd and cmd[0] == 'ffprobe':
            return 127, '', 'ffprobe lipseste'

        print(f"\n  NU gasesc '{cmd[0]}'.\n  Instaleaza ffmpeg:  winget install ffmpeg\n")
        sys.exit(1)

def tc(sec):
    """0:02:05.44 - fara zerouri inutile la coada."""
    t = round(float(sec), 2)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    out = f"{int(h)}:{int(m):02d}:{s:05.2f}".rstrip('0').rstrip('.')
    return out if '.' in out or len(out.split(':')[-1]) == 2 else out + '.0' 

# ---------------------------------------------------------------- 1. METADATE
def _probe_ffmpeg(path):
    """Plan B: ffprobe lipseste (ex: doar ffmpeg din imageio-ffmpeg) -> citesc `ffmpeg -i`."""
    rc, out, err = run(['ffmpeg', '-hide_banner', '-i', path])
    txt = err + out
    if 'Invalid data' in txt or 'No such file' in txt:
        return None
    d = {'format': {}, 'streams': []}
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', txt)
    if m:
        h, mm, ss = m.groups()
        d['format']['duration'] = str(int(h) * 3600 + int(mm) * 60 + float(ss))
    m = re.search(r'bitrate: (\d+) kb/s', txt)
    if m:
        d['format']['bit_rate'] = str(int(m.group(1)) * 1000)
    m = re.search(r'Input #0, ([^,]+)', txt)
    if m:
        d['format']['format_name'] = m.group(1)
    m = re.search(r'Stream #0:\d+.*?: Video: (\w+).*?(\d{2,5})x(\d{2,5})', txt)
    if m:
        d['streams'].append({'codec_type': 'video', 'codec_name': m.group(1),
                             'width': int(m.group(2)), 'height': int(m.group(3))})
    m = re.search(r'(\d+(?:\.\d+)?) fps', txt)
    if m and d['streams']:
        d['streams'][0]['r_frame_rate'] = m.group(1)
    m = re.search(r'Stream #0:\d+.*?: Audio: (\w+).*?(\d{4,6}) Hz', txt)
    if m:
        d['streams'].append({'codec_type': 'audio', 'codec_name': m.group(1),
                             'sample_rate': m.group(2)})
    return d


def probe(path):
    rc, out, err = run(['ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', '-show_streams', path])
    if rc != 0 or not out.strip():
        d = _probe_ffmpeg(path)
        if not d:
            print("  Nu pot citi fisierul. E video valid?")
            print("  ffprobe spune: " + (err.strip().splitlines()[-1] if err.strip() else 'nimic'))
            sys.exit(1)
    else:
        d = json.loads(out)
    fmt = d.get('format', {})
    v = next((s for s in d.get('streams', []) if s.get('codec_type') == 'video'), None)
    a = next((s for s in d.get('streams', []) if s.get('codec_type') == 'audio'), None)

    info = {
        'fisier':      os.path.basename(path),
        'dimensiune':  int(fmt.get('size', 0)),
        'durata':      float(fmt.get('duration', 0) or 0),
        'bitrate':     int(fmt.get('bit_rate', 0) or 0),
        'container':   fmt.get('format_name', '?'),
        'tags':        fmt.get('tags', {}),
    }
    if v:
        info.update({
            'codec':     v.get('codec_name', '?'),
            'profil':    v.get('profile', '?'),
            'latime':    v.get('width'),
            'inaltime':  v.get('height'),
            'fps':       v.get('r_frame_rate', '?'),
            'pix_fmt':   v.get('pix_fmt', '?'),
            'v_bitrate': int(v.get('bit_rate', 0) or 0),
            'v_tags':    v.get('tags', {}),
        })
    if a:
        info.update({
            'a_codec':   a.get('codec_name', '?'),
            'a_rate':    a.get('sample_rate', '?'),
            'a_canale':  a.get('channels', '?'),
            'a_bitrate': int(a.get('bit_rate', 0) or 0),
        })
    return info

# ---------------------------------------------------------------- 2. TAIETURI
def taieuri(path, prag=0.3):
    """ffmpeg select=gt(scene,PRAG) - scor de schimbare intre cadre."""
    rc, out, err = run(['ffmpeg', '-hide_banner', '-i', path,
                        '-filter:v', f"select='gt(scene,{prag})',metadata=print",
                        '-f', 'null', '-'])
    times, scores = [], []
    for line in err.splitlines():
        m = re.search(r'pts_time:([0-9.]+)', line)
        if m:
            times.append(float(m.group(1)))
        m2 = re.search(r'lavfi\.scene_score=([0-9.]+)', line)
        if m2:
            scores.append(float(m2.group(1)))
    n = min(len(times), len(scores))
    return [{'t': times[i], 'scor': scores[i]} for i in range(n)]

# ---------------------------------------------------------------- 3. LUMINA/CULOARE
def culoare_plan(path, start, dur, w=64):
    """O medie de culoare per plan, prin scalare la 1 pixel."""
    if dur <= 0.05:
        return None
    rc, out, err = run(['ffmpeg', '-hide_banner', '-loglevel', 'info',
                        '-ss', f'{start:.3f}', '-t', f'{dur:.3f}', '-i', path,
                        '-vf', 'scale=1:1', '-frames:v', '1',
                        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    try:
        p = subprocess.run(['ffmpeg', '-v', 'quiet', '-ss', f'{start:.3f}', '-t', f'{dur:.3f}',
                            '-i', path, '-vf', 'scale=1:1', '-frames:v', '1',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           capture_output=True)
        b = p.stdout
        if len(b) >= 3:
            return '#%02x%02x%02x' % (b[0], b[1], b[2])
    except Exception:
        pass
    return None

def luminozitate(path, start, dur):
    rc, out, err = run(['ffmpeg', '-hide_banner', '-ss', f'{start:.3f}', '-t', f'{dur:.3f}',
                        '-i', path, '-vf', 'signalstats,metadata=print:key=lavfi.signalstats.YAVG',
                        '-f', 'null', '-'])
    vals = [float(m) for m in re.findall(r'YAVG=([0-9.]+)', err)]
    return round(sum(vals)/len(vals), 1) if vals else None

# ---------------------------------------------------------------- 4. AUDIO
def audio_stat(path):
    rc, out, err = run(['ffmpeg', '-hide_banner', '-i', path,
                        '-af', 'volumedetect,silencedetect=noise=-40dB:d=1.0',
                        '-f', 'null', '-'])
    res = {}
    m = re.search(r'mean_volume:\s*(-?[0-9.]+) dB', err)
    if m: res['volum_mediu'] = float(m.group(1))
    m = re.search(r'max_volume:\s*(-?[0-9.]+) dB', err)
    if m: res['volum_max'] = float(m.group(1))
    res['pauze'] = [round(float(x), 2) for x in re.findall(r'silence_start:\s*([0-9.]+)', err)]
    res['pauze_total'] = len(res['pauze'])
    return res

# ---------------------------------------------------------------- 5. EXPORT
def scrie_edl(tais, dur, path):
    """CMX3600 EDL: o intrare per plan, pe axa V1. Importi in Premiere/Resolve/FilmCraft."""
    lines = ["TITLE   TAIETURI", "FCM: NON-DROP FRAME", ""]
    marks = [0.0] + [t['t'] for t in tais] + [dur]
    n = 0
    for i in range(len(marks) - 1):
        a, b = marks[i], marks[i + 1]
        if b - a < 0.04:
            continue
        n += 1
        def tcms(x):
            f = int(round(x * 25))
            return "00:%02d:%02d:%02d" % (f // 1500, (f // 25) % 60, f % 25)
        lines.append("%03d  AX       V     C        %s %s %s %s" %
                     (n, tcms(a), tcms(b), tcms(a), tcms(b)))
        lines.append("* FROM CLIP NAME: plan_%03d" % n)
        lines.append("")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    return n


def _fps_din(text):
    """'60/1' -> 60.0 ; '30000/1001' -> 29.97 ; '?' -> 25.0"""
    try:
        if "/" in str(text):
            x, y = str(text).split("/")[:2]
            v = float(x) / float(y) if float(y) else 25.0
        else:
            v = float(text)
        return v if 1 <= v <= 240 else 25.0
    except (TypeError, ValueError, ZeroDivisionError):
        return 25.0


def scrie_fcpxml(tais, dur, path, nume="secventa",
                 video=None, fps=None, latime=None, inaltime=None):
    """FCP7 XML (xmeml v4) COMPLET - FilmCraft/Premiere/Resolve leaga media automat.

    video = calea absoluta a .mp4 (fara ea, FilmCraft arata timeline gol)
    fps   = frame rate REAL (60, 29.97...) - nu hardcodat
    """
    import pathlib
    import urllib.parse

    f = _fps_din(fps) if fps is not None else 25.0
    tb = int(round(f))
    ntsc = "TRUE" if abs(f - round(f)) > 0.001 else "FALSE"
    W = int(latime or 1920)
    H = int(inaltime or 1080)
    total = int(round(dur * f))

    file_block = ""
    if video:
        vp = pathlib.Path(video).resolve()
        cale = str(vp).replace("\\", "/")
        # Windows: "C:/Users/..." -> file://localhost/C:/Users/...
        # Linux/Mac: "/home/x/..." -> file://localhost/home/x/...
        if len(cale) > 1 and cale[1] == ":":      # litera de disc
            uri = "file://localhost/" + urllib.parse.quote(cale)
        else:
            uri = "file://localhost" + urllib.parse.quote(cale)
        file_block = (
            f'<file id="file-1">'
            f'<name>{html.escape(vp.name)}</name>'
            f'<pathurl>{html.escape(uri)}</pathurl>'
            f'<duration>{total}</duration>'
            f'<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>'
            f'<media><video><samplecharacteristics>'
            f'<width>{W}</width><height>{H}</height>'
            f'<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>'
            f'</samplecharacteristics></video>'
            f'<audio><samplecharacteristics><depth>16</depth>'
            f'<samplerate>48000</samplerate></samplecharacteristics>'
            f'<channelcount>2</channelcount></audio></media>'
            f'</file>'
        )

    marks = [0.0] + [t['t'] for t in tais] + [dur]
    items = []
    n = 0
    for i in range(len(marks) - 1):
        a, b = marks[i], marks[i + 1]
        if b - a < 0.04:
            continue
        n += 1
        ins = int(round(a * f))
        ous = int(round(b * f))
        # primul clipitem duce definitia completa a fisierului, restul o refera
        ref = file_block if (n == 1 and file_block) else ('<file id="file-1"/>' if file_block else "")
        items.append(
            f'<clipitem id="clipitem-{n}"><name>plan_{n:03d}</name>'
            f'<duration>{ous - ins}</duration>'
            f'<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>'
            f'<start>{ins}</start><end>{ous}</end><in>{ins}</in><out>{ous}</out>'
            f'{ref}</clipitem>'
        )

    xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE xmeml>\n'
        f'<xmeml version="4"><sequence id="seq-1"><name>{html.escape(nume)}</name>'
        f'<duration>{total}</duration>'
        f'<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>'
        '<media><video>'
        '<format><samplecharacteristics>'
        f'<width>{W}</width><height>{H}</height>'
        f'<rate><timebase>{tb}</timebase><ntsc>{ntsc}</ntsc></rate>'
        '</samplecharacteristics></format>'
        f'<track>{"".join(items)}</track>'
        '</video>'
        + (('<audio><track>' + ''.join(
            it.replace('</clipitem>', '<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack></clipitem>')
          for it in items) + '</track></audio>') if file_block else '')
        + '</media></sequence></xmeml>\n'
    )
    open(path, "w", encoding="utf-8").write(xml)
    return n


def scrie_markere_csv(tais, path):
    """CSV de markere: timp, scor. FilmCraft are Markers ▸ Import? Premiere NU importa CSV de markere."""
    rows = ["time_seconds,score"]
    for t in tais:
        rows.append("%.3f,%.4f" % (t['t'], t['scor']))
    open(path, "w", encoding="utf-8").write("\n".join(rows))
    return len(tais)


def scrie_capitole(tais, dur, path):
    """Capitole YouTube: 0:00 Nume - lipesti in descriere."""
    rows = []
    marks = [0.0] + [t['t'] for t in tais] + [dur]
    for i in range(len(marks) - 1):
        a = marks[i]
        rows.append("%d:%02d Plan %d" % (int(a // 60), int(a % 60), i + 1))
    open(path, "w", encoding="utf-8").write("\n".join(rows))
    return len(rows)


# ---------------------------------------------------------------- RAPORT
def raport_html(info, tais, audio, out_path):
    dur = info['durata'] or 1
    def pct(t): return max(0.0, min(100.0, t / dur * 100))

    segmente = []
    for i, t in enumerate(tais):
        start = t['t']
        end = tais[i+1]['t'] if i+1 < len(tais) else dur
        segmente.append((start, end - start, t['scor']))

    culori = []
    for s, d, sc in segmente:
        c = culoare_plan(info['_path'], s, min(d, 3.0))
        y = luminozitate(info['_path'], s, min(d, 3.0))
        culori.append((c, y))

    lungimi = [d for s, d, sc in segmente]
    medie = sum(lungimi)/len(lungimi) if lungimi else 0

    rows = []
    for i, (s, d, sc) in enumerate(segmente):
        c, y = culori[i]
        rows.append(
            f"<tr><td>{i+1}</td><td>{tc(s)}</td><td>{d:.2f}s</td>"
            f"<td>{sc:.3f}</td><td style='background:{c or '#222'}'>{c or '-'}</td>"
            f"<td>{y if y is not None else '-'}</td></tr>"
        )

    bare = "".join(
        f"<div class='seg' style='left:{pct(s):.3f}%;width:{max(0.15,pct(d)):.3f}%;"
        f"background:{culori[i][0] or '#444'}' title='{tc(s)} - {d:.2f}s'></div>"
        for i, (s, d, sc) in enumerate(segmente)
    )

    header = f"""<!doctype html><html lang="ro"><meta charset="utf-8">
<title>Raport: {html.escape(info['fisier'])}</title>
<style>
 body{{background:#111;color:#ddd;font:14px/1.5 ui-monospace,Consolas,monospace;margin:24px}}
 h1{{font-size:20px;color:#fff}} h2{{font-size:15px;color:#8cf;margin-top:28px}}
 table{{border-collapse:collapse;width:100%;margin-top:8px}}
 th,td{{border-bottom:1px solid #2a2a2a;padding:5px 8px;text-align:left}}
 th{{color:#8cf;font-weight:600}}
 .tl{{position:relative;height:52px;background:#1a1a1a;border:1px solid #333;margin:14px 0}}
 .seg{{position:absolute;top:0;bottom:0;border-right:1px solid #000}}
 .k{{color:#7d7}}
</style>
<h1>Raport video — {html.escape(info['fisier'])}</h1>
<table>
<tr><th>Durata</th><td>{tc(info['durata'])}</td></tr>
<tr><th>Rezolutie</th><td>{info.get('latime')}×{info.get('inaltime')}</td></tr>
<tr><th>FPS</th><td>{info.get('fps')}</td></tr>
<tr><th>Codec</th><td>{info.get('codec')} / {info.get('profil')}</td></tr>
<tr><th>Bitrate</th><td>{info.get('bitrate',0)/1000:.0f} kbps (video {info.get('v_bitrate',0)/1000:.0f})</td></tr>
<tr><th>Audio</th><td>{info.get('a_codec')} / {info.get('a_rate')} Hz / {info.get('a_canale')} canale</td></tr>
<tr><th>Container</th><td>{info.get('container')}</td></tr>
</table>
<h2>Timeline — fiecare plan cu culoarea lui</h2>
<div class="tl">{bare}</div>
<h2>Ritm</h2>
<table>
<tr><th>Taieturi detectate</th><td class="k">{len(segmente)}</td></tr>
<tr><th>Taieturi / minut</th><td class="k">{len(segmente)/(dur/60):.1f}</td></tr>
<tr><th>Lungime medie plan</th><td class="k">{medie:.2f} s</td></tr>
<tr><th>Plan cel mai scurt</th><td class="k">{min(lungimi) if lungimi else 0:.2f} s</td></tr>
<tr><th>Plan cel mai lung</th><td class="k">{max(lungimi) if lungimi else 0:.2f} s</td></tr>
</table>
<h2>Audio</h2>
<table>
<tr><th>Volum mediu</th><td>{audio.get('volum_mediu','-')} dB</td></tr>
<tr><th>Volum max</th><td>{audio.get('volum_max','-')} dB</td></tr>
<tr><th>Pauze peste 1 s</th><td>{audio.get('pauze_total','-')}</td></tr>
</table>
<h2>Planuri</h2>
<table><tr><th>#</th><th>inceput</th><th>durata</th><th>scor taietura</th><th>culoare</th><th>lumina</th></tr>
{''.join(rows)}
</table>
</html>"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(header)
    return out_path

# ---------------------------------------------------------------- MAIN
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--prag', type=float, default=0.45, help='0.45 normal (testat: ignora pan/zoom); 0.3 prinde mai mult dar si miscarea de camera')
    ap.add_argument('--fara-html', action='store_true')
    ap.add_argument('--edl', action='store_true', help='scrie EDL (import in Premiere/Resolve/FilmCraft)')
    ap.add_argument('--fcpxml', action='store_true', help='scrie FCP7 XML (import in FilmCraft/Premiere/Resolve)')
    ap.add_argument('--markere', action='store_true', help='scrie CSV cu markere')
    ap.add_argument('--capitole', action='store_true', help='scrie capitole YouTube')
    a = ap.parse_args()

    if not os.path.isfile(a.video):
        print(f"  Nu exista fisierul: {a.video}")
        sys.exit(1)

    print("\n" + "="*64)
    print("  ANALIZA VIDEO")
    print("="*64)

    info = probe(a.video)
    info['_path'] = a.video
    print(f"\n  fisier      : {info['fisier']}")
    print(f"  durata      : {tc(info['durata'])}")
    print(f"  rezolutie   : {info.get('latime')}x{info.get('inaltime')} @ {info.get('fps')} fps")
    print(f"  codec       : {info.get('codec')} ({info.get('profil')})  {info.get('v_bitrate',0)/1000:.0f} kbps")
    print(f"  audio       : {info.get('a_codec')} {info.get('a_rate')} Hz {info.get('a_canale')} canale")

    print(f"\n  detectez taieturi (prag {a.prag}) ...")
    tais = taieuri(a.video, a.prag)
    dur = info['durata'] or 1
    print(f"  taieturi    : {len(tais)}")
    print(f"  pe minut    : {len(tais)/(dur/60):.1f}")

    print(f"\n  analizez audio ...")
    au = audio_stat(a.video)
    print(f"  volum mediu : {au.get('volum_mediu','-')} dB")
    print(f"  volum max   : {au.get('volum_max','-')} dB")
    print(f"  pauze >1s   : {au.get('pauze_total','-')}")

    print(f"\n  primele 10 taieturi:")
    for i, t in enumerate(tais[:10]):
        print(f"    {i+1:3d}.  {tc(t['t']):>10}   scor {t['scor']:.3f}")

    if a.edl or a.fcpxml or a.markere or a.capitole or True:
        base = os.path.splitext(a.video)[0]
        n = scrie_edl(tais, dur, base + '.edl')
        scrie_fcpxml(tais, dur, base + '.xml', os.path.basename(base),
                    video=a.video, fps=info.get('fps'),
                    latime=info.get('latime'), inaltime=info.get('inaltime'))
        scrie_markere_csv(tais, base + '-markere.csv')
        scrie_capitole(tais, dur, base + '-capitole.txt')
        print(f"\n  EDL      : {base}.edl  ({n} planuri)")
        print(f"  FCP XML  : {base}.xml")
        print(f"  markere  : {base}-markere.csv")
        print(f"  capitole : {base}-capitole.txt")

    if not a.fara_html:
        out = os.path.splitext(a.video)[0] + '-raport.html'
        raport_html(info, tais, au, out)
        print(f"\n  RAPORT HTML : {out}")
        print(f"  deschide-l in browser.")

    print("\n" + "="*64 + "\n")

if __name__ == '__main__':
    main()
