"""رسّام المشاهد الجاهزة: يولّد عوالم مقسمة لطبقات عمق (سماء، شمس، جبال، مدينة بقباب...)
كل طبقة صورة RGBA تُوضع على عمق مختلف فتعطي إحساسًا ثلاثي الأبعاد حقيقيًا مع حركة الكاميرا.
"""
import os
import hashlib
import json
import numpy as np
import cv2

CACHE = os.path.join(os.path.dirname(__file__), "..", ".cache", "sets")


def _rng(seed):
    return np.random.default_rng(seed)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def gradient(w, h, stops):
    """stops: [(0,'#hex'),(0.5,'#hex'),(1,'#hex')] رأسيًا."""
    ys = np.linspace(0, 1, h)
    pos = [s[0] for s in stops]
    cols = np.array([hexc(s[1]) for s in stops])
    out = np.stack([np.interp(ys, pos, cols[:, c]) for c in range(3)], 1)
    return np.repeat(out[:, None, :], w, 1).astype(np.float32)


def fractal_1d(w, seed, octaves=6, rough=0.5, base=6):
    r = _rng(seed)
    out = np.zeros(w)
    amp, freq, tot = 1.0, base, 0
    for _ in range(octaves):
        pts = r.uniform(-1, 1, freq + 2)
        xs = np.linspace(0, freq, w)
        out += np.interp(xs, np.arange(freq + 2), pts) * amp
        tot += amp
        amp *= rough
        freq *= 2
    return out / tot


