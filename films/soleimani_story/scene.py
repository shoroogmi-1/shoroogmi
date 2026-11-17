"""مقتل قاسم سليماني (نسخة السيناريو المبني على Writing for Animation) — فيديو قصير بأسلوب الرسوم المقصوصة (عمودي 1080×1920).

python3 films/soleimani/scene.py              # إخراج كامل
python3 films/soleimani/scene.py x 1.5 5 8.6 10.6   # لوحة فحص

اللقطات (متزامنة مع صوت الراوي كريم):
 A 0.0–3.6   مطار بغداد ليلًا (منظور خطي لأضواء المدرج، منظور جوي للمدينة)        «بغداد، الثالث من يناير ٢٠٢٠»
 B 3.6–6.9   سليماني يمشي نحو السيارة (مشية IK، ظل ساقط، بطاقة اسم)                «موكب قاسم سليماني يغادر المطار»
 C 6.9–9.3   المسيّرة في السماء ← منظار حراري يتتبع الموكب                         «في السماء… مسيّرة أمريكية»
 D 9.3–10.4  الصاروخ يهبط على الموكب ← وميض وانفجار واهتزاز                        «صاروخ!»
 E 10.4–12.9 ما بعد الضربة: نار ودخان وبطاقة الختام                                «مقتل قاسم سليماني»
"""
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
from engine import cutout as K  # noqa: E402
from engine import sfx  # noqa: E402
from engine import vehicles as V  # noqa: E402

W, H, FPS = 1080, 1920, 60   # 60 إطارًا/ث لحركة أنعم
DUR = 19.7
IMPACT = 14.85
CACHE = os.path.join(ROOT, ".cache", "soleimani_story")
PLATES = os.path.join(ROOT, ".cache", "soleimani")
os.makedirs(CACHE, exist_ok=True)
LINE = "#2b1c17"
# الفصل الأول: الوصول (A الطائرة تهبط + زرع المسيّرة أمام القمر، B النزول إلى الموكب)
# الفصل الثاني: الرصد يشتد (C1 كشف المسيّرة = حصاد الزرع، C2 المنظار يثبّت الهدف)
# الفصل الثالث: الضربة والخاتمة (D الصاروخ، E «بعد دقائق من هبوطه» = حصاد مشهد الهبوط)
CUTS = [4.75, 9.4, 11.0, 13.55, 15.0]
NARR = [(0.3, 0), (4.9, 1), (9.5, 2), (13.65, 4), (15.35, 5)]
SUBS = [(0.3, 4.55, "بغداد، فجر الثالث من يناير ٢٠٢٠"), (4.9, 9.27, "قاسم سليماني ينزل من الطائرة إلى موكبه"),
        (9.5, 13.45, "لكن في السماء… مسيّرة أمريكية تراقب"), (13.65, 14.75, "ثمّ… صاروخ!"),
        (15.35, 19.35, "قُتل قاسم سليماني بعد دقائق من هبوطه")]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def back_out(t):
    t = clamp(t)
    c = 2.2
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def svg_png(svg, w=W, h=H):
    png = subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h)], input=svg.encode(), capture_output=True, check=True).stdout
    im = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
    if im.shape[2] == 3:
        im = np.concatenate([im, np.ones(im.shape[:2] + (1,), np.float32)], 2)
    return im[..., [2, 1, 0, 3]]


def wrap(body, w=W, h=H):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'


def cached_plate(name, body_fn, blur_far=None):
    p = os.path.join(PLATES, name + ".npy")
    if os.path.exists(p):
        return np.load(p)
    im = svg_png(wrap(body_fn()))
    np.save(p, im)
    return im


def over(dst, rgba, op=1.0):
    a = rgba[..., 3:4] * op
    return dst * (1 - a) + rgba[..., :3] * a


