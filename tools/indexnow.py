"""إرسال روابط المقالات الجديدة أو المعدّلة فورًا إلى محركات البحث التي تدعم IndexNow (Bing وYandex وغيرهما).
يُشغَّل من GitHub Actions بعد بناء الموقع: python3 tools/indexnow.py <ملفات تغيّرت...>
مفتاح الموقع في ملف <KEY>.txt في جذر الموقع (يجب أن يبقى منشورًا)."""
import glob
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "shoroogmi.com"
SITE = f"https://{HOST}/"


def main(changed):
    keys = [f for f in glob.glob(os.path.join(ROOT, "*.txt")) if len(os.path.basename(f)) == 36]
    if not keys:
        print("لا يوجد ملف مفتاح IndexNow")
        return
    key = os.path.basename(keys[0])[:-4]
    urls = []
    for f in changed:
        f = f.strip()
        if f.startswith("content/articles/") and f.endswith(".md"):
            slug = os.path.basename(f)[:-3]
            if os.path.exists(os.path.join(ROOT, f)):
                urls.append(f"{SITE}blog/articles/{slug}.html")
        elif f.startswith("content/en/articles/") and f.endswith(".md"):
            slug = os.path.basename(f)[:-3]
            if os.path.exists(os.path.join(ROOT, f)):
                urls.append(f"{SITE}en/blog/articles/{slug}.html")
        elif f.startswith("content/books/") or f.startswith("content/en/books/"):
            urls += [f"{SITE}books.html", f"{SITE}en/books.html"]
    if not urls:
        print("لا مقالات جديدة أو معدّلة لإرسالها")
        return
    urls = sorted(set(urls + [SITE, f"{SITE}blog/articles.html"]))
    body = json.dumps({"host": HOST, "key": key, "keyLocation": f"{SITE}{key}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow:", r.status, "—", len(urls), "روابط")
    except Exception as e:  # الإرسال تحسين فقط؛ لا يُفشل نشر الموقع
        print("تعذّر إرسال IndexNow:", e)


if __name__ == "__main__":
    main(sys.argv[1:])
