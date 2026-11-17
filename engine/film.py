"""المخرج: يقرأ ملف الفلم (YAML) ويحوّله إلى فيديو MP4 بالصوت والصورة."""
import os
import math
import subprocess
import tempfile
import numpy as np
import cv2
import yaml
from scipy.io import wavfile

from . import world, painter, post, text as T, sfx
from .world import Camera, keyframed, camera_preset, CAMERA_DEFAULT, LAYER_DEFAULT, Particles, god_rays

FORMATS = {"landscape": (1920, 1080), "vertical": (1080, 1920), "square": (1080, 1080)}
TRANS_LEN = {"cut": 0.0, "fade": 0.8, "whip": 0.35, "dip_black": 0.0, "flash": 0.0}


def _load_rgba(path, base_dir):
    p = path if os.path.isabs(path) else os.path.join(base_dir, path)
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None:
        raise FileNotFoundError(p)
    depth = 65535.0 if im.dtype == np.uint16 else 255.0
    im = im.astype(np.float32) / depth
    if im.ndim == 2:
        im = np.stack([im] * 3, 2)
    if im.shape[2] == 3:
        im = np.concatenate([im, np.ones(im.shape[:2] + (1,), np.float32)], 2)
    im = im[..., [2, 1, 0, 3]]
    im[..., :3] *= im[..., 3:4]
    return im


def auto_cutout(rgb_img, box):
    """يفصل الشخص عن الخلفية تلقائيًا (GrabCut) ثم يرمّم الخلفية خلفه.
    box: [x0,y0,x1,y1] بنسب الصورة تقريبًا حول الشخص."""
    h, w = rgb_img.shape[:2]
    s = 900 / max(h, w)
    small = cv2.resize((rgb_img[..., :3] * 255).astype(np.uint8)[..., ::-1], (int(w * s), int(h * s)))
    rect = (int(box[0] * w * s), int(box[1] * h * s), int((box[2] - box[0]) * w * s), int((box[3] - box[1]) * h * s))
    mask = np.zeros(small.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(small, mask, rect, bg, fg, 6, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == 1) | (mask == 3), 1.0, 0.0).astype(np.float32)
    # أكبر جزء متصل فقط
    n, lab, stats, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8))
    if n > 1:
        big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        m = (lab == big).astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    m_full = cv2.resize(m, (w, h))
    m_full = cv2.GaussianBlur(m_full, (0, 0), 1.5)
    # ترميم الخلفية
    hole = (cv2.dilate((m > 0.3).astype(np.uint8), np.ones((15, 15), np.uint8)) * 255)
    inp = cv2.inpaint(small, hole, 12, cv2.INPAINT_TELEA)
    inp_full = cv2.resize(inp, (w, h))[..., ::-1].astype(np.float32) / 255
    hole_full = cv2.GaussianBlur(cv2.resize(hole, (w, h)).astype(np.float32) / 255, (0, 0), 6)[..., None]
    bg_rgb = rgb_img[..., :3] * (1 - hole_full) + inp_full * hole_full
    bg_img = np.concatenate([bg_rgb, np.ones((h, w, 1), np.float32)], 2)
    subj = np.concatenate([rgb_img[..., :3] * m_full[..., None], m_full[..., None]], 2)
    return bg_img.astype(np.float32), subj.astype(np.float32)


