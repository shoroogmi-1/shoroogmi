"""يولّد صفحات الموقع بالعربية (في جذر الموقع) وبالإنجليزية (في مجلد en/).

التشغيل:  python3 build.py

- المقالات: ملف لكل مقال في content/articles/، وترجمته الإنجليزية بالاسم نفسه في content/en/articles/ (انظري README.md).
- الكتب ومحطات جواز سفر والتواصل: قوائم داخل هذا الملف (ابحثي عن BOOKS و STATIONS و CONTACTS).
  النص الذي يختلف بين اللغتين يُكتب زوجًا: ("النص العربي", "English text").
- بعد أي تعديل شغّلي الأمر أعلاه لتحديث ملفات HTML.
"""
import hashlib
import html as html_lib
import json
import glob
import os
import re
from urllib.parse import quote as url_quote, unquote

import yaml  # يُثبَّت في GitHub Actions مع أداة الصوت

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ("ar", "en")


def pick(lang, v):
    """A value is either the same in both languages, or a pair ("عربي", "English")."""
    return v[LANGS.index(lang)] if isinstance(v, tuple) else v


def out_path(lang, path):
    return path if lang == "ar" else f"en/{path}"


SITE = "https://shoroogmi.com/"
SITEMAP = []  # (url, {lang: url}, lastmod) تُملأ أثناء البناء


# ---------- نصوص الصفحات من content/data/*.yml (تُعدَّل من لوحة التحكم) ----------
def data(name):
    return yaml.safe_load(open(os.path.join(ROOT, "content", "data", f"{name}.yml"), encoding="utf-8")) or {}


def rich(x):
    """في ملفات البيانات: **كلمة** غامقة، و[نص](رابط) رابط."""
    x = re.sub(r"&(?!#?\w+;)", "&amp;", str(x or ""))
    x = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", x)
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{m.group(2)}"'
                  + ("" if m.group(2).startswith("mailto:") else ' target="_blank" rel="noopener"') + f">{m.group(1)}</a>", x)


def tx(d, ar="ar", en="en"):
    """زوج (عربي، إنجليزي) من حقلين؛ إن خلت الإنجليزية تُستعمل العربية."""
    d = d or {}
    return rich(d.get(ar)), rich(d.get(en) or d.get(ar))


HOME = {k: tx(v) for k, v in data("home").items() if isinstance(v, dict)}
PASSPORT = data("passport")
JOURNEYS = data("journeys")
CONTACT = data("contact")
LEGAL = data("legal")


def share_btn(lang, path, title, extra_class=""):
    """زر «شارك»: يفتح قائمة المشاركة في الجوال، أو ينسخ الرابط في الحاسوب."""
    t = lambda a, e: a if lang == "ar" else e
    url = SITE + out_path(lang, path)
    title = re.sub(r"<[^>]+>", "", title).replace('"', "&quot;")
    return (f'<button class="share-btn{extra_class}" type="button" data-url="{url}" data-title="{title}">'
            f'<span aria-hidden="true">🔗</span> {t("شارك الرابط", "Share the link")}</button>')


def page(lang, path, key, title, body, desc, alt=None, icon=None, image=None, og_type="website", lastmod=None, jsonld=None):
    """path is relative to the language's root; alt is the same page in the other language
    (defaults to path)."""
    t = lambda a, e: a if lang == "ar" else e
    out = out_path(lang, path)
    p = "../" * out.count("/")          # to the site root (assets)
    h = p + ("" if lang == "ar" else "en/")  # to this language's home
    other = "en" if lang == "ar" else "ar"
    switch = p + out_path(other, alt or path)

    # روابط مطلقة لمحركات البحث ومعاينات المشاركة
    def abs_url(lng, pth):
        pth = out_path(lng, pth)
        return SITE + (pth[:-len("index.html")] if pth.endswith("index.html") else pth)
    canonical = abs_url(lang, path)
    other_abs = abs_url(other, alt or path)
    og_img = SITE + (image or "assets/images/og-default.jpg")
    SITEMAP.append((canonical, {lang: canonical, other: other_abs} if not alt else {lang: canonical}, lastmod))
    seo = (f'  <link rel="canonical" href="{canonical}">\n'
           f'  <link rel="alternate" hreflang="{lang}" href="{canonical}">\n'
           + (f'  <link rel="alternate" hreflang="{other}" href="{other_abs}">\n' if not alt else "")
           + f'  <meta property="og:type" content="{og_type}">\n'
           f'  <meta property="og:site_name" content="{t("شروق المحمادي", "Shoroog Almehmadi")}">\n'
           f'  <meta property="og:title" content="{title}">\n'
           f'  <meta property="og:description" content="{desc}">\n'
           f'  <meta property="og:url" content="{canonical}">\n'
           f'  <meta property="og:image" content="{og_img}">\n'
           f'  <meta property="og:locale" content="{t("ar_SA", "en_US")}">\n'
           f'  <meta name="twitter:card" content="summary_large_image">\n')
    if jsonld:
        seo += f'  <script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>\n'

    def act(k):
        return ' class="active"' if k == key or (k == "blog" and key.startswith("blog")) else ""

    def sub(k):
        return ' class="active"' if k == key else ""

    html = f"""<!doctype html>
<html lang="{lang}" dir="{t("rtl", "ltr")}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
{f'  <link rel="icon" type="image/png" href="{p}{icon}">{chr(10)}  <link rel="apple-touch-icon" href="{p}{icon}">' if icon else
 f'  <link rel="icon" href="{p}favicon.ico" sizes="48x48">{chr(10)}  <link rel="icon" type="image/svg+xml" href="{p}assets/images/favicon.svg">{chr(10)}  <link rel="apple-touch-icon" href="{p}assets/images/apple-touch-icon.png">{chr(10)}  <link rel="manifest" href="{p}site.webmanifest">'}
  <meta name="theme-color" content="#fbc93d">
  <meta name="description" content="{desc}">
{seo}  <script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Readex+Pro:wght@300;400;500;600;700&family=Amiri+Quran&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p}assets/styles.css?v={ASSET_V["styles.css"]}">
</head>
<body>
  <header class="site-header">
    <div class="container nav">
      <a href="{h}index.html" class="logo"><span class="logo-sun" aria-hidden="true"></span>{t("شروق المحمادي", "Shoroog Almehmadi")}</a>
      <a class="search-link{" active" if key == "search" else ""}" href="{h}search.html" aria-label="{t("ابحث في الموقع", "Search the site")}">🔍</a>
      <button class="menu-toggle" aria-label="{t("فتح القائمة", "Open menu")}" aria-expanded="false">☰</button>
      <nav class="nav-links" aria-label="{t("القائمة الرئيسية", "Main menu")}">
        <a href="{h}index.html"{act("home")}>{t("مُشعشعة", "Radiant")}</a>
        <a href="{h}sira.html"{act("sira")}>{t("جواز سفر", "Passport")}</a>
        <div class="has-sub">
          <a href="{h}blog/index.html"{act("blog")}>{t("سجل الرحلات", "Travel Log")} <span class="caret" aria-hidden="true">▾</span></a>
          <div class="sub">
            <a href="{h}blog/articles.html"{sub("blog-articles")}>{t("رحلات طويلة", "Long Journeys")}</a>
          </div>
        </div>
        <a href="{h}books.html"{act("books")}>{t("أمتعة السفر", "Luggage")}</a>
        <a href="{h}testimonials.html"{act("testimonials")}>{t("ما قاله المسافرون", "Reviews")}</a>
        <a href="{h}contact.html"{act("contact")}>{t("برج المراقبة", "Control Tower")}</a>
        <a class="lang-switch" href="{switch}" hreflang="{other}" lang="{other}">{t("English", "العربية")}</a>
        <button class="theme-toggle" aria-label="{t("تبديل الوضع الليلي", "Toggle dark mode")}">🌙</button>
      </nav>
    </div>
  </header>

  <main>
{body}
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p class="footer-name">{t("شروق المحمادي", "Shoroog Almehmadi")}</p>
      <nav class="footer-links" aria-label="{t("روابط التذييل", "Footer links")}">
        <a href="{h}sira.html">{t("جواز سفر", "Passport")}</a>
        <a href="{h}blog/articles.html">{t("رحلات طويلة", "Long Journeys")}</a>
        <a href="{h}books.html">{t("أمتعة السفر", "Luggage")}</a>
        <a href="{h}testimonials.html">{t("ما قاله المسافرون", "What Travelers Said")}</a>
        <a href="{h}contact.html">{t("برج المراقبة", "Control Tower")}</a>
      </nav>
      <p class="legal-links"><a href="{h}privacy.html">{t("سياسة الخصوصية", "Privacy Policy")}</a> · <a href="{h}terms.html">{t("شروط الاستخدام", "Terms of Use")}</a></p>
      <p class="copy">© <span class="year"></span> {t("جميع الحقوق محفوظة", "All rights reserved")}</p>
    </div>
  </footer>

  <script src="{p}assets/script.js?v={ASSET_V["script.js"]}"></script>
</body>
</html>
"""
    full = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)


