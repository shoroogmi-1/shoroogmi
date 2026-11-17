"""مختبر الحركة: تطبيق فصول كتاب Mechanics of Motion — الكتلة والارتداد، الطيران، وذوات الأربع."""
import os
import sys
import math
import subprocess
import numpy as np
import cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from engine import motion as M  # noqa: E402
from engine import cutout as K  # noqa: E402
from engine import sfx  # noqa: E402

W, H, FPS, DUR = 1080, 1920, 60, 7.0
SS = 2   # رسم بدقة مضاعفة ثم تصغير (حواف ناعمة)
LINE = (43, 28, 23)
ROW = H // 3
BALLS = [("tennis", "كرة تنس", (215, 230, 60), 34, 230), ("cannon", "قذيفة مدفع", (60, 62, 70), 40, 540),
         ("balloon", "بالون", (230, 70, 90), 52, 850)]
_F = {}


def font(sz):
    f = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/arabic/Cairo-Variable.ttf"), sz, layout_engine=ImageFont.Layout.RAQM)
    try:
        f.set_variation_by_name("Bold")
    except Exception:
        pass
    return f


def S(v):
    return v * SS


def ell(d, cx, cy, rx, ry, fill, ang=0, outline=LINE, w=5):
    """قطع ناقص مدوّر (للضغط والمط) — مضلع."""
    pts = []
    a = math.radians(ang)
    for k in range(40):
        t = k / 40 * 2 * math.pi
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((S(cx + x * math.cos(a) - y * math.sin(a)), S(cy + x * math.sin(a) + y * math.cos(a))))
    d.polygon(pts, fill=fill, outline=outline, width=S(w))


def seg(d, a, b, w, col):
    d.line([S(a[0]), S(a[1]), S(b[0]), S(b[1])], fill=LINE, width=S(w + 6))
    for p in (a, b):
        r = (w + 6) / 2
        d.ellipse([S(p[0] - r), S(p[1] - r), S(p[0] + r), S(p[1] + r)], fill=LINE)
    d.line([S(a[0]), S(a[1]), S(b[0]), S(b[1])], fill=col, width=S(w))
    for p in (a, b):
        r = w / 2
        d.ellipse([S(p[0] - r), S(p[1] - r), S(p[0] + r), S(p[1] + r)], fill=col)


# ------------------------------------------------------------- الصف 1: الكتلة والارتداد
def row_balls(d, t):
    y0, ground = 0, ROW - 70
    for name, label, col, r, x0 in BALLS:
        tt = (t - 0.4) % 5.0
        x, y, vx, vy, since, iv = M.bounce(max(tt, 0), x0 - 120, 120, 90, ground - r, name)
        sx, sy, ang = M.squash_stretch(vx, vy, since, iv, name)
        h = (ground - r - y) / (ground - 120)
        sh = 1 - 0.6 * h                                               # ظل ساقط: يكبر ويغمق كلما اقترب الجسم من الأرض
        ell(d, x, ground + 4, r * 1.1 * sh, 9 * sh, (0, 0, 0, int(90 * sh)), outline=None)
        if since < 0.06:
            ell(d, x, y + r * (1 - sy) + 0, r * sx, r * sy, col)
        else:
            ell(d, x, y, r * sx, r * sy, col, ang)
        d.ellipse([S(x - r * 0.45), S(y - r * 0.55), S(x - r * 0.1), S(y - r * 0.25)], fill=(255, 255, 255, 140))   # إضاءة (highlight)
        d.text((S(x0 - 60), S(ground + 22)), label, font=_F["s"], fill=(255, 255, 255), anchor="mt", direction="rtl", language="ar",
               stroke_width=S(4), stroke_fill=LINE)


