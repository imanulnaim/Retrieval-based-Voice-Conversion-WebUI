#!/usr/bin/env python3
"""
Kinetic cinematic caption renderer (vertical 9:16 "podcast clip" style).

Style (copied from the reference clip):
  * Word-by-word kinetic captions: small lead-in words sit above-left of a
    huge, heavy keyword; small trailing words sit below-right of it.
  * Keyword pops in: blur -> sharp, slight scale-down, fast fade.
  * Jump-cut punch-in zoom alternating per caption line.
  * Cinematic grade: contrast, warm highlights / teal shadows, vignette, grain.
  * Optional B-roll inserts and a kinetic name card.

Usage:
  python3 kinetic.py script.txt input.mp4 output.mp4 [--no-grade] [--no-zoom]

Script format (one item per line, times in seconds, '#' = comment):
  start end lead | KEY | tail          caption
  BROLL start end path/to/clip.mp4     B-roll covering the main shot (audio kept)
  CARD  start end lead | KEY | tail    full-screen dimmed name card
"""
import os
import subprocess
import sys

from PIL import ImageFont

W, H = 1080, 1920
FONT_KEY = "Inter Display Black"
FONT_SMALL = "Inter Display Bold"
FONT_KEY_FILE = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
KEY_SIZE = 190          # ASS font size of the keyword
SMALL_SIZE = 54         # ASS font size of lead / tail
CAP_Y = int(H * 0.66)   # vertical centre of the keyword
MAX_KEY_W = W - 140     # keyword is shrunk to fit this width
TRACK_KEY = -6          # tight negative tracking like the reference
TRACK_SMALL = -1.5
LIBASS_EM = 1.21        # libass size = ascender+descender (Inter ~1.21 em)
FOCUS = [0.5, 0.5]      # punch-in anchor (0..1), set with "FOCUS x y" in the script
PUNCH = 0.12            # punch-in zoom amount


def ts(t):
    t = max(t, 0)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def key_width(text, size):
    font = ImageFont.truetype(FONT_KEY_FILE, max(1, int(size / LIBASS_EM)))
    w = font.getlength(text)
    return w + TRACK_KEY * (len(text) - 1)


def parse(path):
    caps, brolls, cards = [], [], []
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#", 1)[0].strip() if not raw.lstrip().startswith("#") else ""
        if not line:
            continue
        head = line.split()[0].upper()
        if head == "FOCUS":
            _, fx, fy = line.split()
            FOCUS[:] = [float(fx), float(fy)]
            continue
        if head == "BROLL":
            _, a, b, p = line.split(None, 3)
            brolls.append((float(a), float(b), p.strip()))
            continue
        target = caps
        if head == "CARD":
            target = cards
            line = line.split(None, 1)[1]
        a, b, rest = line.split(None, 2) if len(line.split(None, 2)) == 3 else (*line.split(None, 1), "")
        parts = [p.strip() for p in (rest + "||").split("|")[:3]]
        target.append((float(a), float(b), parts[0], parts[1], parts[2]))
    return caps, brolls, cards


