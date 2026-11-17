"""العالم ثلاثي الأبعاد: صور مسطحة (طبقات) موضوعة في فضاء ثلاثي الأبعاد + كاميرا حقيقية.

الإحداثيات:
  x يمين، y تحت، z عمق (بعيد = أكبر). الكاميرا تبدأ عند z=0.
  كل طبقة لها عمق z، وإزاحة x,y، ودوران yaw/pitch/roll — فتتحرك وتدور ثلاثيًا.
  كلما كانت الطبقة أقرب تتحرك أسرع مع الكاميرا (Parallax) وتتغبش حسب البعد البؤري.
"""
import math
import numpy as np
import cv2

F = 1000.0  # البعد البؤري المرجعي


# ------------------------------------------------------------ التنعيم
def ease(p, kind="inout"):
    p = min(max(p, 0.0), 1.0)
    if kind == "linear":
        return p
    if kind == "in":
        return p ** 3
    if kind == "out":
        return 1 - (1 - p) ** 3
    if kind == "expo":
        return 1 - 2 ** (-10 * p) if p < 1 else 1
    if kind == "snap":  # حركة سريعة ثم تهدأ
        return 1 - (1 - p) ** 5
    return 3 * p * p - 2 * p * p * p if kind == "smooth" else (4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2)


def lerp_props(a, b, p):
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, (int, float)) and isinstance(a.get(k, v), (int, float)):
            out[k] = a.get(k, v) + (v - a.get(k, v)) * p
        else:
            out[k] = v
    return out


def keyframed(spec, t, dur, default):
    """spec إما قيم ثابتة، أو {from:{}, to:{}, ease:..}، أو {keys:[{t:..,...}]}"""
    base = dict(default)
    if not spec:
        return base
    if "keys" in spec:
        keys = sorted(spec["keys"], key=lambda k: k.get("t", 0))
        if t <= keys[0].get("t", 0):
            return lerp_props(base, {k: v for k, v in keys[0].items() if k != "t"}, 1)
        for k0, k1 in zip(keys, keys[1:]):
            if k0["t"] <= t <= k1["t"]:
                p = ease((t - k0["t"]) / max(k1["t"] - k0["t"], 1e-6), k1.get("ease", spec.get("ease", "inout")))
                a = lerp_props(base, {k: v for k, v in k0.items() if k not in ("t", "ease")}, 1)
                return lerp_props(a, {k: v for k, v in k1.items() if k not in ("t", "ease")}, p)
        return lerp_props(base, {k: v for k, v in keys[-1].items() if k not in ("t", "ease")}, 1)
    if "from" in spec or "to" in spec:
        start = spec.get("start", 0.0)
        end = spec.get("end", dur)
        p = ease((t - start) / max(end - start, 1e-6), spec.get("ease", "inout"))
        a = lerp_props(base, spec.get("from", {}), 1)
        return lerp_props(a, spec.get("to", {}), p)
    return lerp_props(base, spec, 1)


# ------------------------------------------------------------ حركات كاميرا جاهزة
CAMERA_DEFAULT = dict(x=0.0, y=0.0, z=0.0, yaw=0.0, pitch=0.0, roll=0.0, fov=1.0, focus=1000.0, aperture=0.0, shake=0.0)


def camera_preset(name, amount=1.0, dur=6.0, ease_kind="inout"):
    a = amount
    P = {
        "static": ({}, {}),
        "dolly_in": ({"z": 0}, {"z": 380 * a}),              # دفع للأمام
        "dolly_out": ({"z": 380 * a}, {"z": 0}),             # رجوع للخلف
        "truck_left": ({"x": 160 * a}, {"x": -160 * a}),     # انزلاق يسار
        "truck_right": ({"x": -160 * a}, {"x": 160 * a}),    # انزلاق يمين
        "crane_up": ({"y": 120 * a}, {"y": -140 * a}),       # رافعة لأعلى
        "crane_down": ({"y": -140 * a}, {"y": 120 * a}),
        "orbit_left": ({"x": 220 * a, "yaw": -6 * a}, {"x": -220 * a, "yaw": 6 * a}),   # دوران حول الهدف
        "orbit_right": ({"x": -220 * a, "yaw": 6 * a}, {"x": 220 * a, "yaw": -6 * a}),
        "push_tilt": ({"z": 0, "pitch": 4 * a}, {"z": 300 * a, "pitch": -2 * a}),
        "vertigo": ({"z": 0, "fov": 1.0}, {"z": 320 * a, "fov": 0.72}),   # دوخة هيتشكوك
        "roll_in": ({"z": 0, "roll": -4 * a}, {"z": 260 * a, "roll": 2 * a}),
        "reveal_up": ({"y": 260 * a, "pitch": 6 * a, "z": 0}, {"y": -60 * a, "pitch": 0, "z": 160 * a}),
        "drift": ({"x": -40 * a, "y": 10 * a}, {"x": 40 * a, "y": -10 * a, "z": 80 * a}),
    }
    fr, to = P[name]
    return {"from": fr, "to": to, "ease": ease_kind}


