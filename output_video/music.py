"""120 BPM uplifting electronic corporate track, synced to render.py timeline. Usage: python3 -I music.py out.wav"""
import sys, wave
import numpy as np

SR = 44100
BPM = 120
B = 60 / BPM
TOTAL = 67.5
N = int((TOTAL + 2.5) * SR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)

# timeline (matches render.py)
DIVS = [4.0, 27.0, 46.5]          # section-divider starts (impacts)
CAROUSELS = [(6.0, 6), (29.0, 5), (48.5, 4)]
OUTRO = 62.5
SWIPES = []
for st, n in CAROUSELS:
    for k in range(1, n):
        SWIPES.append(st + k * 3.5 - .5)

def midi(m):
    return 440 * 2 ** ((m - 69) / 12)

def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= N: return
    sig = sig[: N - i]
    buf[i:i + len(sig)] += sig * gain

def addst(start, sig, g=1.0, pan=0.0):
    add(L, start, sig, g * (1 - max(pan, 0)))
    add(R, start, sig, g * (1 + min(pan, 0)))

def saw(f, dur, harm_max=8000, phase=0.0):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    k = 1
    while k * f < min(harm_max, SR / 2 - 1000):
        out += ((-1) ** (k + 1)) * np.sin(2 * np.pi * k * f * t + phase * k) / k
        k += 1
    return out * 2 / np.pi

def env(n, a=.005, d=.1, s=.6, r=.1, dur=None):
    t = np.arange(n) / SR
    dur = dur or n / SR
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / d))
    rel = np.clip((dur - t) / r, 0, 1)
    return e * rel

# ---------- arrangement helpers ----------
def section(t):
    """intensity 0..1 by time"""
    if t < 4: return .35
    for d in DIVS:
        if d <= t < d + 2: return .5
    if t >= OUTRO: return .4
    if t >= 48.5: return 1.0
    if t >= 29: return .85
    return .75

def drums_on(t):
    if t < 2: return False
    for d in DIVS[1:]:
        if d - .0 <= t < d + 2: return False
    if t >= OUTRO: return False
    return True

# chords: Am F C G  (one bar = 2s each)
PROG = [[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]]
ROOT = [45, 41, 48, 43]

# ---------- kick ----------
def kick():
    n = int(.45 * SR); t = np.arange(n) / SR
    f = 50 + 120 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7)
    s += .3 * rng.standard_normal(n) * np.exp(-t * 200)
    return np.tanh(s * 1.6)
K = kick()