def add_glow(img, x, y, r, col, strength):
    g = np.zeros((H // 4, W // 4), np.float32)
    cv2.circle(g, (int(x / 4), int(y / 4)), max(1, int(r / 4)), 1.0, -1)
    g = cv2.GaussianBlur(g, (0, 0), max(1, r / 10))
    g = cv2.resize(g, (W, H))[..., None]
    return img + g * np.array(col, np.float32) * strength


def push(img, t0, t1, t, z0=1.0, z1=1.1, cx=0.5, cy=0.5, dx=0.0, shake=0.0):
    k = ease((t - t0) / (t1 - t0))
    z = z0 + (z1 - z0) * k
    sx = shake * 14 * (math.sin(t * 91) + 0.6 * math.sin(t * 57)) if shake else 0
    sy = shake * 12 * (math.cos(t * 83) + 0.6 * math.sin(t * 41)) if shake else 0
    M = np.float32([[z, 0, W * cx * (1 - z) + dx * k + sx], [0, z, H * cy * (1 - z) + sy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ======================================================================= عناصر مرسومة
def stars(r, n, y1):
    return "".join(f'<circle cx="{r.uniform(0, W):.0f}" cy="{r.uniform(0, y1):.0f}" r="{r.uniform(0.8, 2.4):.1f}" fill="#fff" opacity="{r.uniform(0.3, 0.9):.2f}"/>' for _ in range(n))


def night_sky(top="#070b22", mid="#16224a", hor="#3a3a62", glow="#b8663a", horizon=1150):
    return (f'<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="{horizon / H * 0.6:.3f}" stop-color="{mid}"/><stop offset="{horizon / H:.3f}" stop-color="{hor}"/>'
            f'<stop offset="1" stop-color="{hor}"/></linearGradient>'
            f'<radialGradient id="cg" cx="0.5" cy="1" r="0.8"><stop offset="0" stop-color="{glow}" stop-opacity="0.55"/>'
            f'<stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="mg"><stop offset="0" stop-color="#eef2ff" stop-opacity="0.9"/><stop offset="0.15" stop-color="#cdd8ff" stop-opacity="0.35"/>'
            f'<stop offset="1" stop-color="#8aa0ff" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#sk)"/><rect x="-200" y="{horizon - 420}" width="{W + 400}" height="520" fill="url(#cg)"/>')


def moon(x, y, r=46):
    return (f'<circle cx="{x}" cy="{y}" r="{r * 7}" fill="url(#mg)"/><circle cx="{x}" cy="{y}" r="{r}" fill="#f1f3ff"/>'
            f'<circle cx="{x + r * 0.3}" cy="{y - r * 0.2}" r="{r * 0.22}" fill="#d9ddf0"/><circle cx="{x - r * 0.35}" cy="{y + r * 0.3}" r="{r * 0.15}" fill="#d9ddf0"/>')


def city(r, y, n, col, win_col, scale=1.0, win=True):
    s = ""
    x = -40
    while x < W + 40:
        bw, bh = r.uniform(50, 130) * scale, r.uniform(60, 240) * scale
        s += f'<rect x="{x:.0f}" y="{y - bh:.0f}" width="{bw:.0f}" height="{bh + 300:.0f}" fill="{col}"/>'
        if r.random() < 0.18:   # قبة أو مئذنة (بغداد)
            s += f'<ellipse cx="{x + bw / 2:.0f}" cy="{y - bh:.0f}" rx="{bw * 0.35:.0f}" ry="{bw * 0.4:.0f}" fill="{col}"/>'
        if win:
            for _ in range(int(bw * bh / 1800)):
                if r.random() < 0.5:
                    s += f'<rect x="{x + r.uniform(4, bw - 8):.0f}" y="{y - bh + r.uniform(6, bh - 8):.0f}" width="{4 * scale:.0f}" height="{6 * scale:.0f}" fill="{win_col}" opacity="{r.uniform(0.4, 0.95):.2f}"/>'
        x += bw + r.uniform(-8, 20)
    return s


def tower(x, base, s=1.0):
    """برج مراقبة (ظلّ) بقمة متسعة."""
    return (f'<path d="M{x - 26 * s},{base} L{x - 16 * s},{base - 420 * s} L{x + 16 * s},{base - 420 * s} L{x + 26 * s},{base} Z" fill="#1a1d33" stroke="{LINE}" stroke-width="3"/>'
            f'<path d="M{x - 70 * s},{base - 470 * s} L{x + 70 * s},{base - 470 * s} L{x + 46 * s},{base - 415 * s} L{x - 46 * s},{base - 415 * s} Z" fill="#20253f" stroke="{LINE}" stroke-width="3"/>'
            f'<rect x="{x - 60 * s}" y="{base - 462 * s}" width="{120 * s}" height="{30 * s}" fill="#ffd98a" opacity="0.85"/>'
            f'<rect x="{x - 40 * s}" y="{base - 500 * s}" width="{80 * s}" height="{30 * s}" fill="#1a1d33"/>'
            f'<line x1="{x}" y1="{base - 500 * s}" x2="{x}" y2="{base - 560 * s}" stroke="#1a1d33" stroke-width="5"/>')


def terminal(y, col="#252a45"):
    s = f'<path d="M-20,{y} L-20,{y - 120} C200,{y - 170} 600,{y - 170} 1100,{y - 130} L1100,{y} Z" fill="{col}" stroke="{LINE}" stroke-width="3"/>'
    for i in range(26):
        s += f'<rect x="{10 + i * 42}" y="{y - 90}" width="26" height="36" fill="#ffd78a" opacity="{0.55 + 0.4 * ((i * 7) % 3) / 2:.2f}"/>'
    return s


def suv(x, y, s=1.0, wheel=0.0, body="#121419", hi="#3a4250", tail=True, head=True, flip=False):
    """سيارة دفع رباعي جانبية متجهة لليمين (x,y = منتصف أسفل العجلات)."""
    g = f'<g transform="translate({x:.1f},{y:.1f}) scale({-s if flip else s},{s})">'
    g += (f'<path d="M-250,-40 L-250,-150 C-246,-170 -230,-178 -200,-180 L-120,-182 L-80,-262 C-74,-272 -64,-276 -50,-276 L120,-276 '
          f'C140,-276 150,-270 160,-256 L210,-186 L250,-170 C266,-164 272,-150 272,-130 L272,-40 Z" fill="{body}" stroke="{LINE}" stroke-width="6" stroke-linejoin="round"/>')
    g += f'<path d="M-66,-252 L-104,-186 L20,-186 L20,-252 Z" fill="#1d2a40"/><path d="M34,-252 L34,-186 L190,-186 L146,-252 Z" fill="#1d2a40"/>'
    g += f'<path d="M-60,-248 L-80,-214" stroke="#5a6a88" stroke-width="6" opacity="0.6"/><path d="M60,-248 L50,-214" stroke="#5a6a88" stroke-width="6" opacity="0.6"/>'
    g += f'<path d="M-240,-150 L262,-150" stroke="{hi}" stroke-width="5" opacity="0.8"/>'   # خط إضاءة على الهيكل
    g += f'<path d="M-250,-70 L272,-70" stroke="#08090b" stroke-width="10"/>'
    if tail:
        g += '<rect x="-256" y="-150" width="16" height="40" rx="4" fill="#ff2a2a"/>'
    if head:
        g += '<rect x="258" y="-150" width="18" height="30" rx="4" fill="#fff6d0"/>'
    for wx in (-150, 170):
        g += (f'<circle cx="{wx}" cy="-40" r="58" fill="#0a0a0c" stroke="{LINE}" stroke-width="5"/>'
              f'<circle cx="{wx}" cy="-40" r="30" fill="#5d6470"/>')
        for k in range(5):
            a = wheel + k * 2 * math.pi / 5
            g += f'<line x1="{wx}" y1="-40" x2="{wx + 26 * math.cos(a):.1f}" y2="{-40 + 26 * math.sin(a):.1f}" stroke="#2a2d33" stroke-width="6"/>'
    return g + "</g>"


def reaper(x, y, s=1.0, rot_=0.0):
    """مسيّرة MQ-9 (ظل جانبي سفلي): جسم طويل، أجنحة رفيعة، ذيل V، مروحة خلفية."""
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot_:.1f}) scale({s})">'
            f'<path d="M-260,0 C-250,-24 -150,-30 120,-24 C190,-22 230,-12 240,0 C230,12 180,16 120,16 L-200,14 C-240,12 -258,8 -260,0 Z" fill="#3a4050" stroke="#0a0c12" stroke-width="5"/>'
            f'<path d="M-40,-6 L-10,-6 L60,-330 L30,-330 Z" fill="#2c313d" stroke="#0a0c12" stroke-width="4"/>'
            f'<path d="M-40,6 L-10,6 L40,240 L10,240 Z" fill="#232731" stroke="#0a0c12" stroke-width="4"/>'
            f'<path d="M-220,-4 L-270,-80 L-250,-80 L-200,-6 Z" fill="#2c313d" stroke="#0a0c12" stroke-width="4"/>'
            f'<path d="M-220,6 L-270,70 L-250,70 L-200,8 Z" fill="#2c313d" stroke="#0a0c12" stroke-width="4"/>'
            f'<ellipse cx="-268" cy="0" rx="8" ry="46" fill="#596070" opacity="0.6"/>'
            f'<path d="M150,-20 C180,-34 210,-28 226,-10" fill="none" stroke="#7a86a0" stroke-width="4"/>'      # إضاءة القمر على المقدمة
            f'<rect x="-60" y="14" width="60" height="10" rx="4" fill="#1a1d24"/>'
            f'</g>')


def a320(x, y, ppm, rot_=0.0):
    """إيرباص A320 جانبية متجهة لليمين (طول 37.6م، قطر الجسم ≈4م، الذيل ≈ 7.5م فوق المحور). x,y = مركز الجسم."""
    def P(u, v):
        return f"{(u - 18.8) * ppm:.1f},{-v * ppm:.1f}"
    fus = ("M" + P(0, 1.2) + " L" + P(3.5, 2.0) + " L" + P(33.5, 2.0) + " C" + P(36.2, 1.9) + " " + P(37.6, 0.6) + " " + P(37.6, -0.2) +
           " C" + P(37.2, -1.4) + " " + P(35.5, -2.0) + " " + P(33.0, -2.0) + " L" + P(8.0, -2.0) + " L" + P(0, 0.4) + " Z")
    fin = "M" + P(1.0, 1.4) + " L" + P(-0.6, 7.6) + " L" + P(2.6, 7.6) + " L" + P(7.5, 2.0) + " Z"
    stab = "M" + P(1.0, 0.6) + " L" + P(-0.4, 0.4) + " L" + P(4.5, 0.2) + " Z"
    wing = "M" + P(13.5, -1.0) + " L" + P(23.0, -0.9) + " L" + P(19.0, -1.6) + " L" + P(12.0, -1.7) + " Z"
    eng = "M" + P(15.0, -2.2) + " L" + P(19.5, -2.2) + " C" + P(20.2, -2.4) + " " + P(20.2, -3.8) + " " + P(19.5, -4.0) + " L" + P(15.5, -3.9) + " Z"
    win = "".join(f'<circle cx="{(u - 18.8) * ppm:.1f}" cy="{-0.8 * ppm:.1f}" r="{0.22 * ppm:.1f}" fill="#ffe2a0"/>' for u in np.arange(6.0, 33.0, 0.9))
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot_:.1f})">'
            f'<path d="{fin}" fill="#3a405a" stroke="{LINE}" stroke-width="2.5"/>'
            f'<path d="{fus}" fill="#4a5170" stroke="{LINE}" stroke-width="2.5"/>'
            f'<path d="M{(3.5 - 18.8) * ppm:.1f},{-1.6 * ppm:.1f} L{(34 - 18.8) * ppm:.1f},{-1.6 * ppm:.1f}" stroke="#8c94b8" stroke-width="2" opacity="0.6"/>'
            f'{win}<path d="{wing}" fill="#2c3149" stroke="{LINE}" stroke-width="2.5"/><path d="{eng}" fill="#262a3e" stroke="{LINE}" stroke-width="2.5"/>'
            f'<path d="{stab}" fill="#2c3149" stroke="{LINE}" stroke-width="2"/></g>')