class Shot:
    def __init__(self, spec, film, idx):
        self.s = spec
        self.film = film
        self.idx = idx
        self.dur = float(spec.get("duration", 5))
        W, H = film.W0, film.H0
        self.layers = []
        self.env = dict(fog="#000000", sun=None, rays=0, ambient=[], particles=[])
        if "set" in spec:
            layers, env = painter.build_set(spec["set"], W, H)
            self.layers = layers
            self.env.update(env)
        if "photo" in spec:
            img = _load_rgba(spec["photo"], film.base)
            ih, iw = img.shape[:2]
            cover = max(W / iw, H / ih) * spec.get("overscan", 1.22)
            subj = spec.get("subject")
            if subj == "auto" or isinstance(subj, list):
                box = subj if isinstance(subj, list) else spec.get("subject_box", [0.3, 0.1, 0.7, 0.98])
                bg, sb = auto_cutout(img, box)
            elif subj:
                bg, sb = img, _load_rgba(subj, film.base)
            else:
                bg, sb = img, None
            depth = spec.get("depth", 1.0)  # قوة الإحساس ثلاثي الأبعاد
            zb, zs = 2600, 2600 / (1 + 1.4 * depth)
            self.layers.append(dict(name="photo_bg", img=bg, z=zb, scale=cover))
            if sb is not None:
                self.layers.append(dict(name="subject", img=sb, z=zs, scale=cover, motion=spec.get("subject_motion")))
        if "clip" in spec:
            p = spec["clip"] if os.path.isabs(spec["clip"]) else os.path.join(film.base, spec["clip"])
            self.cap = cv2.VideoCapture(p)
            self.clip_fps = self.cap.get(cv2.CAP_PROP_FPS) or 24
            self.clip_frames = []
            while True:
                ok, fr = self.cap.read()
                if not ok:
                    break
                self.clip_frames.append(fr)
        for Ls in spec.get("layers", []):
            d = dict(Ls)
            if "image" in d:
                d["img"] = _load_rgba(d.pop("image"), film.base)
            elif "text" in d:
                d["img"] = T.render_text(d.pop("text"), d.pop("style", "title"), font=d.pop("font", None), q=1.0)
            d.setdefault("name", f"layer{len(self.layers)}")
            d.setdefault("z", 1000)
            self.layers.append(d)
        self.layers.sort(key=lambda L: -L["z"])
        parts = spec.get("particles", self.env.get("particles", []))
        self.particles = []
        for i, p in enumerate(parts):
            if isinstance(p, str):
                p = {"kind": p}
            kind = p.pop("kind")
            self.particles.append(Particles(kind, W, H, seed=idx * 10 + i, **p))
        cam = spec.get("camera", "drift")
        if isinstance(cam, str):
            cam = camera_preset(cam, 1.0)
        elif "move" in cam:
            c = camera_preset(cam["move"], cam.get("amount", 1.0), ease_kind=cam.get("ease", "inout"))
            for k in ("start", "end"):
                if k in cam:
                    c[k] = cam[k]
            cam = c
        self.cam_spec = cam
        self.cam_static = {k: spec[k] for k in ("focus", "aperture", "shake") if k in spec}
        self.texts = []
        for tx in spec.get("text", []) if isinstance(spec.get("text"), list) else ([spec["text"]] if spec.get("text") else []):
            if isinstance(tx, str):
                tx = {"content": tx}
            img = T.render_text(tx["content"], tx.get("style", "title"), size=tx.get("size"), font=tx.get("font"),
                                fill=tx.get("fill"), max_width=film.W0 * 0.82, q=film.q)
            self.texts.append((tx, img))

    # ------------------------------------------------------------------
    def camera_at(self, t):
        p = keyframed(self.cam_spec, t, self.dur, CAMERA_DEFAULT)
        p.update({k: v for k, v in self.cam_static.items()})
        sh = p.get("shake", 0)
        if sh:
            p["x"] += sh * 6 * (math.sin(t * 13.1) + 0.5 * math.sin(t * 29.7))
            p["y"] += sh * 6 * (math.sin(t * 11.3 + 1) + 0.5 * math.sin(t * 23.9))
            p["roll"] += sh * 0.25 * math.sin(t * 7.7)
        for (ft, amt) in self._shake_hits():
            if 0 <= t - ft < 0.6:
                k = (1 - (t - ft) / 0.6) ** 2 * amt
                p["x"] += k * 18 * math.sin(t * 90)
                p["y"] += k * 14 * math.cos(t * 77)
        return p

    def _shake_hits(self):
        return [(h["at"], h.get("amount", 1.0)) for h in self.s.get("hits", [])]

    def render(self, t):
        film = self.film
        W, H, q = film.W, film.H, film.q
        cp = self.camera_at(t)
        cam = Camera(W, H, cp, q)
        canvas = np.zeros((H, W, 3), np.float32)
        fog = painter.hexc(self.env.get("fog", "#000000"))
        if hasattr(self, "clip_frames") and self.clip_frames:
            i = min(len(self.clip_frames) - 1, int(t * self.clip_fps))
            fr = self.clip_frames[i][..., ::-1].astype(np.float32) / 255
            fh, fw = fr.shape[:2]
            z = 1 + cp["z"] / 2000
            s = max(W / fw, H / fh) * z
            M = np.float32([[s, 0, W / 2 - fw * s / 2 - cp["x"] * q * 0.3], [0, s, H / 2 - fh * s / 2 - cp["y"] * q * 0.3]])
            canvas = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        for L in self.layers:
            static = {k: L[k] for k in LAYER_DEFAULT if k in L}
            props = keyframed(L.get("anim"), t, self.dur, {**LAYER_DEFAULT, **static})
            props["light"] = L.get("light", False)
            mo = L.get("motion")
            if mo == "breathe":
                props["scale"] *= 1 + 0.004 * math.sin(t * 2 * math.pi / 3.6)
            elif mo == "bob":
                props["y"] += 4 * math.sin(t * 2 * math.pi / 1.1)
            elif mo == "sway":
                props["roll"] += 0.8 * math.sin(t * 2 * math.pi / 4)
            elif mo == "float":
                props["y"] += 10 * math.sin(t * 2 * math.pi / 5)
                props["yaw"] += 3 * math.sin(t * 2 * math.pi / 7)
            canvas = world.render_layer(canvas, L["img"], props, cam, fog)
        for P in self.particles:
            canvas = P.render(canvas, cam, t)
        rays = self.s.get("rays", self.env.get("rays", 0))
        if rays and self.env.get("sun"):
            sx, sy = self.env["sun"]
            src, _ = cam.project(np.array([[(sx - 0.5) * film.W0 * 8.5, (sy - 0.5) * film.H0 * 8.5, 8500.0]]))
            canvas = god_rays(canvas, src[0], rays)
        elif rays and self.s.get("rays_from"):
            fx, fy = self.s["rays_from"]
            canvas = god_rays(canvas, (fx * W, fy * H), rays, threshold=0.7)
        # البرق
        for ft in self.s.get("lightning", []):
            if 0 <= t - ft < 0.35:
                k = 1 - (t - ft) / 0.35
                fl = k * (0.6 + 0.4 * (math.sin((t - ft) * 60) > 0))
                canvas = canvas * (1 + fl * 1.5) + fl * 0.25
        return canvas

    def overlay_text(self, frame_u8, t):
        if not self.texts:
            return frame_u8
        out = frame_u8.astype(np.float32) / 255
        W, H = self.film.W, self.film.H
        for tx, img in self.texts:
            at = tx.get("at", 0.5)
            dur = tx.get("dur", self.dur - at - 0.3)
            op, dy, sc, blur = T.text_anim(t, at, dur, tx.get("fade_in", 0.9), tx.get("fade_out", 0.8), tx.get("anim", "rise"))
            if op <= 0:
                continue
            im = img
            if sc != 1:
                im = cv2.resize(im, (int(im.shape[1] * sc), int(im.shape[0] * sc)))
            if blur > 0.5:
                k = int(blur * 2) * 2 + 1
                im = cv2.GaussianBlur(im, (k, k), blur)
            h, w = im.shape[:2]
            pos = tx.get("pos", "center")
            lb = self.film.letterbox
            bar = int((H - W / lb) / 2) if lb and W / H < lb else 0
            y = {"center": H / 2 - h / 2, "lower": H - bar - h - H * 0.06, "top": bar + H * 0.06,
                 "upper": H * 0.28 - h / 2}.get(pos, H / 2 - h / 2) + dy * self.film.q
            x = W / 2 - w / 2
            x0, y0 = int(x), int(y)
            xs0, ys0 = max(0, -x0), max(0, -y0)
            x1, y1 = min(W, x0 + w), min(H, y0 + h)
            if x1 <= max(0, x0) or y1 <= max(0, y0):
                continue
            crop = im[ys0:ys0 + (y1 - max(0, y0)), xs0:xs0 + (x1 - max(0, x0))]
            reg = out[max(0, y0):y1, max(0, x0):x1]
            a = crop[..., 3:4] * op
            reg[:] = reg * (1 - a) + crop[..., :3] * op
        return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


