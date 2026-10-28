import json, math, os, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = "/root/.claude/uploads/f9577f0b-6296-5153-9b28-f90fe1f3fec3/d6c5182e-Bukit_Katil_Kita_Tawan_2.mp3"
BG = os.path.join(HERE, "..", "images", "1.jpg")
W, H, FPS = 1080, 1920, 30
DUR = 79.6
NF = int(DUR * FPS)
F_ANTON = os.path.join(HERE, "fonts/anton-latin-400-normal.woff")
F_BEBAS = os.path.join(HERE, "fonts/bebas-neue-latin-400-normal.woff")
F_MONT = os.path.join(HERE, "fonts/montserrat-latin-900-normal.woff")
GOLD = (255, 196, 20)
WHITE = (255, 255, 255)
NAVY = (6, 26, 58)
CY = 975  # vertical centre of the lyric zone (between the two background text bands)

ana = json.load(open(os.path.join(HERE, "ana.json")))
BEATS = np.array(ana["beats"])
SPEC = np.load(os.path.join(HERE, "spec.npy"))  # (frames, bands) 0..1


def snap(t):
    return float(BEATS[np.argmin(np.abs(BEATS - t))])


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def e_out_cubic(p): return 1 - (1 - p) ** 3
def e_out_expo(p): return 1 if p >= 1 else 1 - 2 ** (-10 * p)
def e_out_back(p, s=2.2):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1
def e_out_bounce(p):
    n, d = 7.5625, 2.75
    if p < 1 / d: return n * p * p
    if p < 2 / d: p -= 1.5 / d; return n * p * p + .75
    if p < 2.5 / d: p -= 2.25 / d; return n * p * p + .9375
    p -= 2.625 / d; return n * p * p + .984375


