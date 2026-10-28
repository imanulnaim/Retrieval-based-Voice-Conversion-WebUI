"""Carousel motion-graphics renderer. Usage: python3 -I render.py <in_dir> <out_dir> [preview]"""
import sys, os, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

IN, OUT = sys.argv[1], sys.argv[2]
PREVIEW = len(sys.argv) > 3
W, H, FPS = 1080, 1920, 30
BEAT = 0.5  # 120 BPM
F = "/usr/share/fonts/opentype/inter/"

def font(name, size):
    return ImageFont.truetype(F + name, size)

def P(stamp):
    return os.path.join(IN, f"WhatsApp Image 2026-10-28 at {stamp}.jpeg")

# Story order: keynote 1 -> keynote 2 -> closing remarks (by "PETIKAN" number)
SECTIONS = [
    ("KEYNOTE", "YAB Dato' Seri Ir. Dr.\nAhmad Samsuri Mokhtar", "Menteri Besar Terengganu", (64, 132, 255),
     ["2.54.13 PM (1)", "2.54.14 PM (1)", "2.54.14 PM", "2.54.14 PM (2)", "2.54.15 PM", "2.54.15 PM (1)"]),
    ("KEYNOTE", "YB Dato' Dr. Mohamed Fadzli\nbin Dato' Hj Hassan", "Timbalan Menteri Besar Kelantan", (236, 72, 96),
     ["2.54.11 PM (1)", "2.54.11 PM (2)", "2.54.12 PM", "2.54.12 PM (1)", "2.54.13 PM"]),
    ("CLOSING REMARK", "Dr. Haim Hilman Abdullah", "Pengerusi, SG4 Group Sdn. Bhd.", (240, 176, 64),
     ["2.54.10 PM", "2.54.10 PM (1)", "2.54.10 PM (2)", "2.54.11 PM"]),
]

CW, CH = 820, 1025  # card size (4:5)
cards, blurs, accents = [], [], []
seq = []  # (section index, card index)
for si, (_, _, _, acc, stamps) in enumerate(SECTIONS):
    for s in stamps:
        im = Image.open(P(s)).convert("RGB").resize((CW, CH), Image.LANCZOS)
        # rounded corners
        m = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, CW - 1, CH - 1], 36, fill=255)
        im.putalpha(m)
        cards.append(im)
        bg = Image.open(P(s)).convert("RGB").resize((W // 4, H // 4)).filter(ImageFilter.GaussianBlur(14)).resize((W, H), Image.BILINEAR)
        blurs.append(np.asarray(bg, dtype=np.float32))
        seq.append(si)

def ease(t):  # easeInOutQuint-ish (snappy)
    t = min(max(t, 0), 1)
    return 16 * t ** 5 if t < .5 else 1 - (-2 * t + 2) ** 5 / 2

def ease_out(t):
    t = min(max(t, 0), 1)
    return 1 - (1 - t) ** 4

def back_out(t):
    t = min(max(t, 0), 1); c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

# ---------- timeline (seconds, on the 120bpm grid) ----------
INTRO = 4.0
DIV = 2.0
HOLD = 3.5   # time each card sits centred (incl. transition in)
TR = 0.5
OUTRO = 5.0
events = []  # (kind, start, dur, payload)
t = 0
events.append(("intro", t, INTRO, None)); t += INTRO
ci = 0
for si, sec in enumerate(SECTIONS):
    events.append(("div", t, DIV, si)); t += DIV
    n = len(sec[4])
    events.append(("carousel", t, n * HOLD, (ci, n, si))); t += n * HOLD
    ci += n
events.append(("outro", t, OUTRO, None)); t += OUTRO
TOTAL = t

# ---------- drawing helpers ----------
def grad_bg(phase, acc):
    y = np.linspace(0, 1, H)[:, None]
    x = np.linspace(0, 1, W)[None, :]
    base = np.zeros((H, W, 3), np.float32)
    base += np.array([8, 10, 22], np.float32)
    cx, cy = .5 + .25 * math.sin(phase), .35 + .1 * math.cos(phase * .7)
    d = np.sqrt((x - cx) ** 2 + ((y - cy) * 1.7) ** 2)
    glow = np.clip(1 - d * 1.6, 0, 1) ** 2
    base += glow[..., None] * np.array(acc, np.float32) * .55
    d2 = np.sqrt((x - (1 - cx)) ** 2 + ((y - .85) * 1.7) ** 2)
    base += (np.clip(1 - d2 * 2, 0, 1) ** 2)[..., None] * np.array([40, 60, 140], np.float32) * .6
    return base

_bgcache = {}
def bg_for(key, phase, acc):
    k = (key, round(phase, 2))
    return grad_bg(phase, acc)

class BlendDraw:
    """ImageDraw on an RGBA image that alpha-blends instead of overwriting."""
    def __init__(self, img):
        self.img = img
    def __getattr__(self, name):
        def f(*a, **k):
            if "bbox" in name:
                return getattr(ImageDraw.Draw(self.img), name)(*a, **k)
            layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            r = getattr(ImageDraw.Draw(layer), name)(*a, **k)
            self.img.alpha_composite(layer)
            return r
        return f

def grid_overlay(img, t, alpha=28):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    off = int((t * 40) % 90)
    for x in range(-90 + off, W, 90):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, alpha))
    for y in range(-90 + off, H, 90):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, alpha))
    img.alpha_composite(layer)