# ======================================================================= اللوحات الثابتة
def plate_A():
    r = np.random.default_rng(1)
    b = night_sky()
    b += stars(r, 160, 900)
    b += moon(230, 330)
    b += f'<g opacity="0.65">{city(r, 1150, 40, "#2a2c4a", "#e8b46a", 0.8)}</g>'               # منظور جوي: البعيد باهت
    b += tower(780, 1180, 1.0)
    b += terminal(1180)
    # المدرج: منظور خطي — خطوط تتجه لنقطة تلاشي واحدة
    vp = (540, 1190)
    b += f'<path d="M0,1190 L{W},1190 L{W},{H} L0,{H} Z" fill="#14172a"/>'
    b += f'<path d="M{vp[0] - 30},1190 L{vp[0] + 30},1190 L{W + 400},{H} L{-400},{H} Z" fill="#1d2138"/>'
    for i in range(1, 16):
        k = (i / 15) ** 2.2
        y = 1190 + (H - 1190) * k
        for side in (-1, 1):
            xx = vp[0] + side * (30 + (W / 2 + 370) * k)
            b += f'<circle cx="{xx:.0f}" cy="{y:.0f}" r="{2 + 9 * k:.1f}" fill="#ffd27a"/>'
        b += f'<rect x="{vp[0] - 3 - 10 * k:.0f}" y="{y:.0f}" width="{6 + 20 * k:.0f}" height="{6 + 60 * k:.0f}" fill="#d9dbe8" opacity="0.7"/>'
    return b


def plate_B_far():
    r = np.random.default_rng(2)
    b = night_sky(horizon=1100)
    b += stars(r, 90, 700)
    b += f'<g opacity="0.55">{city(r, 1100, 30, "#262946", "#e8b46a", 0.6)}</g>'
    return b


def plate_B_near():
    b = terminal(1260, "#2a2f4c")
    b += f'<rect x="0" y="1260" width="{W}" height="{H - 1260}" fill="#1b1e30"/>'
    b += f'<rect x="0" y="1560" width="{W}" height="{H - 1560}" fill="#232740"/>'
    for i in range(8):      # علامات أرضية
        b += f'<rect x="{-60 + i * 170}" y="1700" width="110" height="14" fill="#d8c86a" opacity="0.55" transform="skewX(-25)"/>'
    b += (f'<rect x="900" y="980" width="16" height="290" fill="#11131e"/><path d="M860,960 L960,960 L940,990 L880,990 Z" fill="#2a2f45" stroke="{LINE}" stroke-width="3"/>')
    return b