class Film:
    def __init__(self, path, quality=None, only=None):
        self.path = path
        self.base = os.path.dirname(os.path.abspath(path))
        self.spec = yaml.safe_load(open(path, encoding="utf-8"))
        sp = self.spec
        self.W0, self.H0 = FORMATS.get(sp.get("format", "landscape"), FORMATS["landscape"])
        self.q = float(quality if quality is not None else sp.get("quality", 1.0))
        self.W, self.H = int(self.W0 * self.q) // 2 * 2, int(self.H0 * self.q) // 2 * 2
        self.fps = sp.get("fps", 24)
        self.look = sp.get("look", "teal_orange")
        self.letterbox = sp.get("letterbox", 2.39 if sp.get("format", "landscape") == "landscape" else None)
        shots = sp["shots"]
        if only is not None:
            shots = [shots[i] for i in only]
        self.shots = [Shot(s, self, i) for i, s in enumerate(shots)]
        # الجدول الزمني
        self.starts = []
        t = 0.0
        for i, sh in enumerate(self.shots):
            self.starts.append(t)
            tr = sh.s.get("transition", "cut") if i < len(self.shots) - 1 else "cut"
            t += sh.dur - TRANS_LEN.get(tr, 0)
        self.total = self.starts[-1] + self.shots[-1].dur

    def frame(self, T_):
        active = [(i, sh) for i, sh in enumerate(self.shots) if self.starts[i] <= T_ < self.starts[i] + sh.dur]
        if not active:
            active = [(len(self.shots) - 1, self.shots[-1])]
        i, sh = active[0]
        lt = T_ - self.starts[i]
        flash = fade = 0.0
        if len(active) > 1:  # تداخل انتقال
            j, sh2 = active[1]
            tr = sh.s.get("transition", "fade")
            ov = TRANS_LEN.get(tr, 0.8)
            p = (T_ - self.starts[j]) / ov
            A = sh.render(lt)
            B = sh2.render(T_ - self.starts[j])
            if tr == "whip":
                k = int(60 * self.q * math.sin(math.pi * p)) * 2 + 1
                A = cv2.blur(A, (k, 1))
                B = cv2.blur(B, (k, 1))
            img = A * (1 - p) + B * p
            look = sh2.s.get("look", self.look) if p > 0.5 else sh.s.get("look", self.look)
            u8 = post.grade(img, look, **self._post(), frame_idx=int(T_ * self.fps))
            u8 = sh.overlay_text(u8, lt)
            return sh2.overlay_text(u8, T_ - self.starts[j])
        img = sh.render(lt)
        tr_out = sh.s.get("transition", "cut")
        tail = sh.dur - lt
        if tr_out == "dip_black" and tail < 0.5:
            fade = 1 - tail / 0.5
        if i > 0:
            prev = self.shots[i - 1].s.get("transition", "cut")
            if prev == "dip_black" and lt < 0.5:
                fade = 1 - lt / 0.5
            if prev == "flash" and lt < 0.4:
                flash = (1 - lt / 0.4) ** 2
        if i == 0 and lt < self.spec.get("fade_in", 0.8):
            fade = max(fade, 1 - lt / self.spec.get("fade_in", 0.8))
        if i == len(self.shots) - 1 and tail < self.spec.get("fade_out", 1.0):
            fade = max(fade, 1 - tail / self.spec.get("fade_out", 1.0))
        u8 = post.grade(img, sh.s.get("look", self.look), **self._post(), frame_idx=int(T_ * self.fps), flash=flash, fade=fade)
        return sh.overlay_text(u8, lt)

    def _post(self):
        sp = self.spec
        return dict(bloom=sp.get("bloom", 0.35), grain=sp.get("grain", 0.03), vignette=sp.get("vignette", 0.35),
                    letterbox=self.letterbox)

    # ------------------------------------------------------------------ الصوت
    def mix_audio(self, out_wav):
        SR = sfx.SR
        n = int((self.total + 2) * SR)
        bus = np.zeros((n, 2), np.float32)
        voice_env = np.zeros(n, np.float32)

        def place(x, t0, gain=1.0, track=None):
            s = int(max(t0, 0) * SR)
            e = min(n, s + len(x))
            if s < n:
                bus[s:e] += x[: e - s] * gain
                if track is not None:
                    track[s:e] = np.maximum(track[s:e], np.abs(x[: e - s]).mean(1) > 0.01)

        sp = self.spec
        mus = sp.get("music")
        music = np.zeros_like(bus)
        if mus:
            args = dict(mus.get("args", {}))
            args["dur"] = self.total + 1
            x = sfx.make(mus.get("sound", "pad"), **args)
            music[: min(n, len(x))] += x[:n] * mus.get("volume", 0.35)
            for extra in mus.get("layers", []):
                a2 = dict(extra.get("args", {}))
                a2.setdefault("dur", self.total + 1)
                x2 = sfx.make(extra["sound"], **a2)
                s = int(extra.get("at", 0) * SR)
                e = min(n, s + len(x2))
                music[s:e] += x2[: e - s] * extra.get("volume", 0.3)
        for i, sh in enumerate(self.shots):
            t0 = self.starts[i]
            amb = sh.s.get("ambience", sh.env.get("ambient", []))
            for a in amb:
                name, vol = (a, 0.22) if isinstance(a, str) else (a["name"], a.get("volume", 0.22))
                x = sfx.make(name, dur=sh.dur + 1.0)
                place(x, t0 - 0.3, vol)
            tr = sh.s.get("transition", "cut")
            if tr == "whip" and i < len(self.shots) - 1:
                place(sfx.make("whoosh", dur=0.9), t0 + sh.dur - 0.6, 0.55)
            for c in sh.s.get("sfx", []):
                c = {"name": c} if isinstance(c, str) else c
                args = dict(c.get("args", {}))
                x = sfx.make(c["name"], **args)
                at = c.get("at", 0)
                if c.get("ends_at") is not None:  # للـ riser: ينتهي عند لحظة الضربة
                    at = c["ends_at"] - len(x) / SR + 0.0
                place(x, t0 + at, c.get("volume", 0.7))
            for h in sh.s.get("hits", []):
                place(sfx.make(h.get("sound", "impact")), t0 + h["at"], h.get("volume", 0.8))
            for ft in sh.s.get("lightning", []):
                place(sfx.make("thunder"), t0 + ft + 0.15, 0.7)
            says = sh.s.get("say")
            if says:
                from . import voice
                for k, sy in enumerate(says if isinstance(says, list) else [says]):
                    tmp = os.path.join(tempfile.gettempdir(), f"say_{i}_{k}.wav")
                    voice.say(sy["text"], tmp, sy.get("voice", sp.get("voice", "man")))
                    sr2, v = wavfile.read(tmp)
                    v = v.astype(np.float32) / 32768
                    place(v, t0 + sy.get("at", 0.5), sy.get("volume", 1.0), voice_env)
        # خفض الموسيقى تحت صوت الراوي
        from scipy.ndimage import gaussian_filter1d
        duck = gaussian_filter1d(voice_env, SR * 0.25) if voice_env.any() else voice_env
        duck = np.clip(duck * 1.5, 0, 1)
        music *= (1 - 0.55 * duck)[:, None]
        mix = bus + music
        # تلاشي بداية ونهاية + محدد
        fi = int(0.5 * SR)
        mix[:fi] *= np.linspace(0, 1, fi)[:, None]
        e = int(self.total * SR)
        fo = int(1.2 * SR)
        mix[e - fo:e] *= np.linspace(1, 0, fo)[:, None]
        mix[e:] = 0
        mix = np.tanh(mix * 1.1) * 0.9
        wavfile.write(out_wav, SR, (mix[:e] * 32767).astype(np.int16))

    # ------------------------------------------------------------------ الإخراج
    def render(self, out_mp4, progress=True):
        tmpv = out_mp4 + ".video.mp4"
        tmpa = out_mp4 + ".audio.wav"
        self.mix_audio(tmpa)
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{self.W}x{self.H}",
               "-r", str(self.fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
               "-pix_fmt", "yuv420p", tmpv]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        nf = int(self.total * self.fps)
        for f in range(nf):
            pr.stdin.write(self.frame(f / self.fps).tobytes())
            if progress and f % self.fps == 0:
                print(f"\r{f}/{nf} إطار", end="", flush=True)
        pr.stdin.close()
        pr.wait()
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmpv, "-i", tmpa, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out_mp4], check=True)
        os.remove(tmpv)
        os.remove(tmpa)
        print("\nتم:", out_mp4)
        return out_mp4

    def still(self, t, out_png):
        cv2.imwrite(out_png, self.frame(t)[..., ::-1])
        return out_png