def page_head(eyebrow, heading, lead, crumbs="", extra="", logo=""):
    return f"""    <section class="page-hero">
      <div class="clouds" aria-hidden="true"><span class="cloud c1"></span><span class="cloud c2"></span></div>
      <div class="container">
{crumbs or f'        <p class="eyebrow">{eyebrow}</p>{chr(10)}'}{logo}        <h1>{heading}</h1>
        <p class="lead">{lead}</p>
{extra}      </div>
    </section>
"""


# تسجيلات المقالات بصوت حامد (تصنعها tools/make_audio.py في GitHub Actions)
AUDIO_DIR = os.path.join(ROOT, "assets", "audio")
_audio_manifest_path = os.path.join(AUDIO_DIR, "manifest.json")
AUDIO_V = json.load(open(_audio_manifest_path, encoding="utf-8")) if os.path.exists(_audio_manifest_path) else {}


def audio_player(lang, slug):
    """مشغّل التسجيل في صفحة المقال العربي، إن وُجد تسجيل؛ وإلا تُستعمل قراءة المتصفح."""
    if lang != "ar" or not os.path.exists(os.path.join(AUDIO_DIR, f"{slug}.mp3")):
        return ""
    return f"""        <div class="audio-player">
          <audio controls preload="none" src="../../assets/audio/{slug}.mp3?v={AUDIO_V.get(slug, "")}"></audio>
          <button class="audio-rate" type="button">السرعة ١×</button>
        </div>"""


def LISTEN_HTML(t):
    return f"""        <div class="listen" hidden>
          <button class="listen-btn" type="button"><span class="listen-icon" aria-hidden="true">🎧</span> <span class="listen-label">{t("استمع للمقال", "Listen to the article")}</span></button>
          <button class="listen-stop" type="button" hidden>⏹ {t("إيقاف", "Stop")}</button>
          <button class="listen-rate" type="button" hidden>{t("السرعة ١×", "Speed 1×")}</button>
          <span class="listen-status" role="status"></span>
        </div>"""


# «اختيارات القرّاء»: قائمة يكتبها tools/popular.py يوميًا من عدّاد القراءات والإعجابات
_pop = os.path.join(ROOT, "content", "popular.json")
POPULAR = json.load(open(_pop, encoding="utf-8")).get("items", []) if os.path.exists(_pop) else []

# شعار الزاوية ٣٦
ZAWIYA_LOGO = "assets/images/zawiya-36-logo.png"

# شريك الزاوية ٣٦
CREATIVE_FORUM = "https://creativeforum.sa/%d8%b7%d9%84%d8%a8-%d8%a7%d8%b3%d8%aa%d8%b4%d8%a7%d8%b1%d8%a9/"

# بصمة لكل ملف تنسيق/برمجة تُضاف إلى رابطه، فيحمّل المتصفح النسخة الجديدة فور أي تعديل بدل نسخته المخزّنة
ASSET_V = {f: hashlib.md5(open(os.path.join(ROOT, "assets", f), "rb").read()).hexdigest()[:8] for f in ("styles.css", "script.js")}


# ---------- shared content ----------

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def ar(n):
    return str(n).translate(AR_DIGITS)


AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
EN_MONTHS = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"]


def fmt_date(lang, iso):
    y, m, d = (int(x) for x in iso.split("-"))
    if lang == "ar":
        return f"{ar(d)} {AR_MONTHS[m - 1]} {ar(y)}"
    return f"{EN_MONTHS[m - 1]} {d}, {y}"


def fmt_time(lang, hhmm):
    h, m = (int(x) for x in hhmm.split(":"))
    if lang == "ar":
        return f"{ar(h % 12 or 12)}:{ar(f'{m:02d}')} {'ص' if h < 12 else 'م'}"
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def word_count(blocks):
    return sum(len(t.split()) for k, t in blocks if k != "img")


def read_time(lang, blocks):
    n = max(1, round(word_count(blocks) / 200))
    if lang == "en":
        return f"{n} min"
    if n == 1:
        return "دقيقة"
    if n == 2:
        return "دقيقتان"
    return f"{ar(n)} {'دقائق' if n <= 10 else 'دقيقة'}"


# أسماء حقول الترويسة بالعربية (والإنجليزية مقبولة أيضاً)
FIELDS = {"العنوان": "title", "التاريخ": "date", "التصنيف": "tag"}
# «الملخص» صار اختياريًا: المقالات الجديدة تكتفي بـ«اقتباس»، وهو الذي يظهر في بطاقة المقال
OPTIONAL_FIELDS = {"الملخص": "excerpt", "Excerpt": "excerpt", "الوقت": "time", "النوع": "kind", "اقتباس": "quote", "Quote": "quote"}  # الوقت بنظام ٢٤ ساعة مثل 21:30، والنوع «قصيدة» يعرض الأبيات في المنتصف
# ترويسة الترجمة الإنجليزية (التاريخ والتصنيف والوقت تؤخذ من المقال العربي)
EN_FIELDS = {"Title": "title"}

# تصنيفات «رحلات طويلة» بالترتيب الذي تظهر به أزرار الفرز. «التصنيف» في كل مقال يجب أن يكون واحدًا منها.
# تصنيفات «رحلات طويلة» من content/data/journeys.yml، بالترتيب الذي تظهر به أزرار الفرز
CATEGORIES = [str(c["ar"]).strip() for c in JOURNEYS.get("categories", []) if c.get("ar")]
# «الزاوية ٣٦» صارت تصنيفًا من تصنيفات رحلات طويلة (صفحتها القديمة تحوّل إليه)
ZAWIYA_TAG = "الزاوية ٣٦"
# اسم كل تصنيف في النسخة الإنجليزية
CATEGORIES_EN = {str(c["ar"]).strip(): str(c.get("en") or c["ar"]).strip() for c in JOURNEYS.get("categories", []) if c.get("ar")}
CATEGORIES_EN.setdefault(ZAWIYA_TAG, "Corner 36")