def tile3(im):
    """يمدّ اللوحة أفقيًا بثلاث نسخ متناظرة (بلا فواصل ظاهرة) للتحريك الأفقي."""
    return np.concatenate([im, im[:, ::-1], im], 1)


def plate_C1():
    r = np.random.default_rng(3)
    b = night_sky(top="#04071a", mid="#0e1838", hor="#1e2a52", horizon=1900)
    b += stars(r, 260, 1900)
    b += moon(760, 620, 60)
    for k in range(6):       # غيوم ليلية مضاءة بالقمر من الأعلى
        cx, cy = r.uniform(0, W), r.uniform(900, 1700)
        for _ in range(6):
            b += f'<circle cx="{cx + r.uniform(-140, 140):.0f}" cy="{cy + r.uniform(-30, 30):.0f}" r="{r.uniform(50, 110):.0f}" fill="#24304f" opacity="0.8"/>'
        b += f'<path d="M{cx - 150:.0f},{cy - 60:.0f} C{cx - 40:.0f},{cy - 110:.0f} {cx + 60:.0f},{cy - 110:.0f} {cx + 160:.0f},{cy - 60:.0f}" fill="none" stroke="#6a7cb0" stroke-width="6" opacity="0.5"/>'
    return b


def plate_D():
    r = np.random.default_rng(4)
    b = night_sky(horizon=1180)
    b += stars(r, 120, 1000)
    b += moon(860, 300, 38)
    b += f'<g opacity="0.6">{city(r, 1190, 30, "#272a48", "#e8b46a", 0.7)}</g>'
    b += f'<rect x="0" y="1190" width="{W}" height="{H}" fill="#151828"/>'
    b += f'<path d="M0,1480 L{W},1480 L{W},1720 L0,1720 Z" fill="#202436"/>'
    for i in range(10):
        b += f'<rect x="{i * 130 - 20}" y="1596" width="70" height="8" fill="#c9c27a" opacity="0.5"/>'
    for x in range(40, W, 200):   # سياج المطار
        b += f'<rect x="{x}" y="1330" width="8" height="150" fill="#2b2f45"/>'
    b += f'<path d="M0,1350 L{W},1350 M0,1400 L{W},1400" stroke="#2b2f45" stroke-width="4"/>'
    return b


# ======================================================================= الشخصية (اللقطة B)
GAIT_B = "confident"
CAR_X = 2250.0   # طرف الأفالون الخلفي (عالمي)


def gait_B():
    """مشية واثقة متواصلة (بلا توقف ينزلق فيه القدمان)، بتدحرج القدم ودوران الجذع والتداخل."""
    g = K.GAITS[GAIT_B]
    v = g["S"] / (g["stance"] * g["T"]) * 0.92
    out, steps = [], []
    prev = [True, True]
    for i in range(int((CUTS[1] - CUTS[0]) * FPS) + 2):
        t = CUTS[0] + i * (1 / FPS)
        lt = t - CUTS[0]
        phase = 0.2 + lt / g["T"]
        hip_x = -120.0 - v * 0.35 + v * lt
        gp = K.gait_pose(GAIT_B, phase, 1.0)
        feet = []
        for k, (fx, lift, fa, st) in enumerate(gp["feet"]):
            feet.append((hip_x + fx, 1590 - lift, fa))
            if st and not prev[k]:
                steps.append(t)
            prev[k] = st
        out.append(dict(t=t, hip_x=hip_x, feet=feet, gp=gp))
    return out, steps


def cam_B(f):
    return clamp(f["hip_x"] - 0.36 * W, 0, 2 * W)


def char_B(f, cam):
    t, gp = f["t"], f["gp"]
    an, af = gp["arm_near"], gp["arm_far"]
    _, wn = K.fk2(K.SHOULDER, an[0], an[1], K.UA, K.FA)
    _, wf = K.fk2(K.SHOULDER, af[0], af[1], K.UA, K.FA)
    blink = math.sin(math.pi * (t - 7.1) / 0.14) if 7.1 <= t < 7.24 else 0.0
    feet = [(x - cam, y, a) for (x, y, a) in f["feet"]]
    pose = K.Pose(hip=(f["hip_x"] - cam, 1590 - K.ANK - 432 + gp["bob"]), lean=gp["lean"], twist=gp["twist"],
                  breath=math.sin(t * 1.7), head_tilt=gp["head"] - 1, feet=feet,
                  arm_near=("ik", wn, -1, "torso"), arm_far=("ik", wf, -1, "torso"), blink=blink, brow=-0.6)
    return K.draw_character(pose, "general")


# ======================================================================= النصوص
FONT_DIR = os.path.join(ROOT, "assets", "fonts", "arabic")


def font(name, size, bold=True):
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), size, layout_engine=ImageFont.Layout.RAQM)
    if bold:
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
    return f


def text_rgba(txt, fnt, fill=(255, 255, 255), stroke=7, stroke_fill=(10, 8, 12), pad=40):
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    bb = tmp.textbbox((0, 0), txt, font=fnt, direction="rtl", language="ar", stroke_width=stroke)
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - bb[0], pad - bb[1]), txt, font=fnt, fill=fill + (255,), direction="rtl", language="ar",
           stroke_width=stroke, stroke_fill=stroke_fill + (255,))
    a = np.asarray(im, np.float32) / 255
    sh = cv2.GaussianBlur(a[..., 3], (0, 0), 6) * 0.6       # ظل ناعم يفصل النص عن الخلفية
    out = np.zeros_like(a)
    out[..., 3] = np.maximum(a[..., 3], sh)
    out[..., :3] = a[..., :3] * a[..., 3:4] / np.maximum(out[..., 3:4], 1e-4)
    return out