# ------------------------------------------------------------ الإسقاط
def _rot(yaw, pitch, roll):
    y, p, r = map(math.radians, (yaw, pitch, roll))
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(p), -math.sin(p)], [0, math.sin(p), math.cos(p)]])
    Rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


class Camera:
    def __init__(self, W, H, p, q=1.0):
        """q: معامل الدقة (1 = الدقة المرجعية، 0.5 = معاينة سريعة)."""
        self.W, self.H, self.q = W, H, q
        self.pos = np.array([p["x"], p["y"], p["z"]], float)
        self.R = _rot(-p["yaw"], -p["pitch"], -p["roll"])
        self.f = F * p["fov"] * q
        self.p = p

    def project(self, P):
        """P: (n,3) نقاط في العالم → (n,2) على الشاشة، وعمقها."""
        Q = (P - self.pos) @ self.R.T
        z = np.maximum(Q[:, 2], 1.0)
        sx = self.W / 2 + Q[:, 0] * self.f / z
        sy = self.H / 2 + Q[:, 1] * self.f / z
        return np.stack([sx, sy], 1), Q[:, 2]


def layer_corners(img_w, img_h, L):
    """أركان الطبقة في العالم. scale=1 تعني: عند z الطبقة وبالكاميرا الأصلية تظهر بحجم بكسلاتها (على شاشة 1920)."""
    z = L["z"]
    s = L["scale"] * z / F
    hw, hh = img_w * s / 2, img_h * s / 2
    local = np.array([[-hw, -hh, 0], [hw, -hh, 0], [hw, hh, 0], [-hw, hh, 0]], float)
    R = _rot(L["yaw"], L["pitch"], L["roll"])
    # الإزاحة x,y معطاة ببكسلات الشاشة المرجعية → نحولها لوحدات العالم عند العمق z
    center = np.array([L["x"] * z / F, L["y"] * z / F, z])
    return local @ R.T + center


LAYER_DEFAULT = dict(x=0.0, y=0.0, z=1000.0, scale=1.0, yaw=0.0, pitch=0.0, roll=0.0, opacity=1.0, fog=0.0,
                     glow=0.0, brightness=1.0)


