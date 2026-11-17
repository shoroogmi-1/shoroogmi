#!/usr/bin/env python3
"""استوديو الفلم — نقطة التشغيل الوحيدة.

  python3 studio.py render films/demo/film.yaml            # إخراج الفلم كاملًا
  python3 studio.py render films/demo/film.yaml --q 0.5    # معاينة سريعة بنصف الدقة
  python3 studio.py still  films/demo/film.yaml 3.5        # لقطة ثابتة عند الثانية 3.5
  python3 studio.py shot   films/demo/film.yaml 2          # إخراج المشهد رقم 2 فقط (يبدأ من 0)
  python3 studio.py sounds                                 # تصدير مكتبة الأصوات للاستماع
  python3 studio.py voices "نَصٌّ مَشْكُولٌ"                 # تجربة كل الأصوات
  python3 studio.py sets                                   # صور معاينة للعوالم الجاهزة
  python3 studio.py fonts                                  # لوحة معاينة الخطوط

  ── أوامر أي فيلم جديد بمستوى سليماني (إلزامية) ──
  python3 studio.py new   <slug> [--title "..."]           # ينشئ films/<slug>/ من نموذج سليماني (scene.py + story.yaml)
  python3 studio.py plan  films/<slug>/story.yaml          # يفحص الخطة بقواعد الكتابين وقاعدة محاكاة الواقع
  python3 studio.py qa    films/<slug>/<out>.mp4 [story]   # يفحص الإخراج: الدقة، 60 إطارًا، الصوت، العلوّ، المدة
  python3 studio.py model                                  # يعرض فيلم النموذج ومكانه
"""
import os
import sys
import argparse
import subprocess
import numpy as np
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from engine import film, sfx, painter  # noqa: E402