def place(img, rgba, cx, cy, scale=1.0, rot_=0.0, op=1.0):
    if scale <= 0.01 or op <= 0:
        return img
    im = rgba
    if scale != 1.0 or rot_:
        h, w = im.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot_, scale)
        nw, nh = int(w * scale * 1.2) + 4, int(h * scale * 1.4) + 4
        M[0, 2] += nw / 2 - w / 2
        M[1, 2] += nh / 2 - h / 2
        im = cv2.warpAffine(im, M, (nw, nh))
    h, w = im.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xs, ys = max(0, -x0), max(0, -y0)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    if x1 <= max(0, x0) or y1 <= max(0, y0):
        return img
    crop = im[ys:ys + y1 - max(0, y0), xs:xs + x1 - max(0, x0)]
    reg = img[max(0, y0):y1, max(0, x0):x1]
    a = crop[..., 3:4] * op
    reg[:] = reg * (1 - a) + crop[..., :3] * a
    return img


def tag_rgba(title, sub=None, red=False):
    ft, fs = font("Cairo-Variable.ttf", 58), font("Cairo-Variable.ttf", 32, False)
    tmp = ImageDraw.Draw(Image.new("L", (10, 10)))
    tw = tmp.textlength(title, font=ft, direction="rtl", language="ar")
    sw_ = tmp.textlength(sub, font=fs, direction="rtl", language="ar") if sub else 0
    w = int(max(tw, sw_) + 90)
    h = 150 if sub else 110
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([12, 14, w + 12, h + 14], 24, fill=(0, 0, 0, 90))
    bg = (178, 34, 34, 255) if red else (255, 255, 255, 255)
    fg = (255, 255, 255, 255) if red else (43, 28, 23, 255)
    d.rounded_rectangle([4, 4, w + 4, h + 4], 24, fill=bg, outline=(43, 28, 23, 255), width=5)
    d.text((w / 2 + 4, 56), title, font=ft, fill=fg, anchor="mm", direction="rtl", language="ar")
    if sub:
        d.text((w / 2 + 4, 112), sub, font=fs, fill=(255, 230, 230, 255) if red else (110, 110, 110, 255), anchor="mm", direction="rtl", language="ar")
    return np.asarray(im, np.float32) / 255


# ======================================================================= الإطارات
_G = {}


