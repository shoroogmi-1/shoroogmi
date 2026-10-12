"""«اختيارات القرّاء»: يجمع عدد القراءات المكتملة والإعجابات لكل مقال من عدّاد الموقع،
ويكتب الأعلى تأثيرًا في content/popular.json (يقرؤه build.py لقسم الصفحة الرئيسية).
يُشغَّل يوميًا من GitHub Actions. الدرجة = القراءات + الإعجابات × ٢."""
import datetime
import glob
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://abacus.jasoncameron.dev/get/shoroogmi/"


def count(key):
    for attempt in range(3):
        try:
            req = urllib.request.Request(API + key, headers={"User-Agent": "shoroogmi-popular/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return int(json.load(r).get("value") or 0)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0
        except Exception:
            pass
        time.sleep(1 + attempt)
    return None  # تعذّر الجلب


def main():
    items, failed = [], 0
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "articles", "*.md"))):
        slug = os.path.basename(path)[:-3]
        reads, likes = count(f"reads-{slug}"), count(f"likes-{slug}")
        if reads is None or likes is None:
            failed += 1
            continue
        items.append({"slug": slug, "reads": reads, "likes": likes, "score": reads + 2 * likes})
        time.sleep(0.15)
    if failed > len(items):  # العدّاد لا يستجيب: نُبقي القائمة السابقة كما هي
        print("تعذّر الوصول إلى العدّاد؛ لم تُحدَّث القائمة")
        return
    items.sort(key=lambda x: (-x["score"], -x["reads"], x["slug"]))
    out = {"updated": datetime.date.today().isoformat(), "items": [x for x in items if x["score"] > 0][:20]}
    with open(os.path.join(ROOT, "content", "popular.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("اختيارات القرّاء:", [x["slug"] for x in out["items"][:6]])


if __name__ == "__main__":
    main()
