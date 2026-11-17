"""المعالجة اللونية السينمائية: تدرج لوني، توهج، حبيبات فيلم، إطار مظلم، أشرطة سينما."""
import numpy as np
import cv2

LOOKS = {
    # shadows, highlights (tint), contrast, saturation
    "teal_orange": dict(sh=(0.0, 0.06, 0.09), hi=(0.08, 0.03, -0.04), contrast=1.12, sat=1.05),
    "warm_epic": dict(sh=(0.05, 0.02, 0.0), hi=(0.1, 0.05, -0.05), contrast=1.1, sat=1.08),
    "cold_night": dict(sh=(0.0, 0.03, 0.10), hi=(-0.02, 0.02, 0.07), contrast=1.08, sat=0.9),
    "bleach": dict(sh=(0.02, 0.02, 0.03), hi=(0.02, 0.02, 0.0), contrast=1.25, sat=0.55),
    "noir": dict(sh=(0, 0, 0), hi=(0, 0, 0), contrast=1.35, sat=0.0),
    "vintage": dict(sh=(0.06, 0.04, 0.0), hi=(0.06, 0.04, -0.06), contrast=0.95, sat=0.75, lift=0.05),
    "none": dict(sh=(0, 0, 0), hi=(0, 0, 0), contrast=1.0, sat=1.0),
}


def grade(img, look="teal_orange", bloom=0.35, grain=0.035, vignette=0.35, letterbox=None, exposure=1.0,
          aberration=0.0, frame_idx=0, flash=0.0, fade=0.0):
    """img: float RGB (يمكن >1). يرجع uint8 جاهز للكتابة."""
    H, W = img.shape[:2]
    x = img * exposure
    if bloom > 0:
        hi = np.clip(x - 0.75, 0, None)
        small = cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        b = cv2.GaussianBlur(small, (0, 0), 8) + cv2.GaussianBlur(small, (0, 0), 24)
        x = x + cv2.resize(b, (W, H)) * bloom
    natural = look == "none"   # للصور المرسومة الجاهزة: نحافظ على ألوانها الأصلية
    if not natural:
        x = x / (1 + x * 0.35) * 1.35  # تحميص ناعم للإضاءات (filmic)
    lk = LOOKS.get(look, LOOKS["none"])
    lum = x.mean(2, keepdims=True)
    if lk.get("sat", 1) != 1:
        x = lum + (x - lum) * lk["sat"]
    w_sh = np.clip(1 - lum * 2, 0, 1)
    w_hi = np.clip(lum * 2 - 1, 0, 1)
    x = x + np.array(lk["sh"], np.float32) * w_sh + np.array(lk["hi"], np.float32) * w_hi
    c = lk.get("contrast", 1)
    x = (x - 0.5) * c + 0.5 + lk.get("lift", 0)
    x = np.clip(x, 0, 1)
    if not natural:
        x = x * x * (3 - 2 * x) * 0.35 + x * 0.65  # منحنى S
    if aberration > 0:
        s = aberration
        M1 = np.float32([[1 + s, 0, -W * s / 2], [0, 1 + s, -H * s / 2]])
        x[..., 0] = cv2.warpAffine(x[..., 0], M1, (W, H), borderMode=cv2.BORDER_REFLECT)
    if vignette > 0:
        ys, xs = np.ogrid[0:H, 0:W]
        d = ((xs - W / 2) / (W / 2)) ** 2 + ((ys - H / 2) / (H / 2)) ** 2
        x = x * (1 - vignette * np.clip(d * 0.55, 0, 1) ** 1.5)[..., None]
    if flash > 0:
        x = x + (1 - x) * flash
    if fade > 0:
        x = x * (1 - fade)
    if grain > 0:
        rng = np.random.default_rng(frame_idx)
        g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
        x = x + g[..., None] * grain * (0.6 + 0.4 * (1 - x))
    x = np.clip(x, 0, 1)
    if letterbox:
        bar = int((H - W / letterbox) / 2) if W / H < letterbox else 0
        if bar > 0:
            x[:bar] = 0
            x[H - bar:] = 0
    return (x * 255 + 0.5).astype(np.uint8)