# ---------------------------------------------------------------- cue sheet
# word markup: "*WORD" gold, "#WORD" navy on gold box, plain = white
# anim: slam | pop | rise | drop | side | track
B = snap
# "at" = start time of each word, taken from a Whisper word-timestamp pass over the song
CUES = [
    dict(t=0.05, end=0.95, lines=[["N17"]], size=560, anim="outline"),
    # INTRO chant
    dict(at=[1.0, 1.9], end=2.4, lines=[["BUKIT"], ["*KATIL!"]], size=300, anim="slam", flash=True),
    dict(at=[2.44, 2.96, 3.46], end=4.0, lines=[["HEI!"], ["HEI!"], ["*HEI!"]], size=230, anim="slam", shake=True),
    dict(at=[4.04], end=5.6, lines=[["#MUAFAKAT!"]], size=210, anim="pop", flash=True),
    dict(at=[5.7, 6.66, 7.2, 8.28], end=9.6, lines=[["AYUH", "SEMUA"], ["ANAK"], ["*MELAKA!"]], size=210, anim="rise"),
    # instrumental bridge
    dict(t=9.7, end=12.3, lines=[["BUKIT", "KATIL"]], size=110, anim="track", font="mont"),
    dict(t=12.4, end=14.95, lines=[["N17"]], size=560, anim="outline"),
    # VERSE
    dict(at=[15.1, 16.0], end=16.6, lines=[["LANGKAH"], ["*SEIRING,"]], size=250, anim="side"),
    dict(at=[16.68, 17.34], end=19.1, lines=[["TEKAD"], ["#DILAWAN,"]], size=250, anim="drop"),
    dict(at=[19.22, 19.86, 20.44, 21.12], end=22.7, lines=[["BUKIT", "KATIL,"], ["*KITA"], ["*TAWAN!"]], size=230, anim="slam", flash=True),
    # CHORUS
    dict(at=[23.1], end=24.15, lines=[["#MUAFAKAT!"]], size=220, anim="pop", flash=True, glitch=True),
    dict(at=[24.24, 24.46], end=25.6, lines=[["KITA"], ["*BERPAKAT!"]], size=250, anim="slam", shake=True),
    dict(at=[26.0, 26.74, 27.5, 28.26], end=29.45, lines=[["BUKIT", "KATIL"], ["MEMBAWA"], ["*BERKAT!"]], size=200, anim="rise"),
    dict(at=[29.58, 30.26], end=31.45, lines=[["SATU"], ["*SUARA!"]], size=290, anim="slam", flash=True, glitch=True),
    dict(at=[31.9, 32.3], end=32.7, lines=[["HEI!"], ["*HEI!"]], size=260, anim="slam", shake=True),
    dict(at=[32.8, 33.34], end=35.1, lines=[["BERSAMA"], ["#PERIKATAN!"]], size=200, anim="side"),
    dict(at=[35.2, 35.76], end=36.7, lines=[["HEI!"], ["*HEI!"]], size=260, anim="slam", shake=True),
    dict(at=[36.78, 37.76, 39.84, 40.74], end=44.9, lines=[["BUKIT", "KATIL,"], ["*KITA", "*TAWAN!"]], size=190, anim="slam", flash=True, shake=True),
    # OUTRO
    dict(at=[45.02, 45.5], end=45.8, lines=[["HEI!"], ["*HEI!"]], size=300, anim="slam", flash=True, shake=True),
    dict(at=[45.82, 46.0, 46.6], end=47.1, lines=[["GENG", "BUKIT"], ["*KATIL!"]], size=230, anim="slam"),
    dict(at=[47.16, 47.88], end=48.9, lines=[["KITA"], ["#MARA!"]], size=290, anim="slam", flash=True, glitch=True),
    dict(at=[48.96, 49.25, 49.62, 50.46], end=52.6, lines=[["KITA", "*BERSAMA!"], ["BERSAMA"], ["#PERIKATAN!"]], size=200, anim="rise"),
    dict(at=[52.7, 53.74, 54.64, 55.18], end=56.35, lines=[["BUKIT", "KATIL"], ["*KITA", "*TAWAN"]], size=190, anim="slam", flash=True),
    dict(at=[56.44, 57.3, 58.2, 58.7], end=60.0, lines=[["BUKIT", "KATIL"], ["#KITA", "#TAWAN"]], size=190, anim="drop", flash=True, glitch=True),
    dict(at=[60.12, 60.64, 63.04, 63.94], end=66.7, lines=[["BUKIT", "KATIL"], ["*KITA", "*TAWAN!"]], size=200, anim="slam", flash=True, shake=True),
    dict(at=[66.82, 67.8, 70.14, 71.04], end=72.3, lines=[["BUKIT", "KATIL"], ["#KITA", "#TAWAN!"]], size=200, anim="side", flash=True, glitch=True),
    dict(at=[72.4, 72.84, 73.28, 73.72], end=79.6, lines=[["BUKIT"], ["KATIL"], ["*KITA"], ["*TAWAN!"]], size=250, anim="slam",
         flash=True, shake=True, final=True),
]
for c in CUES:
    if "at" in c:
        c["t"] = c["at"][0]


def word_time(c, idx):
    if "at" in c:
        return c["at"][min(idx, len(c["at"]) - 1)]
    return c["t"] + idx * c.get("step", 0.44)


FLASHES = sorted(set([c["t"] for c in CUES if c.get("flash")]))
SECTION_SWEEPS = [1.0, 15.1, 23.1, 45.02, 52.7, 72.4]
HIGH_ENERGY = lambda t: t >= 22.8


# ---------------------------------------------------------------- sprites
_font_cache, _spr_cache = {}, {}