IMG_RE = re.compile(r"!\[([^\]]*)\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
# سطر وسائط في المقال: صورة أو فيديو أو صوت ![وصف](ملف) — ملف للتحميل [وصف](ملف) — أو رابط يوتيوب وحده
MEDIA_RE = re.compile(r"(!?)\[([^\]]*)\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
YT_RE = re.compile(r"https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([\w-]{11})\S*")
VIDEO_EXT = (".mp4", ".webm", ".mov", ".m4v")
SOUND_EXT = (".mp3", ".m4a", ".wav", ".ogg")
# مجلدات الوسائط: assets/media (للصور والفيديو والملفات) و assets/images (القديم)
MEDIA_DIRS = ("assets/media", "assets/images")


def media_name(src, dirs=MEDIA_DIRS):
    """اسم الملف داخل مجلد الوسائط: لوحة التحكم تكتب /assets/media/x.jpg، والكتابة اليدوية x.jpg."""
    src = unquote(src).lstrip("/")
    for d in dirs:
        if src.startswith(d + "/"):
            return src[len(d) + 1:]
    return src


def media_path(src):
    """مسار ملف الوسائط داخل الموقع، أو None إن لم يوجد."""
    src = media_name(src)
    for d in MEDIA_DIRS:
        if os.path.exists(os.path.join(ROOT, d, src)):
            return f"{d}/{src}"
    return None


def is_media_line(line):
    line = line.strip("<>")
    m = MEDIA_RE.fullmatch(line)
    if m:
        if YT_RE.fullmatch(m.group(3)):
            return True
        return m.group(1) == "!" or "." in m.group(3).rsplit("/", 1)[-1] and "://" not in m.group(3)
    return bool(YT_RE.fullmatch(line))


# مفاتيح ترويسة لوحة التحكم (Pages CMS) بالإنجليزية ← أسماء الحقول الداخلية
FM_KEYS = {"title": "title", "date": "date", "category": "tag", "excerpt": "excerpt", "quote": "quote", "time": "time",
           "kind": "kind", "subtitle": "sub", "publisher": "pub", "year": "year", "store": "url", "front": "front",
           "back": "back", "pdf": "pdf", "order": "order"}


def inline_md(x):
    """ما يكتبه محرّر لوحة التحكم داخل الفقرة: **غامق** و*مائل* و[رابط](https://…)، وإزالة رموز الهروب \\."""
    x = re.sub(r"\\([\\`*_{}\[\]()#+\-.!>~|])", r"\1", x)
    x = re.sub(r"\*\*([^*]+?)\*\*", r"<strong>\1</strong>", x)
    x = re.sub(r"(?<!\*)\*([^*\s][^*]*?)(?<!\s)\*(?!\*)", r"<em>\1</em>", x)
    x = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', x)
    x = re.sub(r"(?<![\"'=])<(https?://[^>\s]+)>", r'<a href="\1" target="_blank" rel="noopener">\1</a>', x)
    return x


def read_md(path, fields):
    """ترويسة ثم سطر فارغ ثم النص. الترويسة إما «مفتاح: قيمة» بالعربية (الكتابة اليدوية)،
    أو بين سطرين --- بالإنجليزية (ما تكتبه لوحة التحكم).
    في النص: سطر يبدأ بـ ## عنوان فرعي، وسطر يبدأ بـ > اقتباس، والباقي فقرات."""
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n").lstrip("\ufeff")
    meta = {}
    if text.startswith("---\n"):
        import yaml  # يُثبَّت في GitHub Actions مع أداة الصوت
        _, head, body = text.split("---\n", 2) if text.count("---\n") >= 2 else ("", text[4:], "")
        for key, value in (yaml.safe_load(head) or {}).items():
            if isinstance(value, list):
                value = "، ".join(str(v) for v in value)
            elif key == "time" and isinstance(value, int):  # YAML يقرأ 21:30 غير المقتبسة رقمًا (دقائق)
                value = f"{value // 60}:{value % 60:02d}"
            meta[FM_KEYS.get(key, key)] = "" if value is None else str(value).strip()
        body = body.strip("\n")
    else:
        head, _, body = text.strip().partition("\n\n")
        for line in head.splitlines():
            key, _, value = line.partition(":")
            key = key.strip()
            meta[fields.get(key) or OPTIONAL_FIELDS.get(key, key)] = value.strip()
    for label, key in fields.items():
        if not meta.get(key):
            raise SystemExit(f"{path}: الحقل «{label}» مفقود في الترويسة")
    blocks = []
    for para in re.split(r"\n\s*\n", body.strip()):
        lines = [line.strip() for line in para.splitlines() if line.strip()]
        lines = [line[:-1].rstrip() if line.endswith("\\") else line for line in lines]  # سطر جديد من المحرّر
        # فقرة كل أسطرها وسائط: صور/فيديو/صوت/ملفات (في assets/media أو assets/images) أو روابط يوتيوب
        if lines and all(is_media_line(line) for line in lines):
            for line in lines:
                m = MEDIA_RE.fullmatch(line.strip("<>"))
                if m and "://" not in m.group(3) and not media_path(m.group(3)):
                    raise SystemExit(f"{path}: الملف {m.group(3)} غير موجود في assets/media ولا assets/images")
            blocks.append(("img", "\n".join(line.strip("<>") for line in lines)))
            continue
        # قائمة نقطية أو مرقّمة من المحرّر (سطران فأكثر)
        if len(lines) > 1 and all(re.match(r"([-*+]|\d+[.)])\s", line) for line in lines):
            tag = "ol" if lines[0][0].isdigit() else "ul"
            items = "".join(f"<li>{inline_md(re.sub(r'^([-*+]|\d+[.)])\s+', '', line))}</li>" for line in lines)
            blocks.append(("list", f"<{tag}>{items}</{tag}>"))
            continue
        para = " ".join(lines)
        if re.match(r"#{1,6} ", para):
            blocks.append(("h2", inline_md(para.lstrip("#").strip())))
        elif para.startswith(">"):
            blocks.append(("quote", inline_md(re.sub(r"^>\s?", "", re.sub(r" >\s?", " ", para)))))
        elif para:
            blocks.append(("p", inline_md(para)))
    return meta, blocks


def load_article(path):
    meta, blocks = read_md(path, FIELDS)
    # أكثر من تصنيف يُفصل بفاصلة: «تأملات في القرآن والسنة، مقالات نفسية واجتماعية»
    meta["tag"] = tuple(t.strip() for t in re.split(r"[،,]", meta["tag"]) if t.strip())
    for t in meta["tag"]:
        if t not in CATEGORIES:  # تصنيف غير موجود في القائمة: يُنشر المقال ويظهر التصنيف عليه، بلا زر فرز
            print(f"تنبيه: {path}: التصنيف «{t}» ليس في content/data/journeys.yml")
            CATEGORIES_EN.setdefault(t, t)
    if meta.get("time") and not re.fullmatch(r"\d{1,2}:\d{2}", meta["time"]):
        raise SystemExit(f"{path}: اكتبي الوقت بهذا الشكل 21:30")
    slug = os.path.splitext(os.path.basename(path))[0]
    return meta, slug, blocks


# newest first
_loaded = sorted((load_article(f) for f in sorted(glob.glob(os.path.join(ROOT, "content", "articles", "*.md")))),
                 key=lambda x: x[0]["date"], reverse=True)
_en_files = {os.path.splitext(os.path.basename(f))[0]: f
             for f in glob.glob(os.path.join(ROOT, "content", "en", "articles", "*.md"))}
for _s in _en_files:
    if _s not in {slug for _, slug, _ in _loaded}:
        raise SystemExit(f"content/en/articles/{_s}.md: لا يوجد مقال عربي بالاسم نفسه")


def articles_for(lang):
    """The articles of one language, newest first. English shows only the translated ones."""
    out = []
    for m, slug, blocks in _loaded:
        poem = m.get("kind") == "قصيدة" or "قصائد" in m["tag"]
        if lang == "en":
            if slug not in _en_files:
                continue
            en, en_blocks = read_md(_en_files[slug], EN_FIELDS)
            if poem and len(en_blocks) != len(blocks):
                raise SystemExit(f"content/en/articles/{slug}.md: عدد أبيات الترجمة لا يساوي عدد أبيات القصيدة")
            # *word* in the translation is shown in italics (used for transliterated Arabic words)
            em = lambda x: re.sub(r"\*([^*]+)\*", r"<em>\1</em>", x)
            title = em(en["title"])
            first = next((x for k, x in en_blocks if k == "p"), "")
            excerpt = em(en.get("excerpt") or en.get("quote") or first)
            quote = em(en.get("quote") or excerpt)
            blocks = [(k, em(x)) for k, x in en_blocks]
            tags = tuple(CATEGORIES_EN[t] for t in m["tag"])
        else:
            title, tags = m["title"], m["tag"]
            first = next((x for k, x in blocks if k == "p"), "")
            excerpt = m.get("excerpt") or m.get("quote") or first
            quote = m.get("quote") or excerpt
        out.append({
            "slug": slug, "tag": tags, "title": title, "excerpt": excerpt,
            "has_excerpt": bool(m.get("excerpt")) if lang == "ar" else bool(excerpt and en.get("excerpt")), "quote": quote, "blocks": blocks, "poem": poem,
            "date": fmt_date(lang, m["date"]), "iso": m["date"], "read": read_time(lang, blocks),
            "time": fmt_time(lang, m["time"]) if m.get("time") else "",
            "minutes": word_count(blocks) / 200,
        })
    return out


def tags_html(tags, indent):
    spans = "".join(f'<span class="tag">{t}</span>' for t in tags)
    return f'{indent}<div class="tags">{spans}</div>' if len(tags) > 1 else indent + spans


# محطات جواز سفر بالترتيب من content/data/passport.yml: (أيقونة، النص، إيموجي الشارة، نوع خاص)
_KINDS = {"البداية": "start", "جائزة": "award", "الختام": "final"}
STATIONS = [(st.get("icon", ""), tx(st), st.get("badge", "") or "", _KINDS.get(st.get("kind"), ""))
            for st in PASSPORT.get("stations", [])]

# كتبي: (العنوان، العنوان الفرعي، الناشر، السنة، الرابط، صورة الغلاف الأمامي، صورة الغلاف الخلفي، فقرات الوصف)
# الصور في assets/books/
def load_books():
    """الكتب من content/books/*.md (وترجمتها في content/en/books/ بالاسم نفسه)، مرتبة بحقل «الترتيب»."""
    out = []
    ar_fields = {"العنوان": "title", "العنوان الفرعي": "sub", "الناشر": "pub", "السنة": "year", "رابط المتجر": "url",
                 "الغلاف الأمامي": "front", "الغلاف الخلفي": "back", "الترتيب": "order",
                 "رابط التحميل": "pdf"}
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "books", "*.md"))):
        m, blocks = read_md(path, {k: v for k, v in ar_fields.items() if k in ("العنوان", "الغلاف الأمامي", "الغلاف الخلفي")})
        m = {ar_fields.get(k, k): v for k, v in m.items()}
        en_path = os.path.join(ROOT, "content", "en", "books", os.path.basename(path))
        en, en_blocks = ({}, [])
        if os.path.exists(en_path):
            en, en_blocks = read_md(en_path, {"Title": "title"})
            en = {k.lower(): v for k, v in en.items()}
        m["front"], m["back"] = media_name(m["front"], ("assets/books",)), media_name(m["back"], ("assets/books",))
        if m.get("pdf") and "://" not in m["pdf"]:
            m["pdf"] = media_name(m["pdf"], ("assets/books",))
        for img in (m["front"], m["back"]):
            if not os.path.exists(os.path.join(ROOT, "assets", "books", img)):
                raise SystemExit(f"{path}: صورة الغلاف {img} غير موجودة في assets/books")
        # «رابط التحميل»: ملف في assets/books (مثل كتاب.pdf) أو رابط كامل
        pdf = m.get("pdf") or None
        if pdf and "://" not in pdf and not os.path.exists(os.path.join(ROOT, "assets", "books", pdf)):
            raise SystemExit(f"{path}: ملف الكتاب {pdf} غير موجود في assets/books")
        pair = lambda a, e: (a, e or a)
        desc = [pair(x, en_blocks[i][1] if i < len(en_blocks) else "") for i, (_, x) in enumerate(blocks)]
        out.append((int(m.get("order") or 99), (pair(m["title"], en.get("title")), pair(m.get("sub", ""), en.get("subtitle")),
                    pair(m.get("pub", ""), en.get("publisher")), pair(m.get("year", ""), en.get("year")),
                    m.get("url") or None, m["front"], m["back"], desc, pdf)))
    return [b for _, b in sorted(out, key=lambda x: x[0])]


