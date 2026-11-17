"""الخطوط والعناوين السينمائية (عربي + إنجليزي) — تشكيل عربي صحيح عبر Raqm."""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")

FONTS = {
    # عربي
    "amiri": "arabic/Amiri-Bold.ttf",            # نسخ كلاسيكي فخم — للعناوين التاريخية والوثائقية
    "amiri_regular": "arabic/Amiri-Regular.ttf",
    "ruqaa": "arabic/ArefRuqaa-Bold.ttf",        # رقعة — للعناوين التراثية والدرامية
    "kufi": "arabic/ReemKufi.ttf",               # كوفي حديث — عناوين ملحمية قوية
    "qahiri": "arabic/Qahiri-Regular.ttf",       # كوفي قاهري زخرفي — للافتتاحيات والفصول
    "cairo": "arabic/Cairo-Variable.ttf",        # حديث نظيف — للترجمة السفلية والنصوص التوضيحية
    # إنجليزي
    "cinzel": "english/Cinzel-Bold.ttf",                 # عناوين أفلام ملحمية (روماني)
    "cinzel_deco": "english/CinzelDecorative-Bold.ttf",
    "bebas": "english/BebasNeue-Bold.ttf",               # تريلرات وأكشن
    "anton": "english/Anton-Regular.ttf",                # قوي وعريض
    "oswald": "english/Oswald-Bold.ttf",                 # وثائقي حديث
    "playfair": "english/PlayfairDisplay-Variable.ttf",  # دراما أنيقة
    "cormorant": "english/CormorantGaramond-Bold.otf",   # كلاسيكي راقٍ
}

STYLES = {
    "title": dict(font="amiri", size=140, fill="gold", shadow=0.85, glow=0.5, tracking=0),
    "epic": dict(font="kufi", size=150, fill="gold", shadow=0.9, glow=0.6),
    "heritage": dict(font="ruqaa", size=130, fill="#f3e6c8", shadow=0.85, glow=0.3),
    "chapter": dict(font="qahiri", size=110, fill="#f3e6c8", shadow=0.8, glow=0.3),
    "subtitle": dict(font="cairo", size=54, fill="#ffffff", shadow=0.9, glow=0.0, box=False),
    "caption": dict(font="cairo", size=44, fill="#ffffff", shadow=0.0, glow=0.0, box=True),
    "lower_third": dict(font="cairo", size=48, fill="#ffffff", shadow=0.7, glow=0.0, bar="#c9a24a"),
    "en_title": dict(font="cinzel", size=130, fill="gold", shadow=0.85, glow=0.5, tracking=12),
    "en_trailer": dict(font="bebas", size=170, fill="#ffffff", shadow=0.9, glow=0.3, tracking=20),
    "en_doc": dict(font="oswald", size=80, fill="#ffffff", shadow=0.8, glow=0.0, tracking=4),
}


def font_path(name):
    p = FONTS.get(name, name)
    return p if os.path.isabs(p) else os.path.join(FONTS_DIR, p)


def is_arabic(s):
    return any("؀" <= ch <= "ۿ" or "ݐ" <= ch <= "ݿ" or "ﭐ" <= ch <= "ﻼ" for ch in s)


def _gold(w, h):
    ys = np.linspace(0, 1, h)[:, None]
    stops = np.array([[1.0, 0.93, 0.70], [0.93, 0.76, 0.38], [0.78, 0.56, 0.22], [0.98, 0.86, 0.55], [0.70, 0.50, 0.20]])
    pos = np.linspace(0, 1, len(stops))
    g = np.stack([np.interp(ys[:, 0], pos, stops[:, c]) for c in range(3)], 1)
    return np.repeat(g[:, None, :], w, 1)