# ------------------------------------------------------------- الصف 2: الطائر
def row_bird(d, t):
    y0 = ROW
    T = 0.42
    ph = t / T
    sh, fold, tip, body = M.wing_cycle(ph)
    cx = (t * 170) % (W + 300) - 150
    cy = y0 + ROW * 0.5 + body + 14 * math.sin(t * 1.3)
    span = 150

    def wing(sign, col):
        a = math.radians(-sh * sign * 0 - sh)
        L1 = span * 0.5 * (1 - 0.35 * fold)
        L2 = span * 0.55 * (1 - 0.55 * fold)
        p0 = (cx - 6, cy - 6)
        p1 = (p0[0] - L1 * 0.25 - 10 * fold, p0[1] - L1 * math.sin(math.radians(sh)))
        a2 = math.radians(sh + tip)
        p2 = (p1[0] - L2 * 0.35 - 18 * fold, p1[1] - L2 * math.sin(a2))
        d.polygon([S(p0[0] + 18), S(p0[1]), S(p1[0] + 12), S(p1[1]), S(p2[0]), S(p2[1]), S(p1[0] - 30), S(p1[1] + 10),
                   S(p0[0] - 28), S(p0[1] + 6)], fill=col, outline=LINE, width=S(4))
    wing(1, (150, 150, 165))                                          # الجناح البعيد (أغمق)
    ell(d, cx, cy, 58, 26, (205, 205, 215))
    ell(d, cx + 52, cy - 18, 20, 18, (205, 205, 215))
    d.polygon([S(cx + 70), S(cy - 22), S(cx + 92), S(cy - 15), S(cx + 70), S(cy - 10)], fill=(240, 170, 60), outline=LINE, width=S(3))
    d.ellipse([S(cx + 55), S(cy - 26), S(cx + 63), S(cy - 18)], fill=LINE)
    d.polygon([S(cx - 55), S(cy - 6), S(cx - 98), S(cy - 18 + 6 * math.sin(ph * 6.28)), S(cx - 96), S(cy + 8), S(cx - 52), S(cy + 8)],
              fill=(175, 175, 190), outline=LINE, width=S(4))
    wing(1, (230, 230, 238))                                          # الجناح القريب
    d.text((S(W - 50), S(y0 + 40)), "طيران: دفع للأسفل، طيّ للأعلى، وسحب الأطراف", font=_F["s"], fill=(255, 255, 255), anchor="ra",
           direction="rtl", language="ar", stroke_width=S(4), stroke_fill=LINE)


# ------------------------------------------------------------- الصف 3: حصان يهرول (أشكال أساسية)
def row_horse(d, t):
    y0 = 2 * ROW
    ground = y0 + ROW - 80
    g = M.QUAD["trot"]
    ph = t / g["T"]
    q = M.quad_gait("trot", ph, stride=0.9)
    hl = 70                    # طول الرأس — وحدة القياس (الكتف ≈ 2.5 رأس)
    Lu, Ll = hl * 0.85, hl * 0.85
    cx = 470
    body_y = ground - hl * 2.5 + hl * 0.9 + q["body_y"] * hl * 3
    pitch = math.radians(q["pitch"] * 0.5)
    sh = (cx + hl * 1.1, body_y - hl * 0.2)
    hp = (cx - hl * 1.1, body_y - hl * 0.15)
    sh = (sh[0], sh[1] + math.sin(pitch) * hl)
    hp = (hp[0], hp[1] - math.sin(pitch) * hl)
    # [أمامي أيسر، أمامي أيمن، خلفي أيسر، خلفي أيمن] — البعيد (الأيسر) أولًا وأغمق
    coats = [(120, 80, 50), (160, 105, 65)]
    order = [(0, sh, 1, 0), (2, hp, -1, 0), (1, sh, 1, 1), (3, hp, -1, 1)]
    for idx, anchor, bend, near in order[:2]:
        leg(d, q["legs"][idx], anchor, ground, Lu, Ll, bend, coats[near], hl)
    # الجسم والرقبة والرأس (حركة ثانوية متأخرة)
    tail_sw = 14 * math.sin(2 * math.pi * (ph - 0.25))                 # الذيل: متابعة (follow-through)
    d.line([S(hp[0] - 20), S(hp[1] - 20), S(hp[0] - 70), S(hp[1] + 30 + tail_sw), S(hp[0] - 60), S(hp[1] + 90 + tail_sw * 1.6)],
           fill=(60, 35, 20), width=S(16), joint="curve")
    ell(d, cx, body_y, hl * 1.55, hl * 0.62, coats[1], math.degrees(pitch) * 0.5)
    nb = (sh[0] + 10, sh[1] - 10)
    hd = (nb[0] + hl * 0.9, nb[1] - hl * 1.0 + q["head"] * 0.8)
    seg(d, nb, hd, int(hl * 0.55), coats[1])
    ell(d, hd[0] + hl * 0.35, hd[1] + hl * 0.12, hl * 0.55, hl * 0.26, coats[1], 30)
    d.ellipse([S(hd[0] + 8), S(hd[1] - 4), S(hd[0] + 18), S(hd[1] + 6)], fill=LINE)
    d.polygon([S(hd[0] - 10), S(hd[1] - 20), S(hd[0] - 4), S(hd[1] - 46), S(hd[0] + 6), S(hd[1] - 20)], fill=coats[1], outline=LINE, width=S(3))
    d.line([S(nb[0] - 10), S(nb[1] - 6), S(hd[0] - 14), S(hd[1] - 16)], fill=(60, 35, 20), width=S(12))   # العرف
    for idx, anchor, bend, near in order[2:]:
        leg(d, q["legs"][idx], anchor, ground, Lu, Ll, bend, coats[near], hl)
    d.text((S(W - 50), S(y0 + 30)), "هرولة: الأرجل قطرية، ضربتان وتعليق", font=_F["s"], fill=(255, 255, 255), anchor="ra",
           direction="rtl", language="ar", stroke_width=S(4), stroke_fill=LINE)