BOOKS = load_books()

EMAIL = CONTACT.get("email") or "shoroogmi1@gmail.com"
# شعارات التطبيقات (من مكتبة Simple Icons، رخصة CC0)
BRAND_ICONS = {
    "gmail": "M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z",
    "x": "M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z",
    "instagram": "M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077",
    "whatsapp": "M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z",
    "substack": "M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z",
    "facebook": "M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z",
}


_PLATFORMS = {"بريد": "gmail", "إكس": "x", "إنستغرام": "instagram", "واتساب": "whatsapp", "سبستاك": "substack", "فيسبوك": "facebook"}
# (الشعار من BRAND_ICONS، المنصة، النص الظاهر، الرابط أو None)
CONTACTS = [(_PLATFORMS.get(c.get("platform"), "gmail"), tx(c, "name_ar", "name_en"), tx(c, "shown_ar", "shown_en"), c.get("url") or None)
            for c in CONTACT.get("contacts", [])]

LEGAL_UPDATED = tx(LEGAL.get("updated"))
# الصفحات القانونية: (عنوان القسم، [فقرات]) بالعربية ثم بالإنجليزية
_sections = lambda key: [(tx(sec, "title_ar", "title_en"), [tx(p) for p in sec.get("paragraphs", [])]) for sec in LEGAL.get(key, [])]
PRIVACY = _sections("privacy")
TERMS = _sections("terms")