def _init():
    _G["A"] = cached_plate("A", plate_A)
    _G["Bfar"] = tile3(cached_plate("Bfar", plate_B_far))
    _G["Bnear"] = tile3(cached_plate("Bnear", plate_B_near))
    _G["C1"] = cached_plate("C1", plate_C1)
    _G["D"] = cached_plate("D", plate_D)
    _G["gait"], _ = gait_B()
    sub_f = font("Cairo-Variable.ttf", 62)
    subs = []
    for a, b, s in SUBS:
        rg = text_rgba(s, sub_f)
        if rg.shape[1] > W * 0.92:   # السطر الطويل يُصغَّر ليبقى داخل الإطار مع هامش آمن
            k = W * 0.92 / rg.shape[1]
            rg = cv2.resize(rg, (int(rg.shape[1] * k), int(rg.shape[0] * k)), interpolation=cv2.INTER_AREA)
        subs.append((a, b, rg))
    _G["subs"] = subs
    _G["tagA"] = tag_rgba("٣ يناير ٢٠٢٠", "هبوط رحلة دمشق ١٢:٣٣ فجرًا")
    _G["tagB"] = tag_rgba("قاسم سليماني", "قائد فيلق القدس")
    _G["end1"] = text_rgba("مقتل قاسم سليماني", font("ReemKufi.ttf", 120, False), fill=(255, 236, 214), stroke=9)
    _G["end2"] = tag_rgba("بضربة مسيّرة أمريكية قرب مطار بغداد", None, red=True)
    r = np.random.default_rng(11)
    _G["dust"] = [(r.uniform(0, W), r.uniform(0, H), r.uniform(1, 3), r.uniform(0, 6.3), r.uniform(5, 15)) for _ in range(90)]
    _G["sparks"] = [(r.uniform(-1, 1), r.uniform(0.3, 1.0), r.uniform(0.2, 1.0)) for _ in range(140)]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    d = ((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2
    _G["vig"] = (1 - 0.65 * np.clip(d * 0.5, 0, 1) ** 1.5)[..., None]


def shot_A(t):
    img = _G["A"][..., :3].copy()
    if (t * 1.2) % 1 < 0.5:                                        # ضوء التحذير على البرج يومض
        img = add_glow(img, 780, 1180 - 560, 20, (1.0, 0.2, 0.15), 1.2)
    img = add_glow(img, 230, 330, 160, (0.6, 0.7, 1.0), 0.25)
    # زرع: ظلّ مسيّرة صغيرة يعبر أمام القمر (سيُحصد في اللقطة C1)
    u = (t - 2.4) / 2.0
    if 0 <= u <= 1:
        dr = svg_png(wrap(V.reaper_planform(330 - 210 * u, 345 - 25 * u, 2.6, 184)))
        dr[..., :3] *= 0.12
        img = over(img, dr)
    # الطائرة القادمة من دمشق تقترب للهبوط (أضواء الهبوط ووميض الأجنحة)
    u = clamp((t - 0.1) / (CUTS[0] - 0.1))
    px, py = -260 + 1500 * u, 760 + 260 * ease(u)
    img = over(img, svg_png(wrap(a320(px, py, 8.0, 4.0))))
    img = add_glow(img, px + 120, py + 22, 70, (1.0, 0.95, 0.8), 0.9)
    if (t * 1.6) % 1 < 0.12:
        img = add_glow(img, px - 10, py + 8, 30, (1.0, 1.0, 1.0), 1.8)
    img = push(img, 0, CUTS[0], t, 1.0, 1.12, 0.5, 0.62, dx=-30)
    k = back_out((t - 0.7) / 0.28)
    if t > 0.7:
        img = place(img, _G["tagA"], 700, 360, k, -3)
    return img


def shot_B(t):
    i = min(len(_G["gait"]) - 1, int((t - CUTS[0]) * FPS))
    f = _G["gait"][i]
    cam = cam_B(f)
    far, near = _G["Bfar"], _G["Bnear"]
    xf = int(cam * 0.3)
    img = far[:, xf:xf + W, :3].copy()                    # البعيد يتحرك أبطأ (عمق/منظور)
    xn = int(cam)
    img = over(img, near[:, xn:xn + W])
    img = add_glow(img, 840 - (cam % W) * 0.0, 1560, 520, (1.0, 0.88, 0.62), 0.22)
    PPM_B = 570.0                               # رجل 1.72م ≈ 980 بكسل → 570 بكسل/متر (نفس مقياس السيارة)
    car = svg_png(wrap(V.avalon(CAR_X - cam, 1600, PPM_B, 0, lights=True)))
    img = over(img, car)
    img = add_glow(img, CAR_X - cam + 0.17 * PPM_B, 1600 - 0.9 * PPM_B, 90, (1.0, 0.1, 0.08), 0.7)
    ch = svg_png(wrap(char_B(f, cam)))
    a = ch[..., 3]
    G = 1590.0
    M = np.float32([[1, -0.55, 0.55 * G], [0, -0.28, G * 1.28]])
    sh = cv2.warpAffine(a, M, (W, H))
    yy = np.arange(H, dtype=np.float32)[:, None]
    mix = np.clip((yy - G) / 120, 0, 1)
    s_ = (cv2.GaussianBlur(sh, (0, 0), 2) * (1 - mix) + cv2.GaussianBlur(sh, (0, 0), 12) * mix) * (1 - 0.5 * mix)
    s_ = np.clip(s_ * 0.5, 0, 0.5)[..., None]
    img = img * (1 - s_) + np.array([0.05, 0.06, 0.12], np.float32) * s_
    img = over(img, ch)
    img = push(img, CUTS[0], CUTS[1], t, 1.0, 1.06, 0.45, 0.6)
    k = back_out((t - 5.8) / 0.28)
    if t > 5.8:
        img = place(img, _G["tagB"], 640, 470, k, -3)
    return img


def shot_C1(t):
    img = _G["C1"][..., :3].copy()
    u = (t - CUTS[1]) / (CUTS[2] - CUTS[1])
    x = 1300 - 1700 * (0.15 * u + 0.85 * ease(u))
    dr = svg_png(wrap(V.reaper_planform(x, 1050 + 60 * u, 34.0, 184)))   # امتداد 20م ≈ 680 بكسل
    img = over(img, dr)
    img = push(img, CUTS[1], CUTS[2], t, 1.05, 1.15, 0.5, 0.5)
    return img


def shot_C2(t):
    """منظار حراري: أبيض = ساخن. الطريق من الأعلى، سيارتان، علامة تصويب تضيق."""
    u = (t - CUTS[2]) / (CUTS[3] - CUTS[2])
    img = np.full((H, W), 0.18, np.float32)
    cv2.rectangle(img, (0, 820), (W, 1100), 0.30, -1)
    for x in range(-200, W + 200, 160):
        cv2.rectangle(img, (int(x - u * 120), 955), (int(x - u * 120 + 80), 965), 0.42, -1)
    cars = [(330 + u * 260, 960, 5.125, 1.92), (640 + u * 260, 960, 4.975, 1.85)]   # ستاريكس ثم أفالون (أبعاد حقيقية × 44)
    for cx, cy, L, Wd in cars:
        hl, hw = L * 22, Wd * 22
        cv2.rectangle(img, (int(cx - hl), int(cy - hw)), (int(cx + hl), int(cy + hw)), 0.55, -1)
        cv2.rectangle(img, (int(cx + hl * 0.45), int(cy - hw * 0.8)), (int(cx + hl * 0.95), int(cy + hw * 0.8)), 0.95, -1)   # المحرك ساخن
    cars = [(c[0], c[1]) for c in cars]
    img = cv2.GaussianBlur(img, (0, 0), 3)
    noise = np.random.default_rng(int(t * FPS)).standard_normal((H // 3, W // 3)).astype(np.float32)
    img = img + cv2.resize(noise, (W, H)) * 0.035
    out = np.repeat(img[..., None], 3, 2)
    out = out * np.array([0.92, 1.0, 0.92], np.float32)
    # التصويب
    tx, ty = cars[1]
    box = int(260 - 140 * ease(u * 1.4))
    col = (1.0, 1.0, 1.0)
    cv2.rectangle(out, (int(tx - box), int(ty - box)), (int(tx + box), int(ty + box)), col, 3)
    cv2.line(out, (W // 2, 0), (W // 2, H), (0.8, 0.8, 0.8), 2)
    cv2.line(out, (0, H // 2), (W, H // 2), (0.8, 0.8, 0.8), 2)
    cv2.circle(out, (W // 2, H // 2), 60, (0.85, 0.85, 0.85), 2)
    for (x, y, dx, dy) in ((60, 160, 1, 1), (W - 60, 160, -1, 1), (60, H - 260, 1, -1), (W - 60, H - 260, -1, -1)):
        cv2.line(out, (x, y), (x + dx * 90, y), col, 4)
        cv2.line(out, (x, y), (x, y + dy * 90), col, 4)
    if u > 0.55 and (t * 6) % 1 < 0.5:
        cv2.rectangle(out, (int(tx - box - 10), int(ty - box - 10)), (int(tx + box + 10), int(ty + box + 10)), (1.0, 0.3, 0.3), 4)
    return out


PPM_D = 110.0       # مقياس اللقطة الواسعة: الأفالون 4.975م ≈ 547 بكسل


def convoy_D(t):
    """مواضع الموكب (الطرف الخلفي لكل مركبة): ستاريكس خلف، أفالون أمام — تسير بسرعة ثابتة."""
    dx = (t - CUTS[3]) * 260
    av = 260 + dx
    st = av - 5.169 * PPM_D - 1.6 * PPM_D
    return av, st, dx


def impact_point():
    av, _, _ = convoy_D(IMPACT)
    return (av + 2.5 * PPM_D, 1640 - 0.8 * PPM_D)


def shot_D(t):
    img = _G["D"][..., :3].copy()
    av, st, dx = convoy_D(t)
    wheel = dx / (0.34 * PPM_D)
    for x_rear, fn, length in ((st, V.starex, 5.125), (av, V.avalon, 4.975)):
        img = add_glow(img, x_rear + length * PPM_D + 90, 1560, 120, (1.0, 0.95, 0.75), 0.35)   # أضواء أمامية
        img = over(img, svg_png(wrap(fn(x_rear, 1640, PPM_D, wheel))))
    impact_t = IMPACT
    tgt = impact_point()
    if t < impact_t:
        p = clamp((t - (CUTS[3] + 0.15)) / (impact_t - CUTS[3] - 0.15))
        if p > 0:
            sx, sy = tgt[0] + 330, tgt[1] - 1450
            mx, my = sx + (tgt[0] - sx) * p ** 1.6, sy + (tgt[1] - sy) * p ** 1.6
            trail = np.zeros((H, W), np.float32)
            cv2.line(trail, (int(sx), int(sy)), (int(mx), int(my)), 1.0, 16, cv2.LINE_AA)
            trail = cv2.GaussianBlur(trail, (0, 0), 10)[..., None]
            img = img * (1 - trail * 0.5) + trail * np.array([0.62, 0.6, 0.6], np.float32) * 0.5   # دخان رمادي
            ang = math.atan2(my - sy, mx - sx)
            body = np.zeros((H, W), np.float32)
            bx0, by0 = mx - math.cos(ang) * 70, my - math.sin(ang) * 70
            cv2.line(body, (int(bx0), int(by0)), (int(mx), int(my)), 1.0, 12, cv2.LINE_AA)
            img = img * (1 - body[..., None]) + body[..., None] * np.array([0.75, 0.75, 0.78], np.float32)
            img = add_glow(img, bx0, by0, 60, (1.0, 0.75, 0.35), 2.6)                         # لهب المحرك
    else:
        img = explosion(img, t - impact_t, tgt)
    sh = max(0.0, 1 - (t - impact_t) / 0.7) if t >= impact_t else 0.0
    img = push(img, CUTS[3], CUTS[4], t, 1.0, 1.08, 0.6, 0.78, shake=sh * 1.5)
    if t >= impact_t:
        fl = max(0.0, 1 - (t - impact_t) / 0.22)
        img = img + (1 - img) * fl
    return img


def explosion(img, e, c):
    """كرة نار تتسع (قلب أبيض ← أصفر ← برتقالي)، دخان داكن صاعد، شرر، وموجة صدمة."""
    x, y = c
    R = 380 * (1 - math.exp(-e * 6))
    smoke = np.zeros((H, W), np.float32)
    r = np.random.default_rng(5)
    for k in range(14):
        ang = r.uniform(math.pi * 1.05, math.pi * 1.95)
        d = R * r.uniform(0.3, 0.9)
        sx, sy = x + math.cos(ang) * d, y + math.sin(ang) * d - e * 160
        cv2.circle(smoke, (int(sx), int(sy)), int(R * r.uniform(0.35, 0.6) + e * 60), 1.0, -1)
    smoke = cv2.GaussianBlur(smoke, (0, 0), 18)[..., None] * clamp(e * 3) * 0.85
    img = img * (1 - smoke) + np.array([0.09, 0.07, 0.08], np.float32) * smoke
    fire = np.zeros((H, W), np.float32)
    for k in range(9):
        a = k / 9 * 2 * math.pi + e
        cv2.circle(fire, (int(x + math.cos(a) * R * 0.35), int(y - 40 + math.sin(a) * R * 0.25 - e * 40)), int(R * 0.45), 1.0, -1)
    fire = cv2.GaussianBlur(fire, (0, 0), 14) * max(0.0, 1 - e / 2.2)
    core = cv2.GaussianBlur(fire ** 3, (0, 0), 8)
    img = img + fire[..., None] * np.array([1.0, 0.45, 0.08], np.float32) * 1.3 + core[..., None] * np.array([1.0, 0.95, 0.7], np.float32) * 1.4
    if e < 0.6:   # موجة الصدمة
        ring = np.zeros((H, W), np.float32)
        cv2.ellipse(ring, (int(x), int(y)), (int(200 + e * 1500), int(40 + e * 260)), 0, 0, 360, 1.0, 8)
        img = img + cv2.GaussianBlur(ring, (0, 0), 4)[..., None] * (1 - e / 0.6) * 0.6
    for (vx, vy, sp) in _G["sparks"]:
        px = x + vx * 900 * sp * e
        py = y - vy * 1100 * sp * e + 900 * e * e
        if 0 < px < W and 0 < py < H and e < 1.6:
            cv2.circle(img, (int(px), int(py)), 3, (1.0, 0.8, 0.4), -1, cv2.LINE_AA)
    img = add_glow(img, x, y, 600, (1.0, 0.45, 0.15), 0.6 * max(0.3, 1 - e / 3))
    return img


def shot_E(t):
    e = t - IMPACT
    img = _G["D"][..., :3].copy() * 0.75
    img = explosion(img, 0.9 + (t - CUTS[4]) * 0.6, impact_point())
    for k in range(3):   # ألسنة لهب ترتعش
        fl = 0.7 + 0.3 * math.sin(t * 17 + k * 2)
        img = add_glow(img, 700 + k * 60, 1530, 140, (1.0, 0.5, 0.12), 0.5 * fl)
    img = push(img, CUTS[4], DUR, t, 1.12, 1.0, 0.55, 0.75)
    k = back_out((t - CUTS[4] - 0.3) / 0.3)
    if t > CUTS[4] + 0.3:
        img = place(img, _G["end1"], W / 2, 620, k, 0)
    k2 = back_out((t - CUTS[4] - 0.7) / 0.3)
    if t > CUTS[4] + 0.7:
        img = place(img, _G["end2"], W / 2, 800, k2, -2)
    return img


def frame(i):
    if not _G:
        _init()
    t = i / FPS
    if t < CUTS[0]:
        img = shot_A(t)
    elif t < CUTS[1]:
        img = shot_B(t)
    elif t < CUTS[2]:
        img = shot_C1(t)
    elif t < CUTS[3]:
        img = shot_C2(t)
    elif t < CUTS[4]:
        img = shot_D(t)
    else:
        img = shot_E(t)
    if not (CUTS[2] <= t < CUTS[3]):
        # غبار/جسيمات دقيقة + إطار مظلم
        dl = np.zeros((H, W), np.float32)
        for (x, y, r_, ph, sp) in _G["dust"]:
            cv2.circle(dl, (int((x + 6 * math.sin(t + ph)) % W), int((y - sp * t) % H)), int(r_), 0.3 + 0.3 * math.sin(t * 2 + ph), -1)
        img = img + cv2.GaussianBlur(dl, (0, 0), 1.2)[..., None] * np.array([0.8, 0.8, 1.0], np.float32) * 0.35
    img = img * _G["vig"]
    for a, b, rg in _G["subs"]:
        if a <= t <= b:
            op = min(ease((t - a) / 0.15), ease((b - t) / 0.15))
            img = place(img, rg, W / 2, 1720, 1.0, 0, op)
    # انتقالات: غمس للأسود عند القطع (0.2ث) عدا قطع الصاروخ/الانفجار
    f = min(ease(t / 0.5), ease((DUR - t) / 0.7))
    for c in CUTS[:3]:
        if abs(t - c) < 0.18:
            f = min(f, abs(t - c) / 0.18)
    img = np.clip(img * f, 0, 1)
    return (img * 255 + 0.5).astype(np.uint8)


# ======================================================================= الصوت
def buzz(dur):
    SR = sfx.SR
    tt = np.arange(int(dur * SR)) / SR
    f = 118 * (1 + 0.04 * np.sin(2 * np.pi * 0.3 * tt))
    ph = np.cumsum(f) / SR
    x = (2 * (ph % 1) - 1) * 0.5 + np.sign(np.sin(2 * np.pi * ph * 2)) * 0.15
    x = sfx._lp(x, 900)
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.2
    pan = np.linspace(0.8, -0.8, len(tt))
    return np.stack([x * env * np.sqrt((1 - pan) / 2), x * env * np.sqrt((1 + pan) / 2)], 1).astype(np.float32)


def beep(f=1800, d=0.07):
    SR = sfx.SR
    tt = np.arange(int(d * SR)) / SR
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.03)
    return sfx.stereo(x.astype(np.float32))


def audio(out):
    SR = sfx.SR
    n = int((DUR + 1) * SR)
    mix = np.zeros((n, 2), np.float32)
    voice = np.zeros(n, np.float32)

    def put(x, t, g, track=None):
        s = int(t * SR)
        e = min(n, s + len(x))
        mix[s:e] += x[: e - s] * g
        if track is not None:
            track[s:e] = 1

    put(sfx.drone(dur=DUR + 1, note="D"), 0, 0.30)
    put(sfx.wind(dur=IMPACT), 0, 0.18)
    put(buzz(2.4), 2.2, 0.07)             # زرع صوتي خافت للمسيّرة
    put(buzz(4.0), 5.4, 0.05)
    _, steps = gait_B()
    for k, st in enumerate(steps):
        put(sfx.step(0.8, "stone", False, seed=k), st, 0.30)
    put(buzz(1.8), CUTS[1] - 0.1, 0.45)
    for k in range(8):
        put(beep(1700 + 200 * (k % 2)), CUTS[2] + 0.3 + k * 0.25, 0.12)
    put(sfx.glitch(0.3), CUTS[2] - 0.02, 0.15)
    put(sfx.whoosh(0.9, -1), CUTS[3] + 0.15, 0.5)
    put(sfx.riser(1.0), IMPACT - 1.0, 0.35)
    put(sfx.boom(), IMPACT, 1.0)
    put(sfx.sub_drop(), IMPACT, 0.7)
    put(sfx.fire(dur=3.0), IMPACT + 0.2, 0.35)
    put(sfx.impact(), CUTS[4] + 0.3, 0.35)
    for t0, k in NARR:
        sr2, v = wavfile.read(os.path.join(HERE, f"n{k}.wav"))
        v = v.astype(np.float32) / 32768
        if v.ndim == 1:
            v = np.stack([v, v], 1)
        if sr2 != SR:
            v = cv2.resize(v, (2, int(len(v) * SR / sr2)), interpolation=cv2.INTER_LINEAR)
        put(v, t0, 1.3, voice)
    from scipy.ndimage import gaussian_filter1d
    duck = np.clip(gaussian_filter1d(voice, SR * 0.15) * 1.3, 0, 1)
    music = mix.copy()
    e = int(DUR * SR)
    mix = mix[:e]
    mix[:int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))[:, None]
    mix[e - int(0.7 * SR):] *= np.linspace(1, 0, int(0.7 * SR))[:, None]
    mix = np.tanh(mix * 1.1) * 0.92
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))


def main():
    if sys.argv[1:2] == ["x"]:
        _init()
        ts = [float(v) for v in sys.argv[2:6]]
        ims = [frame(int(t * FPS)) for t in ts]
        sheet = np.zeros((H * 2 + 30, W * 2 + 30, 3), np.uint8) + 20
        for k, im in enumerate(ims):
            y, x = 10 + (k // 2) * (H + 10), 10 + (k % 2) * (W + 10)
            sheet[y:y + H, x:x + W] = im
        out = os.path.join(CACHE, "qc.png")
        cv2.imwrite(out, cv2.resize(sheet, (sheet.shape[1] // 3, sheet.shape[0] // 3))[..., ::-1])
        print(out)
        return
    _init()
    N = int(DUR * FPS)
    vid, wav = os.path.join(CACHE, "video.mp4"), os.path.join(CACHE, "audio.wav")
    audio(wav)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    with Pool(2, initializer=_init) as pool:
        for k, fr in enumerate(pool.imap(frame, range(N), chunksize=3)):
            ff.stdin.write(fr.tobytes())
            if k % 60 == 0:
                print(f"{k}/{N}", flush=True)
    ff.stdin.close()
    ff.wait()
    out = os.path.join(CACHE, "soleimani_story.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-af", "loudnorm=I=-14:TP=-1.5", "-shortest", "-movflags", "+faststart", out], check=True)
    print("تم:", out)


if __name__ == "__main__":
    main()