def noise2d(w, h, seed, scale=64, octaves=5):
    r = _rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0
    s = scale
    for _ in range(octaves):
        g = r.random((max(2, h // s + 2), max(2, w // s + 2))).astype(np.float32)
        out += cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC) * amp
        tot += amp
        amp *= 0.5
        s = max(2, s // 2)
    return out / tot


def rgba(rgb, alpha):
    a = np.clip(alpha, 0, 1)[..., None].astype(np.float32)
    return np.concatenate([rgb * a, a], 2).astype(np.float32)


def silhouette(w, h, heights_px, color_top, color_bottom, rim=None, rim_w=4, haze=None, haze_amt=0.0):
    """أرض/جبال: heights_px مصفوفة بطول w = ارتفاع الحافة من الأعلى."""
    ys = np.arange(h)[:, None]
    mask = (ys >= heights_px[None, :]).astype(np.float32)
    mask = cv2.GaussianBlur(mask, (0, 0), 1.2)
    depth = np.clip((ys - heights_px[None, :]) / (h * 0.35), 0, 1)[..., None]
    rgb = hexc(color_top) * (1 - depth) + hexc(color_bottom) * depth
    if rim is not None:
        edge = np.exp(-np.maximum(ys - heights_px[None, :], 0) / rim_w)[..., None] * mask[..., None]
        rgb = rgb + hexc(rim) * edge * 0.9
    if haze is not None:
        rgb = rgb * (1 - haze_amt) + hexc(haze) * haze_amt
    return rgba(rgb, mask)


def sun(w, h, cx, cy, r, core="#fff4d6", glow="#ffb347", glow_r=6.0):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    disc = np.clip((r - d) / 2.0 + 0.5, 0, 1)
    g = np.exp(-(d / (r * glow_r)) ** 1.4) * 0.85
    rgb = hexc(core) * disc[..., None] + hexc(glow) * g[..., None]
    a = np.clip(disc + g, 0, 1)
    return np.concatenate([rgb, a[..., None]], 2).astype(np.float32)  # premultiplied (إضاءة)


def clouds(w, h, seed, color="#ffcc99", density=0.5, y0=0.1, y1=0.5, stretch=4):
    n = noise2d(w // stretch, h, seed, scale=48)
    n = cv2.resize(n, (w, h))
    ys = np.linspace(0, 1, h)[:, None]
    band = np.clip(1 - np.abs((ys - (y0 + y1) / 2) / ((y1 - y0) / 2 + 1e-6)), 0, 1) ** 0.7
    a = np.clip((n - (1 - density)) * 3, 0, 1) * band * 0.75
    a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 6)
    shade = 0.75 + 0.25 * (1 - ys)
    return rgba(hexc(color) * shade[..., None] * np.ones((1, w, 1)), a)


def fog_band(w, h, seed, color="#ffd2a0", y=0.7, thick=0.18, amt=0.55):
    n = cv2.resize(noise2d(w // 6, h // 2, seed, 32), (w, h))
    ys = np.linspace(0, 1, h)[:, None]
    a = np.exp(-((ys - y) / thick) ** 2) * (0.5 + 0.6 * n) * amt
    return rgba(hexc(color) * np.ones((h, w, 1)), a.astype(np.float32))


def skyline(w, h, seed, base_y, color_top, color_bottom, scale=1.0, rim=None, windows=None, domes=True,
            density=1.0, haze=None, haze_amt=0.0):
    """مدينة شرقية: مبانٍ، قباب، مآذن."""
    r = _rng(seed)
    hp = np.full(w, float(h), np.float32)
    shapes = np.zeros((h, w), np.uint8)
    x = 0
    win_pts = []
    while x < w:
        bw = int(r.integers(60, 180) * scale)
        bh = int(r.integers(80, 260) * scale)
        top = int(base_y - bh)
        cv2.rectangle(shapes, (x, top), (x + bw, h), 255, -1)
        kind = r.random()
        if domes and kind < 0.28 * density:  # قبة على رقبة
            dr = int(bw * r.uniform(0.32, 0.45))
            cx = x + bw // 2
            drum = int(dr * 0.5)
            cv2.rectangle(shapes, (cx - int(dr * 0.85), top - drum), (cx + int(dr * 0.85), top), 255, -1)
            cv2.ellipse(shapes, (cx, top - drum), (dr, int(dr * 1.1)), 0, 180, 360, 255, -1)
            cv2.line(shapes, (cx, top - drum - int(dr * 1.1)), (cx, top - drum - int(dr * 1.1) - int(18 * scale)), 255, max(2, int(3 * scale)))
        elif domes and kind < 0.40 * density:  # مئذنة
            mw = max(6, int(14 * scale))
            mh = int(r.integers(220, 380) * scale)
            cx = x + int(bw * r.uniform(0.2, 0.8))
            cv2.rectangle(shapes, (cx - mw // 2, int(base_y - mh)), (cx + mw // 2, h), 255, -1)
            cv2.rectangle(shapes, (cx - mw, int(base_y - mh * 0.7)), (cx + mw, int(base_y - mh * 0.7) + int(8 * scale)), 255, -1)
            pts = np.array([[cx - mw // 2 - 2, int(base_y - mh)], [cx + mw // 2 + 2, int(base_y - mh)], [cx, int(base_y - mh - 30 * scale)]])
            cv2.fillPoly(shapes, [pts], 255)
        if windows is not None:
            for _ in range(int(bw * bh / 2500 * r.uniform(0.2, 0.8))):
                win_pts.append((x + r.integers(8, max(9, bw - 8)), r.integers(top + 10, int(base_y))))
        x += bw + int(r.integers(-20, 25) * scale)
    mask = shapes.astype(np.float32) / 255
    mask = cv2.GaussianBlur(mask, (0, 0), 0.8)
    ys = np.arange(h)[:, None]
    tops = np.argmax(shapes > 0, axis=0).astype(np.float32)
    tops[tops == 0] = h
    depth = np.clip((ys - (base_y - 260 * scale)) / (h - base_y + 260 * scale), 0, 1)[..., None]
    rgb = hexc(color_top) * (1 - depth) + hexc(color_bottom) * depth
    rgb = rgb * np.ones((1, w, 1), np.float32)
    if rim is not None:
        edge = np.exp(-np.maximum(ys - tops[None, :], 0) / 5)[..., None]
        rgb = rgb + hexc(rim) * edge * 0.7
    if windows is not None:
        wl = np.zeros((h, w), np.float32)
        for (wx, wy) in win_pts:
            cv2.rectangle(wl, (int(wx), int(wy)), (int(wx + 5 * scale), int(wy + 8 * scale)), 1.0, -1)
        wl = wl * mask
        glow = cv2.GaussianBlur(wl, (0, 0), 4)
        rgb = rgb * (1 - wl[..., None]) + hexc(windows) * (wl + glow * 0.6)[..., None]
    if haze is not None:
        rgb = rgb * (1 - haze_amt) + hexc(haze) * haze_amt
    return rgba(rgb, mask)


# ------------------------------------------------------------------ المشاهد الجاهزة
def _layer(name, img, z, y=0.0, x=0.0, scale=1.0, **kw):
    d = dict(name=name, img=img, z=z, y=y, x=x, scale=scale)
    d.update(kw)
    return d


K = 1.7  # الطبقة أكبر من الإطار بهذا المعامل (مساحة لحركة الكاميرا)


def _dims(W, H):
    w, h = int(W * K), int(H * K)
    row = lambda f: h / 2 + (f - 0.5) * H        # موضع رأسي بنسبة الشاشة → سطر في الطبقة
    col = lambda f: w / 2 + (f - 0.5) * W
    sg = lambda stops: [(0.5 + (p - 0.5) / K, c) for p, c in stops]
    sy = lambda f: 0.5 + (f - 0.5) / K
    return w, h, row, col, sg, sy


def set_city_sunset(W, H, seed=11):
    """مدينة بقباب ومآذن وقت الغروب البرتقالي."""
    w, h, row, col, sg, sy = _dims(W, H)
    L = []
    sky = gradient(w, h, sg([(-0.3, "#1e0f30"), (0.1, "#6e2a26"), (0.38, "#c8602e"), (0.6, "#ef9a4e"), (1.2, "#f6c27a")]))
    L.append(_layer("sky", rgba(sky, np.ones((h, w))), 9000))
    L.append(_layer("sun", sun(w, h, col(0.56), row(0.52), 62, glow_r=3.2), 8500, light=True))
    L.append(_layer("clouds", clouds(w, h, seed, "#ffb07a", 0.45, sy(0.0), sy(0.42)), 7000))
    L.append(_layer("city_far", skyline(w, h, seed + 1, row(0.66), "#c0623c", "#d98250", 0.7, domes=True, haze="#f2a060", haze_amt=0.45), 4200))
    L.append(_layer("haze", fog_band(w, h, seed + 2, "#ffbd7a", sy(0.64), 0.05, 0.6), 3500))
    L.append(_layer("city_mid", skyline(w, h, seed + 3, row(0.76), "#6b2e24", "#3a1a1c", 1.1, rim="#ff9a4a", windows="#ffcf7a"), 2200))
    ground = fractal_1d(w, seed + 4, 5, 0.5, 4) * H * 0.03 + row(0.9)
    L.append(_layer("rooftops", silhouette(w, h, ground, "#2a1414", "#120909", rim="#ff8a3a", rim_w=3), 900))
    return L, dict(fog="#f0a060", sun=(0.56, 0.52), rays=0.3, ambient=["wind", "crowd"], palette="warm")


def set_desert_dusk(W, H, seed=21):
    w, h, row, col, sg, sy = _dims(W, H)
    L = []
    sky = gradient(w, h, sg([(-0.3, "#0c1430"), (0.2, "#4a2e5a"), (0.5, "#c05a3e"), (0.63, "#ec9a58"), (1.2, "#f8cf98")]))
    L.append(_layer("sky", rgba(sky, np.ones((h, w))), 9000))
    L.append(_layer("sun", sun(w, h, col(0.42), row(0.6), 75, glow="#ff9a50", glow_r=3.5), 8500, light=True))
    L.append(_layer("clouds", clouds(w, h, seed, "#ff9f7a", 0.35, sy(0.05), sy(0.4), 6), 7000))
    for i, (z, by, amp, ct, cb, hz) in enumerate([
        (5000, 0.64, 0.04, "#b5644e", "#c87a56", 0.5),
        (3200, 0.70, 0.06, "#8a4434", "#6a3428", 0.3),
        (1800, 0.78, 0.07, "#5a2a22", "#3a1a16", 0.12),
        (800, 0.90, 0.05, "#2a1210", "#140806", 0.0)]):
        hp = row(by) + fractal_1d(w, seed + 10 + i, 4, 0.45, 3) * H * amp
        L.append(_layer(f"dune{i}", silhouette(w, h, hp, ct, cb, rim="#ffb070", rim_w=3 + i, haze="#e89a6a", haze_amt=hz), z))
        if i == 1:
            L.append(_layer("haze", fog_band(w, h, seed + 30, "#ffc08a", sy(0.69), 0.04, 0.55), 2600))
    return L, dict(fog="#e89a6a", sun=(0.42, 0.6), rays=0.35, ambient=["wind"], palette="warm")


def set_night_mountains(W, H, seed=31):
    w, h, row, col, sg, sy = _dims(W, H)
    L = []
    sky = gradient(w, h, sg([(-0.3, "#02040c"), (0.3, "#0b1a3a"), (0.7, "#1e3a66"), (1.2, "#2a4a78")]))
    L.append(_layer("sky", rgba(sky, np.ones((h, w))), 9500))
    L.append(_layer("moon", sun(w, h, col(0.7), row(0.2), 55, core="#f4f6ff", glow="#7aa0ff", glow_r=4), 9000, glow=0.2, light=True))
    L.append(_layer("clouds", clouds(w, h, seed, "#5a7ab0", 0.35, sy(0.1), sy(0.45)), 7500))
    cols = [("#2c4470", "#22385e", 0.55), ("#1c2e50", "#14223e", 0.35), ("#111c34", "#0a1224", 0.15), ("#070c18", "#03060c", 0)]
    for i, (z, by, amp) in enumerate([(6000, 0.5, 0.12), (3800, 0.6, 0.12), (2000, 0.72, 0.1), (850, 0.88, 0.06)]):
        hp = row(by) + fractal_1d(w, seed + 10 + i, 7, 0.55, 3 + i) * H * amp
        ct, cb, hz = cols[i]
        L.append(_layer(f"mount{i}", silhouette(w, h, hp, ct, cb, rim="#8fb0ff", rim_w=2, haze="#3a5a90", haze_amt=hz), z))
        if i in (1, 2):
            L.append(_layer(f"mist{i}", fog_band(w, h, seed + 40 + i, "#6a8ac0", sy(by + 0.07), 0.04, 0.45), z - 300))
    return L, dict(fog="#3a5a90", sun=(0.7, 0.2), rays=0.25, ambient=["wind"], particles=["stars"], palette="cold")


def set_storm_plain(W, H, seed=41):
    w, h, row, col, sg, sy = _dims(W, H)
    L = []
    sky = gradient(w, h, sg([(-0.3, "#0c1014"), (0.3, "#2a3238"), (0.7, "#44505a"), (1.2, "#56626c")]))
    L.append(_layer("sky", rgba(sky, np.ones((h, w))), 9000))
    L.append(_layer("clouds_hi", clouds(w, h, seed, "#3a444c", 0.65, sy(-0.2), sy(0.4), 3), 7000))
    L.append(_layer("clouds_lo", clouds(w, h, seed + 1, "#5a646c", 0.5, sy(0.25), sy(0.62), 3), 5000))
    for i, (z, by, amp, ct, cb) in enumerate([(3500, 0.68, 0.02, "#2a3034", "#20262a"), (1500, 0.78, 0.03, "#15191c", "#0c0f11"),
                                               (750, 0.92, 0.02, "#08090a", "#040505")]):
        hp = row(by) + fractal_1d(w, seed + 10 + i, 5, 0.5, 6) * H * amp
        L.append(_layer(f"ground{i}", silhouette(w, h, hp, ct, cb, haze="#4a545c", haze_amt=0.4 - i * 0.15), z))
    return L, dict(fog="#4a545c", sun=None, rays=0, ambient=["rain", "wind"], particles=["rain"], palette="cold")


def set_void(W, H, seed=51):
    """استوديو أسود مع بقعة ضوء — لعرض الصور والعناوين ثلاثية الأبعاد."""
    w, h, row, col, sg, sy = _dims(W, H)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xs - w / 2) / W) ** 2 + ((ys - row(0.45)) / H) ** 2)
    v = np.exp(-(d / 0.45) ** 2)
    rgb = np.stack([v * 0.16, v * 0.13, v * 0.10], 2).astype(np.float32) + 0.012
    return [_layer("void", rgba(rgb, np.ones((h, w))), 9000)], dict(fog="#000000", sun=None, rays=0, ambient=[], particles=["dust"], palette="neutral")


SETS = {
    "city_sunset": (set_city_sunset, "مدينة بقباب ومآذن وقت الغروب"),
    "desert_dusk": (set_desert_dusk, "صحراء وكثبان عند المغيب"),
    "night_mountains": (set_night_mountains, "جبال ليلية مع قمر وضباب"),
    "storm_plain": (set_storm_plain, "سهل عاصف ممطر"),
    "void": (set_void, "استوديو أسود لعرض الصور والعناوين"),
}


def build_set(name, W, H):
    """مع ذاكرة مؤقتة: يُرسم مرة ويُحفظ."""
    key = f"{name}_{W}x{H}"
    d = os.path.join(CACHE, key)
    meta = os.path.join(d, "set.json")
    if os.path.exists(meta):
        info = json.load(open(meta))
        layers = []
        for Lm in info["layers"]:
            img = cv2.imread(os.path.join(d, Lm["file"]), cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
            img = img[..., [2, 1, 0, 3]]
            Lm = dict(Lm)
            Lm["img"] = img
            layers.append(Lm)
        return layers, info["env"]
    layers, env = SETS[name][0](W, H)
    os.makedirs(d, exist_ok=True)
    out = []
    for i, Lm in enumerate(layers):
        f = f"{i:02d}_{Lm['name']}.png"
        img16 = (np.clip(Lm["img"], 0, 1) * 65535).astype(np.uint16)[..., [2, 1, 0, 3]]
        cv2.imwrite(os.path.join(d, f), img16)
        m = {k: v for k, v in Lm.items() if k != "img"}
        m["file"] = f
        out.append(m)
    json.dump({"layers": out, "env": env}, open(meta, "w"), ensure_ascii=False, indent=1)
    return layers, env