def build(lang):
    t = lambda a, e: a if lang == "ar" else e
    L = lambda v: pick(lang, v)
    num = ar if lang == "ar" else str
    fwd = t("←", "→")
    q1, q2 = t("«", "“"), t("»", "”")
    me = t("شروق المحمادي", "Shoroog Almehmadi")

    ALL_ARTICLES = articles_for(lang)
    ARTICLES = ALL_ARTICLES
    SLUGS = [a["slug"] for a in ALL_ARTICLES]

    def article_card(a, p="", hook=False):
        """p is the path prefix from the current page to the blog folder.
        hook: show the article's chosen quote (اقتباس) instead of the excerpt, used on the home page."""
        return f"""          <article class="post-card" data-tag="{'|'.join(a["tag"])}">
{tags_html(a["tag"], "            ")}
            <h3><a class="stretched" href="{p}articles/{a["slug"]}.html">{a["title"]}</a></h3>
            <p>{q1 + a["quote"] + q2 if hook else a["excerpt"]}</p>
            <p class="meta">{a["date"]} · {a["read"]} {t("قراءة", "read")}</p>
          </article>"""

    def latest(prefix, more, hook=False):
        return f"""    <section class="section alt">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("أحدث الرحلات الطويلة", "Latest Long Journeys")}</h2>
          <a class="more" href="{more}">{t("كل الرحلات", "All journeys")} {fwd}</a>
        </div>
        <div class="posts">
{chr(10).join(article_card(a, prefix, hook) for a in ARTICLES[:3])}
        </div>
      </div>
    </section>
"""

    # ---------- «اختيارات القرّاء»: الأكثر قراءةً وإعجابًا (تُحدَّث يوميًا من tools/popular.py) ----------
    def readers_picks(prefix):
        by_slug = {a["slug"]: a for a in ALL_ARTICLES}
        picks = [by_slug[x["slug"]] for x in POPULAR if x["slug"] in by_slug][:6]
        if not picks:
            return ""
        cards = "\n".join(article_card(a, prefix, hook=True).replace(
            '<article class="post-card"', f'<article class="post-card pick" data-rank="{num(i)}"', 1) for i, a in enumerate(picks, 1))
        return f"""    <section class="section readers-picks">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("اختيارات القرّاء", "Readers' Picks")} <span class="title-note">{t("(الأكثر تأثيرًا)", "(Most Impactful)")}</span></h2>
        </div>
        <div class="posts scroller">
{cards}
        </div>
      </div>
    </section>
"""

    # ---------- «ما قاله المسافرون» و«قيّمنا» ----------
    def newsletter_html(narrow=False):
        """نموذج الاشتراك في القائمة البريدية للموقع: البريد يُحفظ في جدول subscribers (Supabase) ويصل إشعار به إلى البريد."""
        return f"""    <section class="section newsletter">
      <div class="container{" narrow" if narrow else ""}">
        <form class="newsletter-box" data-email="{EMAIL}" novalidate>
          <h2 class="section-title">{L(HOME.get("newsletter_title", ("القائمة البريدية ✉️", "Mailing List ✉️")))}</h2>
          <p>{L(HOME.get("newsletter_sub", ("", "")))}</p>
          <div class="nl-row">
            <input type="email" name="email" required autocomplete="email" dir="ltr" placeholder="name@example.com" aria-label="{t("بريدك الإلكتروني", "Your email")}">
            <button type="submit" class="btn btn-primary">{t("اشترك", "Subscribe")}</button>
          </div>
          <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
          <p class="form-status" role="status"></p>
        </form>
      </div>
    </section>
"""

    def testimonials_html(limit, home=False):
        """التقييمات الإيجابية تُحمَّل من قاعدة البيانات؛ في الرئيسية شريط يُمرَّر أفقيًا ورابط للصفحة الكاملة."""
        more = (f'<a class="more" href="testimonials.html">{t("كل ما قاله المسافرون", "All reviews")} {fwd}</a>' if home else "")
        return f"""    <section class="section testimonials">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("ما قاله المسافرون", "What Travelers Said")}</h2>{more}
        </div>
        <div class="testimonial-list{" scroller" if home else ""}" data-limit="{limit}">
          <p class="t-empty">{t("لا تقييمات بعد… كن أول من يقيّم الرحلة ⭐", "No reviews yet… be the first to rate the journey ⭐")}</p>
        </div>
      </div>
    </section>
"""

    rate_section = f"""    <section class="section">
      <div class="container narrow">
        <form class="rate-box" data-email="{EMAIL}" novalidate>
          <h2 class="section-title">{t("قيّمنا", "Rate Us")}</h2>
          <fieldset class="stars" aria-label="{t("التقييم بالنجوم", "Star rating")}">
            <legend class="sr-only">{t("كم نجمة تعطي الرحلة؟", "How many stars for the journey?")}</legend>
            {"".join(f'<input type="radio" name="stars" id="star{n}" value="{n}"><label for="star{n}" title="{num(n)}">★</label>' for n in range(5, 0, -1))}
          </fieldset>
          <textarea name="note" rows="3" maxlength="500" placeholder="{t("كيف كانت الرحلة؟ بشّرنا!", "How was the journey? Tell us!")}" aria-label="{t("تعليق سريع", "Quick comment")}"></textarea>
          <input type="text" name="name" maxlength="40" placeholder="{t("اسمك (اختياري)", "Your name (optional)")}" aria-label="{t("الاسم", "Name")}" autocomplete="nickname">
          <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
          <button type="submit" class="btn btn-primary">{t("أرسل", "Send")}</button>
          <p class="form-status" role="status"></p>
        </form>
      </div>
    </section>
"""

    # ---------- Home ----------
    home = f"""    <section class="hero">
      <div class="sky" aria-hidden="true">
        <div class="sun"><span class="rays"></span></div>
        <span class="cloud c1"></span><span class="cloud c2"></span><span class="cloud c3"></span>
      </div>
      <div class="container hero-inner">
        <figure class="verse">
          <blockquote><span>{L(HOME["verse"])}</span></blockquote>
        </figure>
        <h1>{me}</h1>
        <p class="lead">{L(HOME["lead"])}</p>
        <div class="hero-actions">
          <a href="blog/index.html" class="btn btn-primary">{t("سجل الرحلات", "Travel Log")}</a>
          <a href="sira.html" class="btn btn-ghost">{t("جواز سفر", "Passport")}</a>
        </div>
        <ul class="site-stats" aria-label="{t("إحصاءات الموقع", "Site stats")}">
          <li>🧳 {t("زوار الموقع", "Site visitors")}: <b data-stat="visitors">…</b></li>
          <li>🔁 {t("قرّاء دائمون", "Regular readers")}: <b data-stat="returning">…</b></li>
          <li><a href="blog/articles.html">✍️ {t("عدد المقالات", "Articles")}: <b>{num(len(ALL_ARTICLES))}</b></a></li>
        </ul>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2 class="section-title">{t("مُشعشعة", "Radiant")}</h2>
        <div class="tiles">
          <a class="tile" href="sira.html"><span class="tile-icon">🛂</span><h3>{t("جواز سفر", "Passport")}</h3><p>{t("هوية الكاتبة وسيرة موجزة.", "The writer's identity and a brief biography.")}</p></a>
          <a class="tile" href="blog/index.html"><span class="tile-icon">✍️</span><h3>{t("سجل الرحلات", "Travel Log")}</h3><p>{t("مقالات وتأملات وتقارير.", "Essays, reflections and reports.")}</p></a>
          <a class="tile" href="books.html"><span class="tile-icon">📚</span><h3>{t("أمتعة السفر", "Luggage")}</h3><p>{t("كتب تسليك في الرحلة.", "Books to keep you company on the journey.")}</p></a>
        </div>
      </div>
    </section>

{latest("blog/", "blog/articles.html", hook=True) if ARTICLES else ""}
{readers_picks("blog/")}

{newsletter_html()}
{testimonials_html(limit=12, home=True)}
{rate_section}
    <section class="section cta">
      <div class="container cta-inner">
        <h2>{L(HOME["cta_title"])}</h2>
        <p>{L(HOME["cta_sub"])}</p>
        <a href="contact.html" class="btn btn-primary">{t("برج المراقبة", "Control Tower")}</a>
      </div>
    </section>
"""
    page(lang, "index.html", "home", me, home,
         t("الموقع الشخصي لشروق المحمادي: جواز سفر، سجل الرحلات، أمتعة السفر، وبرج المراقبة.",
           "The personal website of Shoroog Almehmadi: Passport, Travel Log, Luggage, and Control Tower."),
         jsonld={"@context": "https://schema.org", "@graph": [
             {"@type": "Person", "@id": SITE + "#person", "name": "شروق المحمادي", "alternateName": ["Shoroog Almehmadi", "shoroogmi"],
              "url": SITE, "jobTitle": t("كاتبة", "Writer"), "image": SITE + "assets/images/og-default.jpg",
              "sameAs": [c[3] for c in CONTACTS if c[3] and c[3].startswith("https://")]},
             {"@type": "WebSite", "@id": SITE + "#website", "name": t("شروق المحمادي", "Shoroog Almehmadi"), "url": SITE,
              "inLanguage": lang, "author": {"@id": SITE + "#person"},
              "potentialAction": {"@type": "SearchAction", "target": SITE + out_path(lang, "search.html") + "?q={search_term_string}",
                                  "query-input": "required name=search_term_string"}}]})

    # ---------- What travelers said (page) ----------
    reviews = page_head(me, t("ما قاله المسافرون", "What Travelers Said"),
                        L(HOME["reviews_lead"])) + testimonials_html(limit=200) + rate_section
    page(lang, "testimonials.html", "testimonials", f"{t('ما قاله المسافرون', 'What Travelers Said')} · {me}", reviews,
         t("تقييمات قرّاء موقع شروق المحمادي.", "Reviews from readers of Shoroog Almehmadi's website."))

    # ---------- Sira ----------
    def station_item(i, s):
        icon, text, badge, kind = s
        return f"""          <li class="station{' ' + kind if kind else ''}">
            <button class="node" type="button" aria-label="{t("المحطة", "Stop")} {num(i)}"><span class="num">{num(i)}</span><span class="icon">{icon}</span></button>
            <article class="stop-card">
              <p>{L(text)}</p>
              <span class="badge" aria-hidden="true">{badge}</span>
            </article>
          </li>"""

    sira = page_head(t("جواز سفر", "Passport"), L(tx(PASSPORT.get("title"))), L(tx(PASSPORT.get("lead"))),
                     extra=f'        <p class="hero-share">{share_btn(lang, "sira.html", t("جواز سفر — شروق المحمادي", "Passport — Shoroog Almehmadi"))}</p>\n') + f"""
    <section class="section quest">
      <div class="container">
        <ul class="hud" aria-label="{t("لوحة اللعبة", "Game panel")}">
          <li>💺 {t("المقعد", "Seat")}: <b>{t("الأيمن", "Right")}</b></li>
          <li>🗺️ {t("المحطات", "Stops")}: <b>{num(len(STATIONS))}</b></li>
          <li>⛽ {t("الوقود", "Fuel")}: <b>{t("قهوة", "Coffee")} ☕</b></li>
        </ul>
        <div class="map">
          <div class="map-floor" aria-hidden="true"></div>
          <div class="decor" aria-hidden="true"><span>🏝️</span><span>☁️</span><span>🎈</span><span>🌴</span><span>☁️</span><span>🐪</span><span>⛰️</span><span>🎈</span></div>
          <svg class="route" aria-hidden="true"><path class="route-line"/><path class="route-done"/></svg>
          <span class="plane" aria-hidden="true">✈️</span>
          <ol class="stations">
{chr(10).join(station_item(i + 1, s) for i, s in enumerate(STATIONS))}
          </ol>
          <p class="map-end">🏁 {t("نهاية الخريطة… حتى الآن. التحديث القادم قريبًا", "End of the map… for now. Next update coming soon")} 😉</p>
        </div>
      </div>
    </section>
"""
    page(lang, "sira.html", "sira", f"{t('جواز سفر', 'Passport')} · {me}", sira,
         t("جواز سفر شروق المحمادي: خريطة رحلتها من ١٩٩٩.", "Shoroog Almehmadi's passport: the map of her journey since 1999."))

    # ---------- Blog hub ----------
    blog = page_head(t("سجل الرحلات", "Travel Log"), t("سجل الرحلات", "Travel Log"),
                     t("مقالات وتأملات وتقارير.", "Essays, reflections and reports.")) + f"""
    <section class="section">
      <div class="container">
        <div class="blog-split">
          <a class="blog-door" href="articles.html">
            <span class="door-icon">✍️</span>
            <h2>{t("رحلات طويلة", "Long Journeys")}</h2>
            <p>{t("مقالات وتأملات بين الثقيلة والخفيفة.", "Essays and reflections, from the weighty to the light.")}</p>
            <span class="count">{num(len(ARTICLES))} {t("رحلات", "journeys")}</span>
          </a>
        </div>
      </div>
    </section>

{latest("", "articles.html") if ARTICLES else ""}
"""
    page(lang, "blog/index.html", "blog", f"{t('سجل الرحلات', 'Travel Log')} · {me}", blog,
         t("سجل رحلات شروق المحمادي: رحلات طويلة.", "Shoroog Almehmadi's travel log: Long Journeys."))

    crumbs_tpl = (f'        <nav class="crumbs" aria-label="{t("مسار التنقل", "Breadcrumb")}"><a href="index.html">'
                  f'{t("سجل الرحلات", "Travel Log")}</a> / <span>{{}}</span></nav>\n')

    # ---------- Articles ----------
    cats = CATEGORIES if lang == "ar" else [CATEGORIES_EN[c] for c in CATEGORIES]
    articles = page_head(t("سجل الرحلات", "Travel Log"), t("رحلات طويلة", "Long Journeys"),
                         t("تأملات في القرآن والسنة، ومقالات نفسية واجتماعية وفكرية وإعلامية، والزاوية ٣٦، وقصائد.",
                           "Reflections on the Quran and Sunnah, psychological, social, intellectual and media essays, Corner 36, and poems."),
                         crumbs_tpl.format(t("رحلات طويلة", "Long Journeys"))) + f"""
    <section class="section">
      <div class="container">
        <div class="toolbar">
          <div class="filters">
            <button class="filter active" data-filter="all">{t("الكل", "All")}</button>
{chr(10).join(f'            <button class="filter" data-filter="{c}">{c}</button>' for c in cats)}
          </div>
          <input class="search" type="search" placeholder="{t("ابحث في الرحلات…", "Search the journeys…")}" aria-label="{t("ابحث في الرحلات الطويلة", "Search the long journeys")}">
        </div>
        <div class="cat-intro" data-for="{t(ZAWIYA_TAG, CATEGORIES_EN[ZAWIYA_TAG])}" hidden>
          <img src="{"../" * out_path(lang, "blog/articles.html").count("/")}{ZAWIYA_LOGO}" alt="{t("شعار الزاوية ٣٦", "Corner 36 logo")}" width="64" height="64">
          <p>{t("مقالات حديثة نترجمها ونحوّرها بطريقتنا!", "Recent articles we translate and reshape our own way!")}</p>
        </div>
        <div class="posts" data-filterable>
{chr(10).join(article_card(a) for a in ARTICLES)}
        </div>
        <p class="empty"{" hidden" if ARTICLES else ""}>{t("لا توجد رحلات بعد.", "No journeys yet.")}</p>
      </div>
    </section>
"""
    page(lang, "blog/articles.html", "blog-articles", f"{t('رحلات طويلة', 'Long Journeys')} · {me}", articles,
         t("رحلات شروق المحمادي الطويلة.", "Shoroog Almehmadi's long journeys."))

    # ---------- Zawiya 36: صارت تصنيفًا؛ الرابط القديم يحوّل إلى رحلات طويلة مفتوحةً على التصنيف ----------
    z_target = "articles.html#" + url_quote(t(ZAWIYA_TAG, CATEGORIES_EN[ZAWIYA_TAG]))
    with open(os.path.join(ROOT, out_path(lang, "blog/zawiya-36.html")), "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html>
<html lang="{lang}" dir="{t('rtl', 'ltr')}"><head><meta charset="utf-8">
<title>{t('الزاوية ٣٦', 'Corner 36')} · {me}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{SITE}{out_path(lang, 'blog/articles.html')}">
<meta http-equiv="refresh" content="0; url={z_target}">
<script>location.replace("{z_target}")</script>
</head><body><p><a href="{z_target}">{t('الزاوية ٣٦', 'Corner 36')}</a></p></body></html>
""")

    # ---------- Privacy & Terms ----------
    for path, key, title, lead, sections in (
            ("privacy.html", "privacy", t("سياسة الخصوصية", "Privacy Policy"),
             t("ما الذي يُجمع عند زيارتك، ولماذا، وأين يُحفظ.", "What is collected when you visit, why, and where it is kept."), PRIVACY),
            ("terms.html", "terms", t("شروط الاستخدام", "Terms of Use"),
             t("الشروط التي تنظّم استخدام الموقع ومحتواه.", "The terms that govern the use of this site and its content."), TERMS)):
        body_html = "".join(f"        <h2>{L(h)}</h2>\n" + "".join(f"        <p>{L(par)}</p>\n" for par in pars) for h, pars in sections)
        legal = page_head(me, title, lead) + f"""
    <section class="section">
      <div class="container narrow prose legal">
        <p class="meta">{t("آخر تحديث:", "Last updated:")} {L(LEGAL_UPDATED)}</p>
{body_html}      </div>
    </section>
"""
        page(lang, path, key, f"{title} · {me}", legal, title)

    # ---------- Search ----------
    # فهرس البحث: العنوان والملخص ونص المقال كاملًا، يُحمَّل عند أول بحث فقط
    strip = lambda x: re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", x))).strip()
    index = [{"u": f"blog/articles/{a['slug']}.html", "t": strip(a["title"]), "d": a["date"], "c": list(a["tag"]),
              "x": strip(" ".join([a["excerpt"]] + [x for k, x in a["blocks"] if k != "img"]))} for a in ALL_ARTICLES]
    idx_name = f"assets/search-{lang}.json"
    with open(os.path.join(ROOT, idx_name), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    idx_v = hashlib.md5(json.dumps(index, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]
    s_root = "../" * out_path(lang, "search.html").count("/")
    search = page_head(t("سجل الرحلات", "Travel Log"), t("ابحث في الرحلات", "Search the Journeys"),
                       t("اكتب أي كلمة: من عنوان المقال أو من داخل نصه.", "Type any word, from an article's title or from inside its text.")) + f"""
    <section class="section">
      <div class="container narrow">
        <form class="site-search" role="search" data-index="{s_root}{idx_name}?v={idx_v}">
          <input class="search" type="search" name="q" placeholder="{t("ابحث عن كلمة أو جملة…", "Search for a word or phrase…")}" aria-label="{t("كلمة البحث", "Search term")}" autocomplete="off">
        </form>
        <p class="search-count" role="status"></p>
        <ol class="search-results"></ol>
      </div>
    </section>
"""
    page(lang, "search.html", "search", f"{t('ابحث في الرحلات', 'Search the Journeys')} · {me}", search,
         t("ابحث في مقالات شروق المحمادي.", "Search Shoroog Almehmadi's articles."))

    # ---------- Books ----------
    a_root = "../" * out_path(lang, "books.html").count("/")

    def book_card(title, sub, pub, year, url, front, back, desc, pdf=None):
        title = L(title)
        book_id = "book-" + os.path.splitext(front)[0].replace("-front", "")
        link = (f'\n              <a class="btn btn-primary book-link" href="{url}" target="_blank" rel="noopener">🛒 {t("زيارة المتجر", "Visit the store")}</a>'
                if url else "")
        if pdf:
            href = pdf if "://" in pdf else f"{a_root}assets/books/{pdf}"
            key = "dl-" + book_id
            link += (f'\n              <a class="btn btn-primary book-link book-dl" data-count="{key}" href="{href}" download target="_blank" rel="noopener">'
                     f'📥 {t("تحميل الكتاب PDF", "Download the book (PDF)")}</a>'
                     f'\n              <span class="dl-count" title="{t("عدد التحميلات", "Downloads")}">⬇️ <b data-count-of="{key}">…</b> {t("تحميل", "downloads")}</span>')
        covers = "".join(
            f'\n              <a href="{a_root}assets/books/{img}" target="_blank" rel="noopener"><img src="{a_root}assets/books/{img}" alt="{alt} {title}" width="900" height="1253" loading="lazy"></a>'
            for img, alt in ((front, t("الغلاف الأمامي لكتاب", "Front cover of")), (back, t("الغلاف الخلفي لكتاب", "Back cover of"))))
        return f"""          <article class="book mine" id="{book_id}">
            <div class="covers">{covers}
            </div>
            <div class="book-info">
              <h3>{title}</h3>
              <p class="subtitle">{L(sub)}</p>
              <p class="author">{L(pub)} · {L(year)}</p>
              <div class="book-desc">
{chr(10).join(f"                <p>{L(d)}</p>" for d in desc)}
              </div>
              <div class="book-actions">{link}
              {share_btn(lang, f"books.html#{book_id}", title)}
              </div>
            </div>
          </article>"""

    books = page_head(t("أمتعة السفر", "Luggage"), L(HOME["books_title"]), "") + f"""
    <section class="section">
      <div class="container">
        <div class="books mine-list">
{chr(10).join(book_card(*bk) for bk in BOOKS)}
        </div>
      </div>
    </section>
"""
    page(lang, "books.html", "books", f"{t('أمتعة السفر', 'Luggage')} · {me}", books,
         t("كتب شروق المحمادي.", "Books by Shoroog Almehmadi."))

    # ---------- Contact ----------
    def contact_item(icon, label, text, url, note=""):
        text = L(text)
        if url:
            ext = "" if url.startswith("mailto:") else ' target="_blank" rel="noopener"'
            ltr = ' dir="ltr"' if lang == "ar" and text.isascii() else ""
            value = f'<a href="{url}"{ext}{ltr}>{text}</a>'
        else:
            value = f'<span class="handle">{text}</span>'
        if note:
            value += f'<small>{L(note)}</small>'
        return f"""            <li><span class="ci ci-{icon}" aria-hidden="true"><svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="{BRAND_ICONS[icon]}"/></svg></span><div><strong>{L(label)}</strong>{value}</div></li>"""

    topics = [tx(x) for x in CONTACT.get("topics", [])]
    contact = page_head(t("برج المراقبة", "Control Tower"), L(tx(CONTACT.get("title"))), L(tx(CONTACT.get("lead")))) + f"""
    <section class="section">
      <div class="container contact">
        <form class="contact-form" data-email="{EMAIL}" novalidate>
          <label>{t("الاسم", "Name")}
            <input type="text" name="name" required autocomplete="name">
          </label>
          <label>{t("بريدك", "Your email")} <small class="field-hint">{t("(اختياري، إذا كنت تريد ردًا على الرسالة فمن الضروري وضع البريد. إذا كنت لا تريد ردًا فلا يحتاج!)", "(Optional. If you want a reply to your message, you need to add your email. If you don't want a reply, there's no need!)")}</small>
            <input type="email" name="email" autocomplete="email" dir="ltr">
          </label>
          <label>{t("الموضوع", "Topic")}
            <select name="topic">
{chr(10).join(f"              <option>{L(o)}</option>" for o in topics)}
            </select>
          </label>
          <label>{t("رسالتك", "Your message")}
            <textarea name="message" rows="6" required></textarea>
          </label>
          <input type="text" name="_honey" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
          <button type="submit" class="btn btn-primary">{t("أرسل إلى البرج", "Send to the Tower")}</button>
          <p class="form-status" role="status"></p>
        </form>
        <aside class="contact-side">
          <h2>{t("ترددات البرج", "Tower Frequencies")}</h2>
          <ul>
{chr(10).join(contact_item(*c) for c in CONTACTS)}
          </ul>
        </aside>
      </div>
    </section>
"""
    page(lang, "contact.html", "contact", f"{t('برج المراقبة', 'Control Tower')} · {me}", contact,
         t("برج المراقبة: تواصل مع شروق المحمادي.", "Control Tower: get in touch with Shoroog Almehmadi."))

    # ---------- Article pages ----------
    art_root = "../" * out_path(lang, "blog/articles/x.html").count("/")  # from an article page to the site root

    def render_block(kind, text):
        if kind == "img":
            figs, out = [], []
            def flush():
                if figs:
                    out.append(figs[0] if len(figs) == 1 else f'<div class="post-gallery">{"".join(figs)}</div>')
                    figs.clear()
            for line in text.split("\n"):
                yt = YT_RE.fullmatch(line)
                m = MEDIA_RE.fullmatch(line)
                if m and YT_RE.fullmatch(m.group(3)):
                    yt = YT_RE.fullmatch(m.group(3))
                if yt:
                    flush()
                    cap = f"<figcaption>{m.group(2)}</figcaption>" if m and m.group(2) else ""
                    out.append(f'<figure class="post-figure post-video"><div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/{yt.group(1)}" '
                               f'title="{(m.group(2) if m else "") or t("فيديو", "Video")}" loading="lazy" allowfullscreen '
                               f'allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"></iframe></div>{cap}</figure>')
                    continue
                bang, alt, src = m.groups()
                url = f"{art_root}{media_path(src)}"
                low = src.lower()
                cap = f"<figcaption>{alt}</figcaption>" if alt else ""
                if low.endswith(VIDEO_EXT):
                    flush()
                    out.append(f'<figure class="post-figure post-video"><video controls preload="metadata" src="{url}"></video>{cap}</figure>')
                elif low.endswith(SOUND_EXT):
                    flush()
                    out.append(f'<figure class="post-figure post-sound"><audio controls preload="none" src="{url}"></audio>{cap}</figure>')
                elif bang:
                    figs.append(f'<figure class="post-figure"><a href="{url}" target="_blank" rel="noopener">'
                                f'<img src="{url}" alt="{alt}" loading="lazy"></a>{cap}</figure>')
                else:
                    flush()
                    ext = src.rsplit(".", 1)[-1].upper()
                    out.append(f'<a class="post-file" href="{url}" download target="_blank" rel="noopener">'
                               f'<span class="post-file-icon" aria-hidden="true">📎</span><span class="post-file-name">{alt or src}</span>'
                               f'<span class="post-file-ext">{ext} · {t("تحميل", "Download")}</span></a>')
            flush()
            return chr(10).join("        " + x for x in out)
        if kind == "h2":
            return f"        <h2>{text}</h2>"
        if kind == "list":
            return f"        {text}"
        if kind == "quote":
            return f"        <blockquote><p>{text}</p></blockquote>"
        return f"        <p>{text}</p>"

    def render_body(a):
        if not a["poem"]:
            return chr(10).join(render_block(k, x) for k, x in a["blocks"])
        # a poem: one line per verse half, with a gap after every couplet
        return chr(10).join(f'        <p{" class=\"verse-end\"" if i % 2 else ""}>{x}</p>' for i, (_, x) in enumerate(a["blocks"]))

    for old in glob.glob(os.path.join(ROOT, out_path(lang, "blog/articles"), "*.html")):
        if os.path.splitext(os.path.basename(old))[0] not in SLUGS:
            os.remove(old)

    for a in ALL_ARTICLES:
        group = ARTICLES
        i = group.index(a)
        slug, tag, title, excerpt = a["slug"], a["tag"], a["title"], a["excerpt"]
        newer = group[i - 1] if i > 0 else None
        older = group[i + 1] if i + 1 < len(group) else None
        nav = ""
        if older:
            nav += f'<a class="pn prev" href="{older["slug"]}.html"><span>{t("الرحلة السابقة", "Previous journey")}</span>{older["title"]}</a>'
        if newer:
            nav += f'<a class="pn next" href="{newer["slug"]}.html"><span>{t("الرحلة التالية", "Next journey")}</span>{newer["title"]}</a>'
        related = [r for r in group if set(r["tag"]) & set(tag) and r is not a][:2]
        lead_blocks = [x for k, x in a["blocks"] if k != "h2"][:2]
        body = f"""    <section class="page-hero article-hero">
      <div class="clouds" aria-hidden="true"><span class="cloud c1"></span><span class="cloud c2"></span></div>
      <div class="container narrow">
        <nav class="crumbs" aria-label="{t("مسار التنقل", "Breadcrumb")}"><a href="../index.html">{t("سجل الرحلات", "Travel Log")}</a> / <a href="../articles.html">{t("رحلات طويلة", "Long Journeys")}</a></nav>
{tags_html(tag, "        ")}
        <h1>{title}</h1>
        <ul class="post-meta">
          <li>📅 {a["date"]}</li>{f"{chr(10)}          <li>🕘 {a['time']}</li>" if a["time"] else ""}
          <li>⏱️ {a["read"]} {t("قراءة", "read")}</li>
          <li>📖 <b class="read-count">…</b> {t("قراءة مكتملة", "completed reads")}</li>
          <li>❤️ <b class="like-count">…</b></li>
        </ul>
      </div>
    </section>

    <article class="section" id="post" data-slug="{slug}" data-minutes="{a["minutes"]:.2f}">
      <div class="container narrow prose{" poem" if a["poem"] else ""}">
{audio_player(lang, slug) or LISTEN_HTML(t)}
{"" if a["poem"] or not a["has_excerpt"] or excerpt in lead_blocks else f'        <p class="excerpt">{excerpt}</p>{chr(10)}'}{render_body(a)}
        <p class="signature">— {me}</p>
        <div class="engage">
          <button class="like-btn" type="button" aria-pressed="false"><span class="heart" aria-hidden="true">❤️</span> {t("جميل! لقد أعجبني!", "Lovely! I liked it!")} <b class="like-count">…</b></button>
          {share_btn(lang, f"blog/articles/{slug}.html", title)}
        </div>
        <section class="comments" hidden aria-labelledby="comments-title">
          <h2 id="comments-title">💬 {t("تعليقات المسافرين", "Travelers' Comments")}</h2>
          <form class="comment-form" novalidate>
            <input name="name" type="text" maxlength="40" placeholder="{t("اسمك", "Your name")}" aria-label="{t("الاسم", "Name")}" autocomplete="nickname">
            <textarea name="body" rows="3" maxlength="1000" placeholder="{t("اكتب تعليقك…", "Write your comment…")}" aria-label="{t("التعليق", "Comment")}"></textarea>
            <input name="website" class="hp" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
            <button type="submit" class="btn btn-primary">{t("أرسل التعليق", "Post comment")}</button>
            <p class="comment-status" role="status"></p>
          </form>
          <ol class="comment-list"></ol>
          <p class="no-comments" hidden>{t("كن أول من يحلّق", "Be the first to take off")} ✈️</p>
        </section>
        <nav class="post-nav" aria-label="{t("تنقل بين الرحلات", "Journey navigation")}">{nav}</nav>
      </div>
    </article>
{newsletter_html(narrow=True)}"""
        if related:
            body += f"""
    <section class="section alt">
      <div class="container">
        <h2 class="section-title">{t("رحلات أخرى في", "More journeys in")} {q1}{f"{q2} {t('و', 'and ')}{q1}".join(tag)}{q2}</h2>
        <div class="posts">
{chr(10).join(article_card(r, "../") for r in related)}
        </div>
      </div>
    </section>
"""
        # the other language's copy of this article, or its list of articles if not translated
        alt = None if lang == "en" or slug in _en_files else "blog/articles.html"
        plain = lambda x: re.sub(r"<[^>]+>", "", x).replace('"', "&quot;")
        first_img = next((m.group(2) for k, x in a["blocks"] if k == "img" for m in map(IMG_RE.fullmatch, x.split("\n"))
                          if m and m.group(2).lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")) and media_path(m.group(2))), None)
        img_path = media_path(first_img) if first_img else None
        ld = {"@context": "https://schema.org", "@type": "Article", "headline": plain(title), "description": plain(excerpt),
              "inLanguage": lang, "datePublished": a["iso"], "author": {"@type": "Person", "name": me, "url": SITE},
              "image": SITE + (img_path or "assets/images/og-default.jpg"), "mainEntityOfPage": SITE + out_path(lang, f"blog/articles/{slug}.html")}
        page(lang, f"blog/articles/{slug}.html", "blog-articles", f"{plain(title)} · {me}", body, plain(excerpt), alt,
             image=img_path, og_type="article", lastmod=a["iso"], jsonld=ld)
    return len(ARTICLES)


n_ar = build("ar")
n_en = build("en")

# خريطة الموقع وملف robots لمحركات البحث
with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
    for url, alts, lastmod in SITEMAP:
        f.write(f"  <url>\n    <loc>{url}</loc>\n" + (f"    <lastmod>{lastmod}</lastmod>\n" if lastmod else "")
                + "".join(f'    <xhtml:link rel="alternate" hreflang="{lg}" href="{u}"/>\n' for lg, u in sorted(alts.items()))
                + "  </url>\n")
    f.write("</urlset>\n")
with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n")
# قائمة التصنيفات في لوحة التحكم (.pages.yml) تتبع content/data/journeys.yml
_cms = os.path.join(ROOT, ".pages.yml")
if os.path.exists(_cms):
    _txt = open(_cms, encoding="utf-8").read()
    _new = re.sub(r"(# CATEGORIES-START[^\n]*\n)(.*?)(\s*# CATEGORIES-END)",
                  lambda m: m.group(1) + "".join(f"          - {json.dumps(c, ensure_ascii=False)}\n" for c in CATEGORIES).rstrip("\n") + m.group(3),
                  _txt, flags=re.S)
    if _new != _txt:
        open(_cms, "w", encoding="utf-8").write(_new)
print(f"تم: {n_ar} مقالات بالعربية، و{n_en} بالإنجليزية")
