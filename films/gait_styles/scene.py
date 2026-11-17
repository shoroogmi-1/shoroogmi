"""عرض أنماط المشي (من كتاب Animation: The Mechanics of Motion): نفس الشخصية بأربع شخصيات مختلفة في المشية."""
import os
import sys
import math
import subprocess
import numpy as np
import cv2
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from engine import cutout as K  # noqa: E402
from engine import sfx  # noqa: E402
from scipy.io import wavfile  # noqa: E402

W, H, FPS, DUR = 1080, 1920, 30, 6.0
ROWS = [("confident", "واثق"), ("sad", "حزين"), ("old", "كبير في السن"), ("happy", "سعيد")]
RH = H // 4
SC = 0.36
OY = 292


def pose_svg(name, t):
    g = K.GAITS[name]
    phase = t / g["T"]
    gp = K.gait_pose(name, phase, 1.0)
    ground = 440.0
    hip = (300.0, ground - K.ANK - 432 + gp["bob"])
    feet = [(hip[0] + fx + (8 if k == 0 else -6), ground - lift, fa) for k, (fx, lift, fa, st) in enumerate(gp["feet"])]
    an, af = gp["arm_near"], gp["arm_far"]
    _, wn = K.fk2(K.SHOULDER, an[0], an[1], K.UA, K.FA)
    _, wf = K.fk2(K.SHOULDER, af[0], af[1], K.UA, K.FA)
    pose = K.Pose(hip=hip, lean=gp["lean"], head_tilt=gp["head"], feet=feet, breath=math.sin(t * 2),
                  arm_near=("ik", wn, -1, "torso"), arm_far=("ik", wf, -1, "torso"),
                  hair_bounce=gp["hair_bounce"], brow=-0.8 if name in ("sad", "old") else 0.4,
                  smile=1.0 if name == "happy" else 0.0)
    return K.draw_character(pose, "general" if name != "happy" else "reem")


def steps_of(name):
    g = K.GAITS[name]
    out = []
    prev = [True, True]
    for i in range(int(DUR * FPS)):
        t = i / FPS
        for k, off in enumerate((0.0, 0.5)):
            st = K.foot_rel(t / g["T"] + off, g, 1.0)[3]
            if st and not prev[k]:
                out.append(t)
            prev[k] = st
    return out


_F = {}


def frame(i):
    t = i / FPS
    if not _F:
        f = ImageFont.truetype(os.path.join(ROOT, "assets/fonts/arabic/Cairo-Variable.ttf"), 54, layout_engine=ImageFont.Layout.RAQM)
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
        _F["f"] = f
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    cols = [((246, 214, 160), (232, 190, 130)), ((150, 170, 200), (120, 140, 175)), ((205, 190, 170), (180, 165, 145)), ((255, 220, 150), (250, 190, 120))]
    for r, (name, label) in enumerate(ROWS):
        y0 = r * RH
        top, bot = cols[r]
        for y in range(RH):
            k = y / RH
            d.line([(0, y0 + y), (W, y0 + y)], fill=tuple(int(top[c] * (1 - k) + bot[c] * k) for c in range(3)))
        g = K.GAITS[name]
        speed = g["S"] / (g["stance"] * g["T"]) * SC     # الأرض تتحرك بنفس سرعة القدم الثابتة (لا انزلاق)
        gy = y0 + int(440 * SC) + OY
        d.rectangle([0, gy, W, y0 + RH], fill=(90, 80, 70))
        for x in np.arange(-200, W + 200, 160):
            xx = (x - t * speed) % (W + 160) - 80
            d.line([(xx, gy + 30), (xx + 60, gy + 30)], fill=(140, 125, 110), width=6)
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{RH}"><g transform="translate(300,{OY}) scale({SC})">{pose_svg(name, t)}</g></svg>'
        png = subprocess.run(["rsvg-convert"], input=svg.encode(), capture_output=True, check=True).stdout
        ch = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
        chi = Image.fromarray(ch[..., [2, 1, 0, 3]])
        img.paste(chi, (0, y0), chi)
        d.text((W - 60, y0 + 80), label, font=_F["f"], fill=(255, 255, 255), anchor="ra", direction="rtl", language="ar",
               stroke_width=6, stroke_fill=(30, 20, 15))
        d.line([(0, y0), (W, y0)], fill=(30, 20, 15), width=6)
    return np.asarray(img)


def main():
    N = int(DUR * FPS)
    vid = "/tmp/gait.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    with Pool(2) as pool:
        for fr in pool.imap(frame, range(N), chunksize=4):
            ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    SR = sfx.SR
    mix = np.zeros((int(DUR * SR), 2), np.float32)
    pans = [-0.6, -0.2, 0.2, 0.6]
    vols = {"confident": 0.5, "sad": 0.25, "old": 0.22, "happy": 0.45}
    for r, (name, _) in enumerate(ROWS):
        for k, st in enumerate(steps_of(name)):
            x = sfx.step(1.0, "stone", False, seed=r * 100 + k)
            s = int(st * SR)
            e = min(len(mix), s + len(x))
            g = np.array([math.sqrt((1 - pans[r]) / 2), math.sqrt((1 + pans[r]) / 2)], np.float32)
            mix[s:e] += x[: e - s] * vols[name] * g
    wavfile.write("/tmp/gait.wav", SR, (np.tanh(mix * 1.5) * 0.9 * 32767).astype(np.int16))
    out = os.path.join(ROOT, ".cache", "gait_styles.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", "/tmp/gait.wav", "-c:v", "copy", "-c:a", "aac", "-shortest", out], check=True)
    print(out)


if __name__ == "__main__":
    if sys.argv[1:2] == ["x"]:
        Image.fromarray(frame(int(float(sys.argv[2]) * FPS))).resize((540, 960)).save("/tmp/gs.png")
        print("/tmp/gs.png")
    else:
        main()