def leg(d, lg, anchor, ground, Lu, Ll, bend, col, hl):
    fx, lift, down = lg
    foot = (anchor[0] + fx * hl * 1.6, ground - lift * hl * 1.6 - 8)
    knee = K.ik2(anchor, foot, Lu, Ll, bend=bend)                    # الركبة الأمامية للأمام، العرقوب الخلفي للخلف
    seg(d, anchor, knee, 26, col)
    seg(d, knee, foot, 18, col)
    d.rectangle([S(foot[0] - 11), S(foot[1] - 4), S(foot[0] + 13), S(foot[1] + 10)], fill=(40, 30, 25))


def frame(i):
    if not _F:
        _F["s"] = font(S(36))
        bg = Image.new("RGB", (S(W), S(H)))
        bd = ImageDraw.Draw(bg)
        cols = [((150, 190, 225), (225, 220, 190)), ((120, 160, 210), (200, 215, 235)), ((240, 200, 140), (210, 165, 110))]
        for r, (a, b) in enumerate(cols):
            for y in range(S(ROW)):
                k = y / S(ROW)
                bd.line([(0, S(r * ROW) + y), (S(W), S(r * ROW) + y)], fill=tuple(int(a[c] * (1 - k) + b[c] * k) for c in range(3)))
        bd.rectangle([0, S(ROW - 70), S(W), S(ROW)], fill=(120, 150, 80))
        bd.rectangle([0, S(3 * ROW - 80), S(W), S(3 * ROW)], fill=(150, 120, 80))
        for r in (1, 2):
            bd.line([0, S(r * ROW), S(W), S(r * ROW)], fill=LINE, width=S(6))
        _F["bg"] = bg
    t = i / FPS
    img = _F["bg"].copy()
    d = ImageDraw.Draw(img, "RGBA")
    # أرضية الحصان تتحرك (منظور ثابت للكاميرا مع الحصان)
    for x in range(-200, W + 200, 140):
        xx = (x - t * 330) % (W + 140) - 70
        d.line([S(xx), S(3 * ROW - 40), S(xx + 50), S(3 * ROW - 40)], fill=(120, 95, 65), width=S(6))
    row_balls(d, t)
    row_bird(d, t)
    row_horse(d, t)
    out = img.resize((W, H), Image.LANCZOS)
    return np.asarray(out)


def audio(out):
    SR = sfx.SR
    n = int(DUR * SR)
    mix = np.zeros((n, 2), np.float32)

    def put(x, t, g):
        s = int(t * SR)
        e = min(n, s + len(x))
        if 0 <= s < n:
            mix[s:e] += x[: e - s] * g
    for name, *_r in BALLS:                                            # أصوات الاصطدام حسب الكتلة
        prev = 0
        for k in range(int(5.0 * 240)):
            tt = k / 240
            _, _, _, _, since, iv = M.bounce(tt, 0, 120, 90, 1000, name)
            if since == 0.0 and iv > 120 and tt - prev > 0.05:
                prev = tt
                g = min(1.0, iv / 1500)
                if name == "cannon":
                    x = sfx.impact(0.8)
                elif name == "balloon":
                    x = sfx.step(0.6, "grass", False, seed=k)
                else:
                    x = sfx.step(0.9, "stone", True, seed=k)
                put(x, tt + 0.4, 0.5 * g)
    T = M.QUAD["trot"]["T"]
    for k in range(int(DUR / T * 2) + 1):                              # الهرولة: ضربتان لكل دورة
        put(sfx.step(1.0, "wood", True, seed=500 + k), k * T / 2 + 0.02, 0.35)
    for k in range(int(DUR / 0.42)):
        put(sfx.whoosh(0.25), k * 0.42, 0.06)
    mix = np.tanh(mix * 1.2) * 0.9
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))


def main():
    if sys.argv[1:2] == ["x"]:
        Image.fromarray(frame(int(float(sys.argv[2]) * FPS))).resize((540, 960)).save("/tmp/ml.png")
        print("/tmp/ml.png")
        return
    N = int(DUR * FPS)
    vid, wav = "/tmp/ml.mp4", "/tmp/ml.wav"
    audio(wav)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for fr in pool.imap(frame, range(N), chunksize=6):
            ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    out = os.path.join(ROOT, ".cache", "motion_lab.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-shortest", out], check=True)
    print(out)


if __name__ == "__main__":
    main()
