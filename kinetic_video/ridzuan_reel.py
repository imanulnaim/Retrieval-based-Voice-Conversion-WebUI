#!/usr/bin/env python3
"""
Highlight reel: Ridzuan Sarif, calon N17 Bukit Katil (ceramah malam pertama kempen).

Cuts the strongest lines out of the four raw clips, writes a kinetic caption
script for them and renders it with kinetic.py.

Usage: python3 ridzuan_reel.py <folder with the raw clips> <output.mp4>
Raw clips expected (by suffix): *1028_15.mp4 *1028_16.mp4 *1028_17.mp4 *1028_18.mp4

Caption text is a corrected transcript. Review it against the audio before
posting; lines marked (?) were unclear in the recording.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# (clip, start, end, [(lead, KEY, tail), ...])   times are seconds in the raw clip
EDIT = [
    ("16", 31.11, 36.45, [("Pada malam ini", "malam pertama", ""),
                          ("kita", "berkempen", "")]),
    ("16", 36.45, 42.47, [("bagi", "pilihan raya", ""),
                          ("negeri", "Melaka", "tahun 2026")]),
    ("16", 82.69, 93.58, [("dan", "Alhamdulillah", ""),
                          ("ia merupakan satu", "gelombang", "pertama"),
                          ("untuk kita lihat", "kemenangan", "sekali lagi"),
                          ("di DUN", "Bukit Katil", ""),
                          ("", "Takbir!", "")]),
    ("17", 0.20, 2.58, [("hampir", "18 tahun", "")]),
    ("17", 12.97, 20.65, [("berbekalkan", "pengalaman", ""),
                          ("khususnya dalam", "perkhidmatan", ""),  # (?) heard as "hikmah ni"
                          ("", "awam", "ataupun kerajaan")]),
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
    ("18", 48.20, 50.51, [("kita akan", "pastikan", ""),
                          ("", "setiap", "satu rumah")]),
    ("18", 70.60, 72.22, [("ini", "janji kita", "tuan-tuan")]),
    ("15", 109.57, 116.13, [("hari", "penentuan", ""),
                            ("", "14 November", "nanti"),
                            ("sama-sama kita", "memenangkan", "DUN Bukit Katil")]),
]
# closing name card plays over this (audio fades out)
CARD_SRC = ("15", 116.13, 119.60)
CARD = ("Calon N17 Bukit Katil", "RIDZUAN SARIF", "Melaka")


def find_clips(folder):
    clips = {}
    for k in ("15", "16", "17", "18"):
        hit = glob.glob(os.path.join(folder, f"*1028_{k}.mp4"))
        if not hit:
            sys.exit(f"missing clip *1028_{k}.mp4 in {folder}")
        clips[k] = hit[0]
    return clips


def cut(clips, tmp):
    parts = EDIT + [(CARD_SRC[0], CARD_SRC[1], CARD_SRC[2], None)]
    inputs, fc, labels = [], [], []
    for i, (k, a, b, _) in enumerate(parts):
        inputs += ["-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", clips[k]]
        d = b - a
        afade = (f"afade=t=in:d=0.03,afade=t=out:st={d - 0.04:.3f}:d=0.04" if _ is not None
                 else f"afade=t=out:st=0:d={d:.3f}")
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
    t = 0.0
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
    return path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    folder, out = sys.argv[1:]
    tmp = os.path.dirname(os.path.abspath(out))
    cut_file = cut(find_clips(folder), tmp)
    scr = script(tmp)
    subprocess.run([sys.executable, os.path.join(HERE, "kinetic.py"), scr, cut_file, out], check=True)
