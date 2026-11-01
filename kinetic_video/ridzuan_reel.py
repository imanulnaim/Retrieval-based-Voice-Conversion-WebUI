#!/usr/bin/env python3
"""
Highlight reel: Ridzuan Sarif, calon N17 Bukit Katil (ceramah malam pertama kempen).

Cuts the strongest lines out of the four raw clips, writes a kinetic caption
script for them and renders it with kinetic.py.

Usage: python3 ridzuan_reel.py <folder with the raw clips> <song.mp3> <output.mp4>
Raw clips expected (by suffix): *1028_15.mp4 ... *1028_19.mp4
Song: "Bukit Katil Kita Tawan" - intro chant opens the reel, ducked under the
speech, full-power ending under the name card.

Caption text is a corrected transcript. Review it against the audio before
posting; lines marked (?) were unclear in the recording.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (clip, start, end, [(lead, KEY, tail), ...])   times are seconds in the raw clip
INTRO_SRC = ("16", 22.15, 25.15)          # muted, music + title only
INTRO = ("N17", "BUKIT KATIL", "kita tawan")
EDIT = [
    ("16", 31.11, 36.45, [("Pada malam ini", "malam pertama", ""),
                          ("kita", "berkempen", "")]),
    # --- testimonial (clip 19)
    ("19", 0.26, 7.65, [("semalam merupakan", "hari terakhir", "saya bertugas"),
                        ("di", "Jabatan Kesihatan", "Negeri Melaka")]),
    ("19", 9.03, 12.29, [("dan hari ini bermulalah", "hidup baru", "bagi saya")]),
    ("19", 16.71, 21.41, [("tempoh perkhidmatan saya", "dalam kerajaan", ""),
                          ("lebih kurang", "18 tahun", "")]),
    ("19", 22.09, 31.08, [("saya diberikan peluang", "berkhidmat", ""),
                          ("di", "Kuala Lumpur", "dan Putrajaya"),
                          ("Negeri Sembilan dan juga", "Melaka", "")]),   # (?) heard as "dia nilai 9"
    # --- commitment
    ("17", 72.93, 81.08, [("untuk saya", "mencurahkan", "segala khidmat"),
                          ("bagi saya", "berfokus", "di DUN Bukit Katil"),
                          ("berbanding sebelum ini", "seluruh", "Negeri Melaka")]),
    ("17", 81.57, 92.00, [("maka dengan itu", "saya memohon", ""),
                          ("seluruh", "pengundi", "di DUN Bukit Katil"),
                          ("memberikan saya", "peluang", ""),
                          ("berikan saya", "ruang", ""),
                          ("untuk saya", "menabur bakti", "")]),
    ("18", 27.43, 33.29, [("mungkin ada di antara kita", "ketinggalan", ""),
                          ("mungkin ada yang", "masih", "memerlukan")]),
    ("18", 70.60, 72.22, [("ini", "janji kita", "tuan-tuan")]),
    # --- climax
    ("16", 82.69, 93.58, [("dan", "Alhamdulillah", ""),
                          ("ia merupakan satu", "gelombang", "pertama"),
                          ("untuk kita lihat", "kemenangan", "sekali lagi"),
                          ("di DUN", "Bukit Katil", ""),
                          ("", "Takbir!", "")]),
    ("15", 109.57, 116.13, [("hari", "penentuan", ""),
                            ("", "14 November", "nanti"),
                            ("sama-sama kita", "memenangkan", "DUN Bukit Katil")]),
]
# closing name card plays over this (speech muted, music full)
CARD_SRC = ("15", 116.13, 120.63)
CARD = ("Calon N17 Bukit Katil", "RIDZUAN SARIF", "Melaka")
MUSIC_START = 0.4      # song offset where the intro chant starts
MUSIC_BED = 0.30       # music level under speech (before sidechain ducking)


def find_clips(folder):
    clips = {}
    for k in ("15", "16", "17", "18", "19"):
        hit = glob.glob(os.path.join(folder, f"*1028_{k}.mp4"))
        if not hit:
            sys.exit(f"missing clip *1028_{k}.mp4 in {folder}")
        clips[k] = hit[0]
    return clips


def cut(clips, tmp):
    parts = ([(INTRO_SRC[0], INTRO_SRC[1], INTRO_SRC[2], None)] + EDIT
             + [(CARD_SRC[0], CARD_SRC[1], CARD_SRC[2], None)])
    inputs, fc, labels = [], [], []
    for i, (k, a, b, _) in enumerate(parts):
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", clips[k]]
        d = b - a
        afade = (f"afade=t=in:d=0.03,afade=t=out:st={d - 0.04:.3f}:d=0.04" if _ is not None
                 else "volume=0")
        fc.append(f"[{i}:v]fps=30,scale=480:854,setsar=1,setpts=PTS-STARTPTS[v{i}]")
        fc.append(f"[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,{afade}[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    fc.append(f"{''.join(labels)}concat=n={len(parts)}:v=1:a=1[v][a]")
    out = os.path.join(tmp, "reel_cut.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fc),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "14", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "256k", out], check=True)
    return out


def script(tmp):
    lines = ["FOCUS 0.30 0.22"]
    t = INTRO_SRC[2] - INTRO_SRC[1]
    lines.append(f"CARD 0.10 {t:.2f} {INTRO[0]} | {INTRO[1]} | {INTRO[2]}")
    for idx, (_, a, b, groups) in enumerate(EDIT):
        d = b - a
        if idx % 2 == 1:
            lines.append(f"ZOOM {t:.2f} {t + d:.2f}")
        weights = [max(4, len(" ".join(g))) for g in groups]
        total = sum(weights)
        usable = d - 0.25
        cur = t + 0.15
        for g, w in zip(groups, weights):
            gd = usable * w / total
            end = cur + gd if g is not groups[-1] else t + d
            lines.append(f"{cur:.2f} {end:.2f} {g[0]} | {g[1]} | {g[2]}")
            cur += gd
        t += d
    cd = CARD_SRC[2] - CARD_SRC[1]
    lines.append(f"CARD {t:.2f} {t + cd:.2f} {CARD[0]} | {CARD[1]} | {CARD[2]}")
    path = os.path.join(tmp, "reel_script.txt")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path, INTRO_SRC[2] - INTRO_SRC[1], t, t + cd


def mix(video, song, out, intro_end, card_start, total):
    """Speech + ducked music bed + impact hits."""
    song_len = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", song]))
    xf = 0.6
    body = card_start + xf / 2
    tail = total - card_start + xf / 2
    tail_from = max(0.0, song_len - tail)
    clip = lambda x: f"max(0,min(1,{x}))"
    vol = (f"{MUSIC_BED}+{1 - MUSIC_BED}*max({clip(f'({intro_end}+0.2-t)/0.5')},"
           f"{clip(f'(t-{card_start}+0.2)/0.5')})")
    boom = ("aevalsrc=exprs='0.9*sin(2*PI*(38+70*exp(-9*t))*t)*exp(-3.2*t)':s=48000:d=1.8,"
            "aformat=channel_layouts=stereo")
    riser = ("anoisesrc=d=1.2:c=pink:a=0.35:r=48000,highpass=f=1500,"
             "afade=t=in:d=1.15:curve=exp,afade=t=out:st=1.15:d=0.05,aformat=channel_layouts=stereo")
    ms = lambda x: int(x * 1000)
    fc = [
        # speech: clean up rally audio, even out level
        "[0:a]highpass=f=90,lowpass=f=9000,acompressor=threshold=0.08:ratio=3:attack=10:release=200,"
        "dynaudnorm=f=200:g=11,volume=1.0,aformat=channel_layouts=stereo,asplit=2[sp][sc]",
        f"[1:a]atrim={MUSIC_START}:{MUSIC_START + body:.3f},asetpts=PTS-STARTPTS[m1]",
        f"[1:a]atrim={tail_from:.3f}:{tail_from + tail:.3f},asetpts=PTS-STARTPTS[m2]",
        f"[m1][m2]acrossfade=d={xf}:c1=tri:c2=tri,aresample=48000,aformat=channel_layouts=stereo,"
        f"volume='{vol}':eval=frame[mv]",
        "[mv][sc]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=450:makeup=1[mduck]",
        f"{boom},adelay={ms(intro_end)}|{ms(intro_end)}[b1]",
        f"{boom},adelay={ms(card_start)}|{ms(card_start)}[b2]",
        f"{riser},adelay={ms(max(0, card_start - 1.2))}|{ms(max(0, card_start - 1.2))}[r1]",
        f"{boom},volume=0.6[b0]",
        "[sp][mduck][b0][b1][b2][r1]amix=inputs=6:normalize=0:duration=first,"
        f"afade=t=out:st={total - 0.6:.3f}:d=0.6,alimiter=limit=0.89,"
        "loudnorm=I=-14:TP=-1.0:LRA=11[aout]",
    ]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", song, "-filter_complex", ";".join(fc),
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", "-movflags", "+faststart", out], check=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    folder, song, out = sys.argv[1:]
    tmp = os.path.dirname(os.path.abspath(out))
    cut_file = cut(find_clips(folder), tmp)
    scr, intro_end, card_start, total = script(tmp)
    voice_only = os.path.join(tmp, "reel_voice_only.mp4")
    subprocess.run([sys.executable, os.path.join(HERE, "kinetic.py"), scr, cut_file, voice_only], check=True)
    mix(voice_only, song, out, intro_end, card_start, total)
    print("wrote", out)