def text_c(d, y, s, f, fill, spacing=10, x=None):
    bb = d.multiline_textbbox((0, 0), s, font=f, spacing=spacing, align="center")
    w = bb[2] - bb[0]
    d.multiline_text(((W - w) / 2 if x is None else x, y), s, font=f, fill=fill, spacing=spacing, align="center")
    return bb[3] - bb[1]

def reveal_text(base, y, s, f, fill, p, spacing=10):
    """Text slides up from a mask line as p goes 0->1."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.multiline_textbbox((0, 0), s, font=f, spacing=spacing, align="center")
    h = bb[3] + 12
    dy = int((1 - ease_out(p)) * h)
    text_c(d, y + dy, s, f, fill, spacing)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rectangle([0, y - 6, W, y + h], fill=255)
    a = layer.split()[3]
    layer.putalpha(Image.fromarray(np.minimum(np.asarray(a), np.asarray(mask))))
    base.alpha_composite(layer)

def pill(d, cx, y, s, f, acc, alpha=255):
    bb = d.textbbox((0, 0), s, font=f)
    w = bb[2] - bb[0] + 60
    d.rounded_rectangle([cx - w / 2, y, cx + w / 2, y + 64], 32, fill=acc + (alpha,))
    d.text((cx - (bb[2] - bb[0]) / 2, y + 32 - (bb[3] + bb[1]) / 2), s, font=f, fill=(255, 255, 255, alpha))

def shadowed(card, scale, alpha):
    w, h = int(CW * scale), int(CH * scale)
    c = card.resize((w, h), Image.BILINEAR)
    if alpha < 1:
        a = np.asarray(c.split()[3], np.float32) * alpha
        c.putalpha(Image.fromarray(a.astype(np.uint8)))
    return c

SHADOW = None
def get_shadow():
    global SHADOW
    if SHADOW is None:
        pad = 120
        s = Image.new("RGBA", (CW + pad * 2, CH + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(s).rounded_rectangle([pad, pad + 30, pad + CW, pad + CH + 30], 40, fill=(0, 0, 0, 190))
        SHADOW = s.filter(ImageFilter.GaussianBlur(40))
    return SHADOW

def place(img, card, cx, cy, scale, alpha, shadow=True):
    if alpha <= 0.01:
        return
    if shadow:
        sh = get_shadow()
        sw, shh = int(sh.width * scale), int(sh.height * scale)
        s = sh.resize((sw, shh), Image.BILINEAR)
        if alpha < 1:
            s.putalpha(Image.fromarray((np.asarray(s.split()[3], np.float32) * alpha).astype(np.uint8)))
        img.alpha_composite(s, (int(cx - sw / 2), int(cy - shh / 2)))
    c = shadowed(card, scale, alpha)
    img.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))

FT_BIG = font("Inter-Black.otf", 120) if os.path.exists(F + "Inter-Black.otf") else font("Inter-Bold.otf", 120)
FT_H = font("Inter-ExtraBold.otf", 64) if os.path.exists(F + "Inter-ExtraBold.otf") else font("Inter-Bold.otf", 64)
FT_M = font("Inter-SemiBold.otf", 40)
FT_S = font("Inter-Bold.otf", 30)
FT_XS = font("Inter-Medium.otf", 30)

def counter_bar(img, idx, n, acc, local_p):
    d = BlendDraw(img)
    y = 1720
    seg = 70; gap = 14
    tw = n * seg + (n - 1) * gap
    x0 = (W - tw) / 2
    for i in range(n):
        x = x0 + i * (seg + gap)
        d.rounded_rectangle([x, y, x + seg, y + 8], 4, fill=(255, 255, 255, 60))
        fillp = 1 if i < idx else (local_p if i == idx else 0)
        if fillp > 0:
            d.rounded_rectangle([x, y, x + seg * fillp, y + 8], 4, fill=acc + (255,))

def frame(tt):
    for kind, st, du, pl in events:
        if st <= tt < st + du or (kind == "outro" and tt >= st):
            lt = tt - st
            break
    # beat pulse (kick on every beat)
    bp = (tt % BEAT) / BEAT
    pulse = math.exp(-bp * 6)

    if kind == "intro":
        acc = (64, 132, 255)
        bg = grad_bg(tt * .6, acc)
        img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
        grid_overlay(img, tt)
        # fan of cards flying in from bottom
        picks = [0, 6, 11, 3, 13]
        for k, ci in enumerate(picks):
            p = ease_out((lt - .15 * k) / 1.2)
            ang = (k - 2) * 9
            cx = W / 2 + (k - 2) * 170 * p
            cy = 1250 + (1 - p) * 900 + abs(k - 2) * 40
            c = shadowed(cards[ci], .5, 1).rotate(-ang * p, expand=True, resample=Image.BICUBIC)
            img.alpha_composite(c, (int(cx - c.width / 2), int(cy - c.height / 2)))
        d = BlendDraw(img)
        reveal_text(img, 330, "SG4", font("Inter-Bold.otf", 220), (255, 255, 255, 255), (lt - .3) / .6)
        reveal_text(img, 600, "BUSINESS & ECONOMIC", FT_H, (255, 255, 255, 255), (lt - .6) / .6)
        reveal_text(img, 690, "FORUM 2026", FT_H, (120, 170, 255, 255), (lt - .8) / .6)
        if lt > 1.3:
            a = int(255 * ease_out((lt - 1.3) / .5))
            text_c(d, 820, "Four States · One Economic Vision", FT_M, (220, 225, 240, a))
            ww = 420 * ease_out((lt - 1.3) / .8)
            d.rectangle([W / 2 - ww / 2, 790, W / 2 + ww / 2, 796], fill=(120, 170, 255, a))
        # exit flash
        if lt > INTRO - .25:
            f = (lt - (INTRO - .25)) / .25
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * f))))
        return img

    if kind == "div":
        si = pl
        lbl, name, role, acc, _ = SECTIONS[si]
        bg = grad_bg(tt * .6, acc)
        img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
        grid_overlay(img, tt)
        d = BlendDraw(img)
        # flash-in from previous
        # sweeping accent bars
        for k in range(3):
            p = ease((lt - k * .08) / .6)
            x1 = -W + p * 2 * W
            d.polygon([(x1, 0), (x1 + 160, 0), (x1 + 160 - 600, H), (x1 - 600, H)], fill=acc + (60 - k * 15,))
        num = f"0{si + 1}"
        a = int(255 * ease_out(lt / .4))
        text_c(d, 400, num, font("Inter-Bold.otf", 260), acc + (int(a * .35),))
        pill(d, W / 2, 720, lbl, FT_S, acc, int(255 * back_out(lt / .4)) if lt < .4 else 255)
        reveal_text(img, 840, name, font("Inter-Bold.otf", 70), (255, 255, 255, 255), (lt - .15) / .5, spacing=14)
        reveal_text(img, 1040, role, FT_M, (210, 215, 235, 255), (lt - .35) / .5)
        if lt < .2:
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - lt / .2)))))
        if lt > DIV - .3:  # wipe out
            p = ease((lt - (DIV - .3)) / .3)
            d.rectangle([0, H - p * H, W, H], fill=(8, 10, 22, 255))
        return img

    if kind == "carousel":
        c0, n, si = pl
        acc = SECTIONS[si][3]
        # position: continuous index; each slot HOLD long, transition in the last TR of the slot
        slot = lt / HOLD
        k = int(slot)
        frac = slot - k
        trp = ease((frac * HOLD - (HOLD - TR)) / TR) if k < n - 1 else 0
        pos = k + trp
        cur = c0 + min(k, n - 1)
        nxt = c0 + min(k + 1, n - 1)
        # background: blurred poster crossfade + darken + accent glow
        b = blurs[cur] * (1 - trp) + blurs[nxt] * trp
        g = grad_bg(tt * .5, acc)
        bg = b * .28 + g * .75
        img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
        grid_overlay(img, tt, 22)
        d = BlendDraw(img)
        # header
        d.text((70, 130), "SG4 BUSINESS & ECONOMIC FORUM 2026", font=FT_S, fill=(255, 255, 255, 230))
        d.rectangle([70, 180, 70 + 90, 186], fill=acc + (255,))
        lbl = SECTIONS[si][0]
        num = f"{min(k, n - 1) + 1:02d}/{n:02d}"
        bb = d.textbbox((0, 0), num, font=FT_H)
        d.text((W - 70 - bb[2], 112), num, font=FT_H, fill=(255, 255, 255, 255))
        d.text((70, 200), lbl, font=FT_XS, fill=acc + (255,))
        # cards: render neighbours behind, centre in front
        entry = ease_out(lt / .6)
        items = []
        for j in range(n):
            off = j - pos
            if abs(off) > 2.2:
                continue
            ao = abs(off)
            scale = (1.0 - .2 * min(ao, 1) - .08 * max(ao - 1, 0)) * (1 + .015 * pulse * (ao < .5))
            cx = W / 2 + off * 640 * (1 - .06 * min(ao, 1))
            cy = 960 + ao * 30 + (1 - entry) * 1300 * (1 + j * .1)
            alpha = max(0, 1 - .45 * ao)
            items.append((ao, j, cx, cy, scale, alpha))
        for ao, j, cx, cy, scale, alpha in sorted(items, key=lambda x: -x[0]):
            # motion-blur ghost while moving fast
            place(img, cards[c0 + j], cx, cy, scale, alpha)
            if ao > .15:
                dim = Image.new("RGBA", (int(CW * scale), int(CH * scale)), (0, 0, 0, int(140 * min(ao, 1))))
                m = Image.new("L", dim.size, 0)
                ImageDraw.Draw(m).rounded_rectangle([0, 0, dim.width - 1, dim.height - 1], int(36 * scale), fill=int(140 * min(ao, 1) * alpha))
                dim.putalpha(m)
                img.alpha_composite(dim, (int(cx - dim.width / 2), int(cy - dim.height / 2)))
        # accent frame bracket on current card
        if trp < .05 or trp > .95:
            ff = ease_out((frac * HOLD) / .4) if trp < .05 else 1
            x0, y0 = W / 2 - CW / 2 - 18, 960 - CH / 2 - 18
            x1, y1 = W / 2 + CW / 2 + 18, 960 + CH / 2 + 18
            L = 90 * ff
            for (px, py, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
                d.line([(px, py), (px + sx * L, py)], fill=acc + (255,), width=8)
                d.line([(px, py), (px, py + sy * L)], fill=acc + (255,), width=8)
        # progress
        idx = min(k, n - 1)
        counter_bar(img, idx, n, acc, min(frac * HOLD / (HOLD - TR), 1))
        # swipe hint arrows
        # flash on transition
        if 0 < trp < 1:
            fl = math.sin(trp * math.pi) * 40
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(fl))))
        if lt > n * HOLD - .25:
            p = (lt - (n * HOLD - .25)) / .25
            img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * p))))
        return img

    # outro
    acc = (64, 132, 255)
    bg = grad_bg(tt * .6, acc)
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")
    grid_overlay(img, tt)
    d = BlendDraw(img)
    # 3x5 mosaic of all posters assembling
    tw, th = 300, 375
    for i in range(15):
        r, c = divmod(i, 3)
        p = ease_out((lt - i * .05) / .7)
        x = W / 2 + (c - 1) * (tw + 16)
        y = 330 + r * (th + 16) * .52 + 0
        sc = .5 * p + .0001
        if p > 0.01:
            cc = shadowed(cards[i], tw / CW * p, .9 * p)
            img.alpha_composite(cc, (int(x - cc.width / 2), int(380 + r * 200 - cc.height / 2 + (1 - p) * 300)))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(H):
        pass
    gr = np.zeros((H, W, 4), np.uint8)
    yy = np.linspace(0, 1, H)
    gr[..., 3] = (np.clip((yy - .35) / .3, 0, 1) * 235).astype(np.uint8)[:, None]
    gr[..., :3] = (8, 10, 22)
    img.alpha_composite(Image.fromarray(gr, "RGBA"))
    reveal_text(img, 1230, "Bersatu. Bersaing.", font("Inter-Bold.otf", 92), (255, 255, 255, 255), (lt - 1.0) / .6)
    reveal_text(img, 1345, "Berjaya.", font("Inter-Bold.otf", 92), (120, 170, 255, 255), (lt - 1.2) / .6)
    if lt > 1.8:
        a = int(255 * ease_out((lt - 1.8) / .6))
        text_c(d, 1500, "SG4 BUSINESS & ECONOMIC FORUM 2026", FT_S, (255, 255, 255, a))
        text_c(d, 1550, "Terengganu · Kedah · Kelantan · Perlis", FT_XS, (190, 200, 225, a))
    if lt > OUTRO - .8:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * ease((lt - (OUTRO - .8)) / .8)))))
    return img


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if PREVIEW:
        for ts in [1.0, 3.0, 5.0, 7.0, 9.0, 11.25, 30.0, 75.0, TOTAL - 2.5]:
            frame(ts).convert("RGB").save(f"{OUT}/p_{ts:05.2f}.jpg", quality=80)
        print("TOTAL", TOTAL)
        sys.exit()
    part, nparts = int(os.environ.get("PART", 0)), int(os.environ.get("NPARTS", 1))
    N = int(TOTAL * FPS)
    lo, hi = N * part // nparts, N * (part + 1) // nparts
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", f"{OUT}/part{part}.mp4"],
                         stdin=subprocess.PIPE)
    for i in range(lo, hi):
        p.stdin.write(frame(i / FPS).convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    print("done", part, TOTAL)