def render_text(text, style="title", size=None, font=None, fill=None, max_width=1600, line_gap=0.25, q=1.0):
    """يرجع صورة RGBA (float, premultiplied) للنص مع الظل والتوهج."""
    st = dict(STYLES.get(style, STYLES["title"]))
    if font:
        st["font"] = font
    if fill:
        st["fill"] = fill
    if size:
        st["size"] = size
    if not is_arabic(text) and st["font"] in ("amiri", "ruqaa", "kufi", "qahiri", "cairo") and style in ("title", "epic"):
        st["font"] = "cinzel"
    sz = int(st["size"] * q)
    fnt = ImageFont.truetype(font_path(st["font"]), sz, layout_engine=ImageFont.Layout.RAQM)
    ar = is_arabic(text)
    kw = dict(direction="rtl", language="ar") if ar else {}
    # التفاف الأسطر
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(" "), ""
        for wd in words:
            test = (cur + " " + wd).strip()
            if fnt.getlength(test, **kw) > max_width * q and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = test
        lines.append(cur)
    tracking = st.get("tracking", 0) * q
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * (1 + line_gap))
    widths = [fnt.getlength(l, **kw) + tracking * len(l) for l in lines]
    pad = int(sz * 0.9)
    W = int(max(widths) + pad * 2)
    H = int(lh * len(lines) + pad * 2)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i, l in enumerate(lines):
        x = (W - widths[i]) / 2
        y = pad + i * lh
        if tracking and not ar:
            for ch in l:
                d.text((x, y), ch, font=fnt, fill=255)
                x += fnt.getlength(ch) + tracking
        else:
            d.text((x, y), l, font=fnt, fill=255, **kw)
    m = np.asarray(mask, np.float32) / 255
    if st["fill"] == "gold":
        col = _gold(W, H)
    else:
        h = st["fill"].lstrip("#")
        col = np.ones((H, W, 3), np.float32) * np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    rgb = col * m[..., None]
    a = m.copy()
    if st.get("shadow"):
        sh = cv2.GaussianBlur(m, (0, 0), sz * 0.06) * st["shadow"]
        sh = np.roll(np.roll(sh, int(sz * 0.03), 0), int(sz * 0.02), 1)
        halo = np.clip(cv2.GaussianBlur(m, (0, 0), sz * 0.3) * 2.2, 0, 1) * st["shadow"] * 0.55  # هالة داكنة للقراءة فوق الخلفيات الفاتحة
        sh = np.maximum(np.clip(sh * 1.6, 0, 1), halo)
        a = a + sh * (1 - a)
    if st.get("glow"):
        gl = cv2.GaussianBlur(rgb, (0, 0), sz * 0.25) * st["glow"] * 0.5
        rgb = rgb + gl * (1 - m[..., None])
        a = np.maximum(a, np.clip(gl.max(2), 0, 1) * 0.0 + a)
    if st.get("box"):
        box = np.zeros_like(a)
        box[int(pad * 0.6):H - int(pad * 0.6), int(pad * 0.4):W - int(pad * 0.4)] = 0.55
        a = np.maximum(a, box)
    if st.get("bar"):
        h = st["bar"].lstrip("#")
        bc = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
        bx = W - int(pad * 0.5) if ar else int(pad * 0.5)
        rgb[pad // 2:H - pad // 2, bx - int(6 * q):bx + int(6 * q)] = bc
        a[pad // 2:H - pad // 2, bx - int(6 * q):bx + int(6 * q)] = 1
    return np.concatenate([rgb, a[..., None]], 2).astype(np.float32)


def text_anim(t, start, dur, fade_in=0.9, fade_out=0.8, kind="rise"):
    """يرجع (opacity, dy, scale, blur) للنص في اللحظة t."""
    lt = t - start
    if lt < 0 or lt > dur:
        return 0, 0, 1, 0
    pin = min(1, lt / fade_in) if fade_in else 1
    pout = min(1, (dur - lt) / fade_out) if fade_out else 1
    p = min(pin, pout)
    e = 1 - (1 - p) ** 3
    slow = lt / dur
    if kind == "rise":
        return e, (1 - e) * 30, 1.0 + slow * 0.04, (1 - e) * 8
    if kind == "zoom":
        return e, 0, 0.9 + 0.1 * e + slow * 0.05, (1 - e) * 10
    if kind == "slam":
        s = 1.6 - 0.6 * min(1, lt / 0.25)
        return min(1, lt / 0.1) * pout, 0, s, 0
    return e, 0, 1, 0