def font(name, size):
    key = (name, size)
    if key not in _font_cache:
        path = {"anton": F_ANTON, "bebas": F_BEBAS, "mont": F_MONT}[name]
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def word_sprite(word, size, fname="anton", kind=None, tracking=0):
    """Return RGBA sprite for a word; kind in (None,'outline','ghost','red','cyan')."""
    style = "w"
    if word.startswith("*"): style, word = "g", word[1:]
    elif word.startswith("#"): style, word = "b", word[1:]
    key = (word, size, fname, style, kind, tracking)
    if key in _spr_cache:
        return _spr_cache[key]
    f = font(fname, size)
    pad = int(size * 0.25)
    if tracking:
        widths = [f.getlength(ch) for ch in word]
        tw = int(sum(widths) + tracking * (len(word) - 1))
    else:
        tw = int(f.getlength(word))
    asc, desc = f.getmetrics()
    th = asc + desc
    img = Image.new("RGBA", (tw + 2 * pad, th + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    stroke = max(2, size // 40)

    def draw_text(fill, sfill=None, sw=0):
        if tracking:
            x = pad
            for ch, wch in zip(word, widths):
                d.text((x, pad), ch, font=f, fill=fill, stroke_width=sw, stroke_fill=sfill)
                x += wch + tracking
        else:
            d.text((pad, pad), word, font=f, fill=fill, stroke_width=sw, stroke_fill=sfill)

    if kind in ("outline", "ghost"):
        col = GOLD if (style != "w" or kind == "outline") else WHITE
        draw_text((0, 0, 0, 0), col + (255,), max(3, size // 28))
    else:
        if style == "b":
            bx0, by0 = pad - size * 0.12, pad + size * 0.10
            bx1, by1 = pad + tw + size * 0.12, pad + th - size * 0.02
            d.rectangle([bx0, by0, bx1, by1], fill=GOLD + (255,))
            draw_text(NAVY + (255,))
        else:
            col = GOLD if style == "g" else WHITE
            draw_text(col + (255,), NAVY + (255,), stroke)
        if kind in ("red", "cyan"):
            a = img.split()[3]
            c = (255, 40, 60) if kind == "red" else (0, 230, 255)
            img = Image.merge("RGBA", (*[Image.new("L", img.size, v) for v in c], a.point(lambda v: v * 0.7)))
        else:
            # soft drop shadow for depth
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            sh.putalpha(img.split()[3].point(lambda v: v * 0.75))
            sh = Image.merge("RGBA", (*[Image.new("L", img.size, 0)] * 3, sh.split()[3]))
            sh = sh.filter(ImageFilter.GaussianBlur(size / 14))
            base = Image.new("RGBA", img.size, (0, 0, 0, 0))
            base.alpha_composite(sh, (0, int(size / 18)))
            base.alpha_composite(img)
            img = base
    _spr_cache[key] = (img, pad, tw, th)
    return _spr_cache[key]


def layout(cue):
    """Compute per-word positions (centre x,y) and fitted font size."""
    if "_lay" in cue:
        return cue["_lay"]
    fname = cue.get("font", "anton")
    size = cue["size"]
    gap_fac = 0.22
    while True:
        f = font(fname, size)
        widths = [[f.getlength(w.lstrip("*#")) for w in line] for line in cue["lines"]]
        lw = [sum(ws) + gap_fac * size * (len(ws) - 1) for ws in widths]
        lh = size * (1.12 if fname == "anton" else 1.2)
        if max(lw) <= 960 and lh * len(cue["lines"]) <= 760:
            break
        size -= 6
    total_h = lh * len(cue["lines"])
    words = []
    for li, line in enumerate(cue["lines"]):
        y = CY - total_h / 2 + lh * (li + 0.5)
        x = W / 2 - lw[li] / 2
        for wi, w in enumerate(line):
            ww = widths[li][wi]
            words.append(dict(w=w, cx=x + ww / 2, cy=y, line=li, idx=len(words)))
            x += ww + gap_fac * size
    cue["_lay"] = (words, size, fname)
    return cue["_lay"]


def comp(dst, src, x, y):
    """alpha_composite src onto dst at (x, y), clipping to bounds."""
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst.alpha_composite(src, (x + sx0, y + sy0), (sx0, sy0, sx1, sy1))


def paste(canvas, spr, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    img, pad, tw, th = spr
    if alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.005 or rot:
        nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
        img = img.resize((nw, nh), Image.BILINEAR)
        if rot:
            img = img.rotate(rot, Image.BILINEAR, expand=True)
    if alpha < 0.999:
        a = img.split()[3].point(lambda v: int(v * alpha))
        img = img.copy(); img.putalpha(a)
    x = int(cx - img.width / 2); y = int(cy - img.height / 2)
    comp(canvas, img, x, y)


# ---------------------------------------------------------------- background
_bg = Image.open(BG).convert("RGB")
_bg = _bg.resize((W, int(_bg.height * W / _bg.width)), Image.LANCZOS)
_off = (_bg.height - H) // 2
BGIMG = _bg.crop((0, _off, W, _off + H))

def make_vignette():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - CY) / (H * 0.62)) ** 2)
    v = np.clip((r - 0.45) * 1.1, 0, 0.75)
    return Image.fromarray((v * 255).astype(np.uint8))
VIGNETTE = make_vignette()

# centre glow (blue light behind lyrics)
def make_glow():
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / 520) ** 2 + ((yy - CY) / 420) ** 2)
    g = np.exp(-r ** 2 * 1.6)
    a = (g * 255).astype(np.uint8)
    img = Image.new("RGBA", (W, H), (40, 120, 220, 0)); img.putalpha(Image.fromarray(a))
    return img
GLOW = make_glow()

MARQ_TEXT = "BUKIT KATIL  •  KITA TAWAN  •  "
def make_marquee(color):
    f = font("anton", 330)
    tw = int(f.getlength(MARQ_TEXT))
    img = Image.new("RGBA", (tw * 2, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(2):
        d.text((k * tw, 20), MARQ_TEXT, font=f, fill=(0, 0, 0, 0), stroke_width=3, stroke_fill=color)
    return img, tw
MARQ, MARQ_W = make_marquee((90, 160, 240, 70))

rng = np.random.default_rng(7)
NP = 70
P_X = rng.uniform(0, W, NP); P_Y0 = rng.uniform(0, H, NP)
P_V = rng.uniform(25, 110, NP); P_S = rng.uniform(2, 7, NP); P_PH = rng.uniform(0, 6.28, NP)
P_DR = rng.uniform(-20, 20, NP)

def particle_sprite(r):
    s = int(r * 6)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=GOLD + (255,))
    img = img.filter(ImageFilter.GaussianBlur(r * 0.9))
    d = ImageDraw.Draw(img)
    d.ellipse([s / 2 - r / 2.5, s / 2 - r / 2.5, s / 2 + r / 2.5, s / 2 + r / 2.5], fill=(255, 240, 200, 255))
    return img
P_SPR = {k: particle_sprite(k) for k in range(2, 8)}

def make_sweep():
    w = 260
    img = Image.new("L", (w * 3, H * 2), 0)
    arr = np.zeros((H * 2, w * 3), np.float32)
    x = np.arange(w * 3)
    arr[:] = np.exp(-((x - w * 1.5) / (w * 0.45)) ** 2)
    a = Image.fromarray((arr * 120).astype(np.uint8)).rotate(18, Image.BILINEAR, expand=False)
    out = Image.new("RGBA", a.size, (255, 230, 170, 0)); out.putalpha(a)
    return out
SWEEP = make_sweep()


def beat_pulse(t, decay=0.11):
    i = np.searchsorted(BEATS, t) - 1
    if i < 0: return 0.0
    return math.exp(-(t - BEATS[i]) / decay)


def recent(ts, t, win):
    best = None
    for x in ts:
        if x <= t < x + win: best = x
    return best


def shake_offset(t):
    amt = 0.0
    for c in CUES:
        if not c.get("shake"): continue
        words, _, _ = layout(c)
        for w in words:
            land = word_time(c, w["idx"]) + 0.12
            if land <= t < land + 0.25:
                amt = max(amt, 22 * (1 - (t - land) / 0.25))
    for x in FLASHES:
        if x <= t < x + 0.2:
            amt = max(amt, 14 * (1 - (t - x) / 0.2))
    if amt <= 0: return 0, 0
    r = random.Random(int(t * 1000))
    return int(r.uniform(-amt, amt)), int(r.uniform(-amt, amt))


# ---------------------------------------------------------------- frame
def render_cue(canvas, c, t):
    words, size, fname = layout(c)
    anim = c["anim"]
    step = c.get("step", 0.44)
    t0, t1 = c["t"], c["end"]
    out_d = 0.14 if not c.get("final") else 0.5
    exit_p = clamp((t - (t1 - out_d)) / out_d)
    exit_s = 1 + 0.25 * e_out_cubic(exit_p)
    exit_a = 1 - exit_p
    final_zoom = 1.0
    if c.get("final"):
        final_zoom = 1 + 0.06 * clamp((t - t0 - 2) / 4)
    for w in words:
        ws = word_time(c, w["idx"])
        if anim == "track":
            ws = t0
        if t < ws:
            continue
        lt = t - ws
        cx, cy = w["cx"], w["cy"]
        cx = W / 2 + (cx - W / 2) * final_zoom
        cy = CY + (cy - CY) * final_zoom
        sc, al, rot = 1.0, 1.0, 0.0
        if anim == "slam":
            p = clamp(lt / 0.16)
            sc = 2.6 - 1.6 * e_out_cubic(p); al = clamp(lt / 0.08)
        elif anim == "pop":
            p = clamp(lt / 0.35)
            sc = 0.2 + 0.8 * e_out_back(p); al = clamp(lt / 0.1)
        elif anim == "rise":
            p = clamp(lt / 0.4)
            cy += 140 * (1 - e_out_expo(p)); al = clamp(lt / 0.2)
        elif anim == "drop":
            p = clamp(lt / 0.55)
            cy -= 260 * (1 - e_out_bounce(p)); al = clamp(lt / 0.1)
        elif anim == "side":
            p = clamp(lt / 0.35)
            dirn = -1 if w["line"] % 2 == 0 else 1
            cx += dirn * 900 * (1 - e_out_expo(p)); al = clamp(lt / 0.15)
            rot = dirn * -6 * (1 - e_out_cubic(p))
        sc *= exit_s * final_zoom
        al *= exit_a
        if anim == "outline":
            p = clamp(lt / 0.5)
            sc = (1.5 - 0.5 * e_out_expo(p)) * exit_s
            pulse = beat_pulse(t)
            paste(canvas, word_sprite(w["w"], size, fname, "outline"), cx, cy, sc * (1 + 0.04 * pulse), al * (0.55 + 0.45 * pulse))
            continue
        if anim == "track":
            p = clamp(lt / 1.4)
            tr = int(size * (1.2 - 1.0 * e_out_expo(p)))
            line_spr = word_sprite(" ".join(x["w"] for x in words), size, fname, None, tracking=tr)
            paste(canvas, line_spr, W / 2, CY, exit_s, al * clamp(lt / 0.4))
            return
        # glitch copies right after landing
        if c.get("glitch") and lt < 0.3:
            g = (1 - lt / 0.3)
            r = random.Random(int(t * 997) + w["idx"])
            dx = r.uniform(10, 28) * g
            paste(canvas, word_sprite(w["w"], size, fname, "red"), cx - dx, cy + r.uniform(-6, 6), sc, al * g)
            paste(canvas, word_sprite(w["w"], size, fname, "cyan"), cx + dx, cy + r.uniform(-6, 6), sc, al * g)
        # echo ghost ring after landing (impact)
        land = 0.16 if anim == "slam" else 0.3
        if lt > land * 0.6 and lt < land + 0.45:
            gp = (lt - land * 0.6) / 0.45
            paste(canvas, word_sprite(w["w"], size, fname, "ghost"), cx, cy, sc * (1 + 0.45 * e_out_cubic(gp)), al * (1 - gp) * 0.8)
        # beat breathe on held text
        if HIGH_ENERGY(t) and lt > 0.3:
            sc *= 1 + 0.025 * beat_pulse(t, 0.09)
        paste(canvas, word_sprite(w["w"], size, fname), cx, cy, sc, al, rot)


def render_frame(fi):
    t = fi / FPS
    # --- background with slow push-in + beat pulse
    zoom = 1.0 + 0.05 * (t / DUR)
    if HIGH_ENERGY(t):
        zoom += 0.012 * beat_pulse(t, 0.1)
    sx, sy = shake_offset(t)
    cw, ch = W / zoom, H / zoom
    x0 = (W - cw) / 2 - sx * 0.4 / zoom; y0 = (H - ch) / 2 - sy * 0.4 / zoom
    bg = BGIMG.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BILINEAR).convert("RGBA")
    # glow behind lyrics, intensifies with bass
    bass = float(SPEC[min(fi, len(SPEC) - 1), :4].mean())
    ga = 0.35 + 0.55 * bass
    g = GLOW.copy(); g.putalpha(g.split()[3].point(lambda v: int(v * ga)))
    bg.alpha_composite(g)
    # scrolling outline marquee behind lyrics
    mx = int((t * 140) % MARQ_W)
    bg.alpha_composite(MARQ, (0, CY - 210), (mx, 0, mx + W, MARQ.height))

    # --- audio reactive gold bars just above the bottom slogan
    spec = SPEC[min(fi, len(SPEC) - 1)]
    d = ImageDraw.Draw(bg)
    nb = len(spec); bw = 26; gap = 10
    total = nb * bw + (nb - 1) * gap
    bx = (W - total) // 2
    base_y = 1690
    for i in range(nb):
        v = float(spec[i])  # mirrored spectrum, bass in the centre
        hgt = int(8 + v * 150)
        x = bx + i * (bw + gap)
        d.rounded_rectangle([x, base_y - hgt, x + bw, base_y], radius=6, fill=GOLD + (int(90 + 120 * v),))

    # --- particles (gold embers rising)
    speed = 1.0 + (0.8 if HIGH_ENERGY(t) else 0)
    for i in range(NP):
        y = (P_Y0[i] - P_V[i] * t * speed) % (H + 40) - 20
        x = P_X[i] + P_DR[i] * math.sin(t * 0.8 + P_PH[i])
        tw = 0.5 + 0.5 * math.sin(t * 3 + P_PH[i])
        spr = P_SPR[int(P_S[i])]
        a = 0.25 + 0.6 * tw
        sp = spr.copy(); sp.putalpha(sp.split()[3].point(lambda v, a=a: int(v * a)))
        comp(bg, sp, int(x) % W, int(y))

    # --- lyric layer
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for c in CUES:
        if c["t"] <= t < c["end"]:
            render_cue(txt, c, t)
    comp(bg, txt, sx, sy)

    # --- light sweep on section starts
    s0 = recent(SECTION_SWEEPS, t, 0.9)
    if s0 is not None:
        p = (t - s0) / 0.9
        xs = int(-SWEEP.width + p * (W + SWEEP.width * 1.2))
        comp(bg, SWEEP.crop((0, H // 2, SWEEP.width, H // 2 + H)), xs, 0)

    # --- vignette
    dark = Image.new("RGBA", (W, H), (0, 6, 20, 0)); dark.putalpha(VIGNETTE)
    bg.alpha_composite(dark)

    # --- flash on impacts
    f0 = recent(FLASHES, t, 0.22)
    if f0 is not None:
        a = 0.55 * (1 - (t - f0) / 0.22) ** 2
        fl = Image.new("RGBA", (W, H), (255, 245, 220, int(255 * a)))
        bg.alpha_composite(fl)

    # --- fades
    if t < 0.4:
        bg = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), bg, t / 0.4)
    if t > DUR - 0.6:
        bg = Image.blend(bg, Image.new("RGBA", (W, H), (0, 0, 0, 255)), clamp((t - (DUR - 0.6)) / 0.6))
    return bg.convert("RGB")


def run_segment(seg, nseg):
    a = NF * seg // nseg; b = NF * (seg + 1) // nseg
    out = os.path.join(HERE, f"seg{seg}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fi in range(a, b):
        p.stdin.write(render_frame(fi).tobytes())
        if (fi - a) % 150 == 0:
            print(f"seg{seg} {fi - a}/{b - a}", flush=True)
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "still":
        for t in map(float, sys.argv[2:]):
            render_frame(int(t * FPS)).save(os.path.join(HERE, f"still_{t:05.2f}.jpg"), quality=85)
    else:
        run_segment(int(sys.argv[2]), int(sys.argv[3]))