def render_layer(canvas, img, L, cam, fog_color=(0, 0, 0)):
    """يرسم طبقة RGBA (float 0..1، premultiplied) على canvas (H,W,3) ويرجع canvas."""
    h, w = img.shape[:2]
    corners = layer_corners(w, h, L)
    scr, depth = cam.project(corners)
    if (depth < 5).any():
        return canvas
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(src, scr.astype(np.float32))
    W, H = cam.W, cam.H
    # قص سريع: تجاهل الطبقة لو خارج الإطار
    if scr[:, 0].max() < 0 or scr[:, 0].min() > W or scr[:, 1].max() < 0 or scr[:, 1].min() > H:
        return canvas
    warped = cv2.warpPerspective(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    # عمق الميدان (DOF)
    ap = cam.p.get("aperture", 0.0)
    if ap > 0:
        zc = float(depth.mean())
        coc = ap * abs(1.0 / zc - 1.0 / max(cam.p["focus"] - cam.pos[2], 10)) * 1000.0 * cam.q
        coc = min(coc, 40)
        if coc > 0.6:
            k = int(coc * 3) | 1
            warped = cv2.GaussianBlur(warped, (k, k), coc)
    rgb = warped[..., :3]
    a0 = warped[..., 3:4]
    if L["brightness"] != 1.0:
        rgb = rgb * L["brightness"]
    if L["fog"] > 0:
        fc = np.array(fog_color, np.float32).reshape(1, 1, 3)
        rgb = rgb * (1 - L["fog"]) + fc * a0 * L["fog"]
    a = a0 * L["opacity"]
    rgb = rgb * L["opacity"]
    if L.get("light"):           # طبقة ضوء (شمس/قمر): تُضاف إضافةً
        return canvas + rgb
    canvas = canvas * (1 - a) + rgb
    if L["glow"] > 0:
        g = cv2.GaussianBlur(rgb, (0, 0), 25 * cam.q)
        canvas = canvas + g * L["glow"]
    return canvas


# ------------------------------------------------------------ الجسيمات ثلاثية الأبعاد
class Particles:
    """غبار، جمر، مطر، ثلج، شرر، نجوم — نقاط حقيقية في فضاء ثلاثي الأبعاد."""

    PRESETS = {
        "dust": dict(n=260, size=2.2, color=(1.0, 0.9, 0.75), vel=(6, -3, 0), jitter=8, alpha=0.45, glow=0.3),
        "embers": dict(n=160, size=2.6, color=(1.0, 0.55, 0.15), vel=(10, -60, 0), jitter=25, alpha=0.9, glow=1.2),
        "snow": dict(n=420, size=2.6, color=(1, 1, 1), vel=(10, 55, 0), jitter=15, alpha=0.85, glow=0.2),
        "rain": dict(n=650, size=1.2, color=(0.75, 0.8, 0.9), vel=(-60, 1400, 0), jitter=40, alpha=0.4, glow=0, streak=True),
        "sparks": dict(n=120, size=1.8, color=(1, 0.8, 0.4), vel=(0, -120, 0), jitter=160, alpha=1.0, glow=1.5),
        "stars": dict(n=500, size=1.4, color=(1, 1, 1), vel=(0, 0, 0), jitter=0, alpha=0.9, glow=0.4, twinkle=True, depth=(4000, 9000)),
        "fireflies": dict(n=60, size=3.0, color=(0.8, 1.0, 0.4), vel=(0, 0, 0), jitter=30, alpha=0.9, glow=1.5, twinkle=True),
    }

    def __init__(self, kind, W, H, seed=1, density=1.0, **over):
        p = dict(self.PRESETS[kind])
        p.update(over)
        self.p = p
        self.kind = kind
        r = np.random.default_rng(seed)
        n = int(p["n"] * density)
        d0, d1 = p.get("depth", (250, 2600))
        z = r.uniform(d0, d1, n)
        spread = 1.6
        self.pos = np.stack([r.uniform(-W * spread, W * spread, n) * z / F,
                             r.uniform(-H * spread, H * spread, n) * z / F, z], 1)
        self.phase = r.uniform(0, 6.28, n)
        self.W, self.H = W, H
        self.r = r

    def render(self, canvas, cam, t):
        p = self.p
        vel = np.array(p["vel"], float)
        P = self.pos.copy()
        P[:, :2] += vel[:2] * t * (P[:, 2:3] / F)
        P[:, 0] += np.sin(t * 0.7 + self.phase) * p["jitter"] * P[:, 2] / F
        P[:, 1] += np.cos(t * 0.5 + self.phase) * p["jitter"] * 0.5 * P[:, 2] / F
        # التفاف: نعيد الجسيمات داخل الحجم
        span_x = self.W * 3.2 * P[:, 2] / F
        span_y = self.H * 3.2 * P[:, 2] / F
        P[:, 0] = (P[:, 0] + span_x / 2 - cam.pos[0]) % span_x - span_x / 2 + cam.pos[0]
        P[:, 1] = (P[:, 1] + span_y / 2 - cam.pos[1]) % span_y - span_y / 2 + cam.pos[1]
        scr, dep = cam.project(P)
        layer = np.zeros_like(canvas)
        sc = cam.q
        col = np.array(p["color"], np.float32)
        for i in range(len(P)):
            if dep[i] < 20:
                continue
            x, y = scr[i]
            if not (-20 < x < cam.W + 20 and -20 < y < cam.H + 20):
                continue
            rad = p["size"] * 900 / dep[i] * sc
            a = p["alpha"]
            if p.get("twinkle"):
                a *= 0.5 + 0.5 * math.sin(t * 3 + self.phase[i] * 5)
            c = tuple(float(v * a) for v in col)
            if p.get("streak"):
                L = vel[1] * 0.035 * 900 / dep[i] * sc
                cv2.line(layer, (int(x), int(y)), (int(x + vel[0] * 0.035 * sc), int(y + L)), c, max(1, int(rad)), cv2.LINE_AA)
            else:
                cv2.circle(layer, (int(x), int(y)), max(1, int(round(rad))), c, -1, cv2.LINE_AA)
        if p["glow"] > 0:
            layer = layer + cv2.GaussianBlur(layer, (0, 0), 6 * sc) * p["glow"] * 2
        return canvas + layer


# ------------------------------------------------------------ أشعة الضوء (God rays)
def god_rays(canvas, src_xy, strength=0.6, threshold=0.85):
    H, W = canvas.shape[:2]
    small = cv2.resize(canvas, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    lum = small.max(axis=2, keepdims=True)
    mask = np.clip((lum - threshold) / (1 - threshold + 1e-6), 0, 1) * small
    cx, cy = src_xy[0] / 4, src_xy[1] / 4
    acc = mask.copy()
    cur = mask
    for i in range(1, 7):
        s = 1 + 0.06 * i
        M = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
        cur = cv2.warpAffine(mask, M, (small.shape[1], small.shape[0]))
        acc += cur * (0.9 ** i)
    acc = cv2.GaussianBlur(acc, (0, 0), 3)
    rays = cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)
    return canvas + rays * strength * 0.35