def caption_events(a, b, lead, key, tail, card=False):
    ev = []
    size = KEY_SIZE * (1.25 if card else 1.0)
    kw = key_width(key, size)
    if kw > MAX_KEY_W:
        size *= MAX_KEY_W / kw
        kw = MAX_KEY_W
    cx, cy = W // 2, (H // 2 if card else CAP_Y)
    left, right = cx - kw / 2, cx + kw / 2
    top = cy - size * 0.40
    bottom = cy + size * 0.40
    dur = b - a
    t_key = a + (min(0.35, dur * 0.3) if lead else 0)
    t_tail = t_key + min(0.45, (b - t_key) * 0.4)

    # lead words: word-by-word, sitting on the keyword's top-left edge
    if lead:
        words = lead.split()
        step = max(0.06, (t_key - a) / max(1, len(words)))
        for i, _ in enumerate(words):
            st = a + i * step
            shown = " ".join(words[: i + 1])
            end = a + (i + 1) * step if i < len(words) - 1 else b
            ev.append((st, end, "Small",
                       f"{{\\an1\\pos({left + 4:.0f},{top:.0f})\\fsp{TRACK_SMALL}}}{shown}"))
    # keyword: blur -> sharp pop
    ev.append((t_key, b, "Key",
               f"{{\\an5\\pos({cx},{cy})\\fs{size:.0f}\\fsp{TRACK_KEY}"
               f"\\fad(70,90)\\blur14\\fscx114\\fscy114\\alpha&H40&"
               f"\\t(0,240,0.6,\\blur0\\fscx100\\fscy100\\alpha&H00&)}}{key}"))
    # tail: under the keyword, right aligned
    if tail:
        ev.append((t_tail, b, "Small",
                   f"{{\\an9\\pos({right - 4:.0f},{bottom:.0f})\\fsp{TRACK_SMALL}"
                   f"\\fad(120,90)\\move({right - 4:.0f},{bottom + 14:.0f},{right - 4:.0f},{bottom:.0f},0,200)}}{tail}"))
    return ev


def write_ass(caps, cards, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Key,{FONT_KEY},{KEY_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,0,6,5,0,0,0,1
Style: Small,{FONT_SMALL},{SMALL_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,0,3,1,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    for c in caps:
        for st, en, style, txt in caption_events(*c):
            lines.append(f"Dialogue: 1,{ts(st)},{ts(en)},{style},,0,0,0,,{txt}\n")
    for c in cards:
        for st, en, style, txt in caption_events(*c, card=True):
            lines.append(f"Dialogue: 2,{ts(st)},{ts(en)},{style},,0,0,0,,{txt}\n")
    open(path, "w", encoding="utf-8").writelines(lines)


def zoom_expr(caps):
    # jump-cut punch-in: every other caption line is pushed in (PUNCH) toward FOCUS
    terms = [f"between(t,{a:.3f},{b:.3f})" for i, (a, b, *_) in enumerate(caps) if i % 2 == 1]
    if not terms:
        return "1"
    return f"(1+{PUNCH}*gt({'+'.join(terms)},0))"


def build(script, src, out, grade=True, zoom=True):
    caps, brolls, cards = parse(script)
    ass = os.path.splitext(out)[0] + ".ass"
    write_ass(caps, cards, ass)

    inputs = ["-i", src]
    for _, _, p in brolls:
        inputs += ["-i", p]

    z = zoom_expr(caps) if zoom else "1"
    fc = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,crop={W}:{H}:x='(iw-{W})*{FOCUS[0]}':y='(ih-{H})*{FOCUS[1]}',setsar=1[v0]"]
    cur = "v0"
    for i, (a, b, _) in enumerate(brolls, start=1):
        fc.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
                  f"trim=duration={b - a:.3f},setpts=PTS-STARTPTS+{a:.3f}/TB[b{i}]")
        fc.append(f"[{cur}][b{i}]overlay=enable='between(t,{a:.3f},{b:.3f})':eof_action=pass[o{i}]")
        cur = f"o{i}"
    post = []
    if grade:
        post += ["eq=contrast=1.08:saturation=1.08:gamma=0.97",
                 "colorbalance=rs=-0.04:bs=0.05:rh=0.05:bh=-0.04",
                 "vignette=PI/4.6",
                 "noise=alls=6:allf=t"]
    for a, b, *_ in cards:
        post.append(f"drawbox=t=fill:c=black@0.62:enable='between(t,{a:.3f},{b:.3f})'")
    post.append(f"ass='{ass}'")
    fc.append(f"[{cur}]{','.join(post)},format=yuv420p[vout]")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
           "-map", "[vout]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium",
           "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print("wrote", out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        sys.exit(__doc__)
    build(*args, grade="--no-grade" not in sys.argv, zoom="--no-zoom" not in sys.argv)