def clap():
    n = int(.3 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    nz = nz - np.convolve(nz, np.ones(6) / 6, 'same')  # high-pass-ish
    e = sum(np.exp(-np.clip(t - o, 0, None) * 60) * (t >= o) for o in (0, .012, .024)) + .6 * np.exp(-t * 14)
    return nz * e * .5
C = clap()

def hat(open_=False):
    n = int((.22 if open_ else .05) * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    nz = np.diff(np.concatenate([[0], nz]))
    return nz * np.exp(-t * (18 if open_ else 90)) * .25
HC, HO = hat(), hat(True)

kicks = []
for i in range(int(TOTAL / B) + 1):
    t = i * B
    if drums_on(t):
        addst(t, K, .9)
        kicks.append(t)
        if i % 2 == 1: addst(t, C, .55 * (section(t) > .6) + .25, .0)
        addst(t + B / 2, HO, .35 * section(t), .25)
        for q in (0, .25, .75):
            addst(t + q * B, HC, .25 * section(t), -.3)
# drum fills (snare roll into each divider)
for d in DIVS[1:] + [OUTRO]:
    for j in range(8):
        tt = d - 1.0 + j * .125
        addst(tt, C, .2 + .05 * j)

# ---------- sidechain envelope ----------
sc = np.ones(N)
dk = int(.35 * SR)
curve = 1 - .7 * np.exp(-np.arange(dk) / SR * 12)
for t in kicks:
    i = int(t * SR); m = min(dk, N - i)
    sc[i:i + m] = np.minimum(sc[i:i + m], curve[:m])

# ---------- pads (supersaw) ----------
padL = np.zeros(N); padR = np.zeros(N)
bar = 2 * B * 2  # 2 seconds
for b in range(int(TOTAL / bar) + 2):
    t0 = b * bar
    ch = PROG[b % 4]
    inten = section(t0)
    cutoff = 1500 + 4000 * inten
    for m in ch:
        for det, pan in ((-.12, -.7), (0, 0), (.12, .7)):
            f = midi(m + 12) * 2 ** (det / 12)
            s = saw(f, bar + .1, cutoff, phase=rng.uniform(0, 6)) * env(int((bar + .1) * SR), a=.03, d=1, s=.8, r=.08)
            add(padL, t0, s, .045 * (1 - max(pan, 0)))
            add(padR, t0, s, .045 * (1 + min(pan, 0)))
L += padL * sc; R += padR * sc

# ---------- bass (offbeat pumping) ----------
for i in range(int(TOTAL / (B / 2))):
    t = i * B / 2
    if t < 4 or t >= OUTRO + 2: continue
    b = int(t // 2) % 4
    if i % 2 == 1 or section(t) > .9:
        f = midi(ROOT[b] - 12 + 12 * (i % 4 == 3 and section(t) > .8))
        s = saw(f, B / 2 * .95, 900) * env(int(B / 2 * .95 * SR), a=.004, d=.08, s=.5, r=.03)
        s += .6 * np.sin(2 * np.pi * f * np.arange(len(s)) / SR) * env(len(s), a=.004, d=.2, s=.7, r=.03)
        addst(t, np.tanh(s * 1.4), .32 * (.6 if not drums_on(t) else 1))

# ---------- pluck arpeggio (16ths) ----------
ARP = [0, 1, 2, 1, 2, 0, 1, 2]
for i in range(int(TOTAL / (B / 4))):
    t = i * B / 4
    if t < 2 or t >= OUTRO + 3: continue
    b = int(t // 2) % 4
    ch = PROG[b]
    m = ch[ARP[i % 8] % len(ch)] + 24 - (12 if i % 16 >= 8 and section(t) < .8 else 0)
    dur = .22
    s = saw(midi(m), dur, 2500 + 3500 * section(t)) * env(int(dur * SR), a=.002, d=.06, s=.0, r=.05)
    pan = .45 if i % 2 else -.45
    g = .11 * (.5 + .5 * section(t))
    addst(t, s, g, pan)
    addst(t + .375, s, g * .35, -pan)   # dotted-8th echo

# ---------- lead hook in the final carousel ----------
HOOK = [(0, 76, .5), (.5, 74, .5), (1, 72, .5), (1.5, 74, .5), (2, 72, .75), (3, 71, .5), (3.5, 69, .5)]
for rep in range(4):
    base = 48.5 + 1.5 + rep * 4  # aligned to bar grid  (50, 54, 58)
    base = 50 + rep * 4
    if base >= OUTRO: break
    for o, m, d in HOOK:
        f = midi(m)
        t = np.arange(int(d * SR)) / SR
        vib = 1 + .004 * np.sin(2 * np.pi * 5.5 * t)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        s = sum(np.sin(k * ph) / k for k in range(1, 9)) * env(len(t), a=.01, d=.3, s=.7, r=.06)
        addst(base + o, s, .07, 0)
        addst(base + o + .25, s, .025, .6)

# ---------- FX: risers, impacts, whooshes ----------
def noise_sweep(dur, up=True, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    # crude moving filter: mix of smoothed and raw noise
    sm = np.convolve(nz, np.ones(24) / 24, 'same')
    p = (t / dur) if up else (1 - t / dur)
    s = sm * (1 - p) + nz * p * bright
    amp = p ** 2 if up else (1 - t / dur) ** 2
    return s * amp

def impact():
    n = int(2.5 * SR); t = np.arange(n) / SR
    f = 30 + 80 * np.exp(-t * 8)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    nz = rng.standard_normal(n)
    tail = np.convolve(nz, np.ones(40) / 40, 'same') * np.exp(-t * 3) * 1.5
    return np.tanh((boom + tail) * 1.5)
IMP = impact()

def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 200 * 2 ** (3 * t / dur)
    s = saw(1, 0.01)  # placeholder unused
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) ** 2 * .3
    return tone + noise_sweep(dur, True) * .5

addst(0, riser(4.0), .35)
for d in DIVS:
    addst(d - 2.0 if d > 4 else 2.0, riser(2.0), .3)
    addst(d, IMP, .8)
addst(OUTRO, IMP, .9)
addst(6.0, IMP, .45)
for s in SWIPES:
    w = noise_sweep(.35, True, .8)
    w = np.concatenate([w, noise_sweep(.25, False, .8)])
    addst(s + .05, w, .22, .3)
    addst(s + .5, K[: int(.2 * SR)], .25)  # sub thump on landing

# ---------- outro: sustained chord, fade ----------
for m in [45, 57, 60, 64, 69, 72]:
    s = saw(midi(m), 5.5, 2500) * env(int(5.5 * SR), a=.02, d=2, s=.5, r=2.5)
    addst(OUTRO, s, .05, rng.uniform(-.5, .5))

# ---------- master ----------
mix = np.stack([L, R], 1)
# simple stereo reverb-ish: few delayed taps
for dl, g in ((.031, .18), (.047, .14), (.073, .1), (.113, .07)):
    k = int(dl * SR)
    mix[k:, 0] += mix[:-k, 1] * g
    mix[k:, 1] += mix[:-k, 0] * g
mix = mix[: int(TOTAL * SR)]
t = np.arange(len(mix)) / SR
mix *= np.clip(t / .05, 0, 1)[:, None] * np.clip((TOTAL - t) / 2.0, 0, 1)[:, None]
mix /= np.percentile(np.abs(mix), 99.9) + 1e-9
mix = np.tanh(mix * 1.2) * .89
out = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(out.tobytes())
print("ok", len(out) / SR)