MODEL = "soleimani_mckee"   # فيلم النموذج: الحد الأدنى للمستوى


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--q", type=float, default=None, help="الدقة: 1 كاملة، 0.5 معاينة")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.cmd == "render":
        f = film.Film(a.args[0], quality=a.q)
        out = a.out or os.path.splitext(a.args[0])[0] + ".mp4"
        print(f"المدة {f.total:.1f} ث — {f.W}x{f.H} @ {f.fps}fps")
        f.render(out)
    elif a.cmd == "shot":
        idx = [int(x) for x in a.args[1:]]
        f = film.Film(a.args[0], quality=a.q, only=idx)
        out = a.out or os.path.splitext(a.args[0])[0] + f"_shot{'_'.join(map(str, idx))}.mp4"
        f.render(out)
    elif a.cmd == "still":
        f = film.Film(a.args[0], quality=a.q)
        t = float(a.args[1]) if len(a.args) > 1 else 1.0
        out = a.out or os.path.splitext(a.args[0])[0] + f"_t{t}.png"
        print(f.still(t, out))
    elif a.cmd == "sounds":
        d = os.path.join(ROOT, "sounds")
        os.makedirs(d, exist_ok=True)
        lines = ["# مكتبة الأصوات السينمائية\n", "| الاسم | الوصف | ملف |", "|---|---|---|"]
        for name, (fn, desc) in sfx.LIBRARY.items():
            kw = {"dur": 8.0} if name in ("drone", "pad", "wind", "rain", "fire", "crowd", "park") else {}
            x = sfx.make(name, **kw)
            tmp = f"/tmp/{name}.wav"
            wavfile.write(tmp, sfx.SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-c:a", "libmp3lame", "-b:a", "128k", f"{d}/{name}.mp3"], check=True)
            lines.append(f"| `{name}` | {desc} | [استمع](./{name}.mp3) |")
        open(os.path.join(d, "README.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("تم تصدير", len(sfx.LIBRARY), "صوتًا إلى", d)
    elif a.cmd == "voices":
        from engine import voice
        text = a.args[0] if a.args else "فِي لَيْلَةٍ هَادِئَةٍ، خَرَجَ الْفَتَى يَبْحَثُ عَنِ الْحَقِيقَةِ."
        d = os.path.join(ROOT, "voices", "samples")
        os.makedirs(d, exist_ok=True)
        for v in voice.VOICES:
            w = f"/tmp/voice_{v}.wav"
            voice.say(text, w, v)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", w, "-c:a", "libmp3lame", "-b:a", "128k", f"{d}/{v}.mp3"], check=True)
            print(v, "→", f"{d}/{v}.mp3")
    elif a.cmd == "sets":
        import cv2
        from engine.world import Camera, CAMERA_DEFAULT, render_layer
        from engine import post
        d = os.path.join(ROOT, "previews")
        os.makedirs(d, exist_ok=True)
        for name in painter.SETS:
            layers, env = painter.build_set(name, 1920, 1080)
            cam = Camera(960, 540, dict(CAMERA_DEFAULT), 0.5)
            c = np.zeros((540, 960, 3), np.float32)
            for L in sorted(layers, key=lambda L: -L["z"]):
                props = {**{k: L.get(k, v) for k, v in film.LAYER_DEFAULT.items()}, "light": L.get("light", False)}
                c = render_layer(c, L["img"], props, cam, painter.hexc(env["fog"]))
            cv2.imwrite(f"{d}/set_{name}.jpg", post.grade(c, "teal_orange", letterbox=None)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 85])
            print(name)
    elif a.cmd == "fonts":
        import cv2
        from engine import text as T
        rows = []
        for key in T.FONTS:
            sample = "The Last Light" if key in ("cinzel", "cinzel_deco", "bebas", "anton", "oswald", "playfair", "cormorant") else "الضوء الأخير"
            im = T.render_text(f"{sample}", "subtitle", font=key, size=90, fill="#f3e6c8")
            lab = T.render_text(key, "subtitle", font="cairo", size=34, fill="#c9a24a")
            canvas = np.zeros((170, 1400, 3), np.float32) + 0.05
            for img, x in ((im, 380), (lab, 10)):
                ys_, xs_ = np.nonzero(img[..., 3] > 0.02)
                img = img[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]
                h, w = img.shape[:2]
                h2, w2 = min(h, 170), min(w, 1400 - x)
                y = (170 - h2) // 2
                reg = canvas[y:y + h2, x:x + w2]
                reg[:] = reg * (1 - img[:h2, :w2, 3:4]) + img[:h2, :w2, :3]
            rows.append(canvas)
        out = np.clip(np.concatenate(rows, 0), 0, 1)
        cv2.imwrite(os.path.join(ROOT, "previews", "fonts.jpg"), (out[..., ::-1] * 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("previews/fonts.jpg")
    elif a.cmd == "new":
        import shutil
        slug = a.args[0]
        src, dst = os.path.join(ROOT, "films", MODEL), os.path.join(ROOT, "films", slug)
        os.makedirs(dst, exist_ok=False)
        code = open(os.path.join(src, "scene.py"), encoding="utf-8").read()
        code = code.replace('"soleimani_mckee"', f'"{slug}"').replace("soleimani_mckee.mp4", f"{slug}.mp4")
        open(os.path.join(dst, "scene.py"), "w", encoding="utf-8").write(code)
        shutil.copy(os.path.join(ROOT, "templates", "story.yaml"), os.path.join(dst, "story.yaml"))
        print(f"تم إنشاء films/{slug}/ من النموذج.\nالخطوات الإلزامية:\n"
              f"  1) املأ films/{slug}/story.yaml (أو انسخ سيناريوها الجاهز في narration إن كان mode: script)\n"
              f"  2) python3 studio.py plan films/{slug}/story.yaml  ← حتى لا يبقى خطأ\n"
              f"  3) ابحث عن مراجع حقيقية وأبعاد، ثم عدّل اللقطات في scene.py (اللوحات، الشخصيات، المركبات)\n"
              f"  4) python3 films/{slug}/scene.py x t1 t2 t3 t4  ← لوحة فحص وانظر إليها\n"
              f"  5) python3 films/{slug}/scene.py  ← إخراج كامل\n"
              f"  6) python3 studio.py qa .cache/{slug}/{slug}.mp4 films/{slug}/story.yaml")
    elif a.cmd == "plan":
        from engine import story
        sys.exit(story.check_plan(a.args[0]))
    elif a.cmd == "qa":
        from engine import story
        sys.exit(story.check_video(a.args[0], a.args[1] if len(a.args) > 1 else None))
    elif a.cmd == "model":
        print(f"النموذج: films/{MODEL}/  (scene.py، story.yaml، model.mp4)\nالمرجع البصري: films/{MODEL}/model.mp4")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
