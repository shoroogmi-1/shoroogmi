"""يولّد صفحات الموقع بالعربية (في جذر الموقع) وبالإنجليزية (في مجلد en/).

التشغيل:  python3 build.py

- المقالات: ملف لكل مقال في content/articles/، وترجمته الإنجليزية بالاسم نفسه في content/en/articles/ (انظري README.md).
- الزاوية ٣٦ والكتب ومحطات جواز سفر والتواصل: قوائم داخل هذا الملف (ابحثي عن ZAWIYA و BOOKS و STATIONS و CONTACTS).
  النص الذي يختلف بين اللغتين يُكتب زوجًا: ("النص العربي", "English text").
- بعد أي تعديل شغّلي الأمر أعلاه لتحديث ملفات HTML.
"""
import hashlib
import html as html_lib
import json
import glob
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ("ar", "en")


def pick(lang, v):
    """A value is either the same in both languages, or a pair ("عربي", "English")."""
    return v[LANGS.index(lang)] if isinstance(v, tuple) else v


def out_path(lang, path):
    return path if lang == "ar" else f"en/{path}"


SITE = "https://shoroogmi.com/"


def share_btn(lang, path, title, extra_class=""):
    """زر «شارك»: يفتح قائمة المشاركة في الجوال، أو ينسخ الرابط في الحاسوب."""
    t = lambda a, e: a if lang == "ar" else e
    url = SITE + out_path(lang, path)
    title = re.sub(r"<[^>]+>", "", title).replace('"', "&quot;")
    return (f'<button class="share-btn{extra_class}" type="button" data-url="{url}" data-title="{title}">'
            f'<span aria-hidden="true">🔗</span> {t("شارك", "Share")}</button>')


def page(lang, path, key, title, body, desc, alt=None, icon=None):
    """path is relative to the language's root; alt is the same page in the other language
    (defaults to path)."""
    t = lambda a, e: a if lang == "ar" else e
    out = out_path(lang, path)
    p = "../" * out.count("/")          # to the site root (assets)
    h = p + ("" if lang == "ar" else "en/")  # to this language's home
    other = "en" if lang == "ar" else "ar"
    switch = p + out_path(other, alt or path)

    def act(k):
        return ' class="active"' if k == key or (k == "blog" and key.startswith("blog")) else ""

    def sub(k):
        return ' class="active"' if k == key else ""

    html = f"""<!doctype html>
<html lang="{lang}" dir="{t("rtl", "ltr")}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>{f'{chr(10)}  <link rel="icon" type="image/png" href="{p}{icon}">{chr(10)}  <link rel="apple-touch-icon" href="{p}{icon}">' if icon else ""}
  <meta name="description" content="{desc}">
  <link rel="alternate" hreflang="{other}" href="{switch}">
  <script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
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
            <a href="{h}blog/zawiya-36.html"{sub("blog-zawiya")}>{t("الزاوية ٣٦", "Corner 36")}</a>
          </div>
        </div>
        <a href="{h}books.html"{act("books")}>{t("أمتعة السفر", "Luggage")}</a>
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
        <a href="{h}blog/zawiya-36.html">{t("الزاوية ٣٦", "Corner 36")}</a>
        <a href="{h}books.html">{t("أمتعة السفر", "Luggage")}</a>
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
          <p class="audio-label">🎧 استمع للمقال بصوت حامد</p>
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


# شعار الزاوية ٣٦
ZAWIYA_LOGO = "assets/images/zawiya-36-logo.png"

# شريك الزاوية ٣٦
CREATIVE_FORUM = "https://creativeforum.sa/%d8%b7%d9%84%d8%a8-%d8%a7%d8%b3%d8%aa%d8%b4%d8%a7%d8%b1%d8%a9/"

# بصمة لكل ملف تنسيق/برمجة تُضاف إلى رابطه، فيحمّل المتصفح النسخة الجديدة فور أي تعديل بدل نسخته المخزّنة
ASSET_V = {f: hashlib.md5(open(os.path.join(ROOT, "assets", f), "rb").read()).hexdigest()[:8] for f in ("styles.css", "script.js")}


# ---------- shared content ----------
# الخواطر، الأحدث أولاً: (العنوان، التاريخ، النص)
ZAWIYA = []

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
FIELDS = {"العنوان": "title", "التاريخ": "date", "التصنيف": "tag", "الملخص": "excerpt"}
OPTIONAL_FIELDS = {"الوقت": "time", "النوع": "kind", "اقتباس": "quote", "Quote": "quote"}  # الوقت بنظام ٢٤ ساعة مثل 21:30، والنوع «قصيدة» يعرض الأبيات في المنتصف
# ترويسة الترجمة الإنجليزية (التاريخ والتصنيف والوقت تؤخذ من المقال العربي)
EN_FIELDS = {"Title": "title", "Excerpt": "excerpt"}

# تصنيفات «رحلات طويلة» بالترتيب الذي تظهر به أزرار الفرز. «التصنيف» في كل مقال يجب أن يكون واحدًا منها.
CATEGORIES = ["تأملات في القرآن والسنة", "شعب العلاقة مع القرآن", "مقالات نفسية واجتماعية", "مقالات فكرية", "مقالات تربوية",
              "مقالات إعلامية", "الذكاء الاصطناعي", "الشهرة والمشاهير", "القيادة", "قصائد"]
# المقال الذي تصنيفه «الزاوية ٣٦» يظهر في صفحة الزاوية ٣٦ لا في رحلات طويلة
ZAWIYA_TAG = "الزاوية ٣٦"
# اسم كل تصنيف في النسخة الإنجليزية
CATEGORIES_EN = {
    "تأملات في القرآن والسنة": "Reflections on the Quran & Sunnah",
    "شعب العلاقة مع القرآن": "Branches of the Relationship with the Quran",
    "مقالات نفسية واجتماعية": "Psychological & Social Essays",
    "مقالات فكرية": "Intellectual Essays",
    "مقالات تربوية": "Parenting & Education Essays",
    "مقالات إعلامية": "Media Essays",
    "الذكاء الاصطناعي": "Artificial Intelligence",
    "الشهرة والمشاهير": "Fame & Celebrities",
    "القيادة": "Leadership",
    ZAWIYA_TAG: "Corner 36",
    "قصائد": "Poems",
}


IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")


def read_md(path, fields):
    """ترويسة (مفتاح: قيمة) ثم سطر فارغ ثم النص.
    في النص: سطر يبدأ بـ ## عنوان فرعي، وسطر يبدأ بـ > اقتباس، والباقي فقرات."""
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    head, _, body = text.strip().partition("\n\n")
    meta = {}
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
        # فقرة كل أسطرها صور: ![وصف](اسم-الملف.jpg) — الملفات في assets/images
        if lines and all(IMG_RE.fullmatch(line) for line in lines):
            for line in lines:
                src = IMG_RE.fullmatch(line).group(2)
                if not os.path.exists(os.path.join(ROOT, "assets", "images", src)):
                    raise SystemExit(f"{path}: الصورة {src} غير موجودة في assets/images")
            blocks.append(("img", "\n".join(lines)))
            continue
        para = " ".join(lines)
        if para.startswith("## "):
            blocks.append(("h2", para[3:]))
        elif para.startswith("> "):
            blocks.append(("quote", para[2:]))
        elif para:
            blocks.append(("p", para))
    return meta, blocks


def load_article(path):
    meta, blocks = read_md(path, FIELDS)
    # أكثر من تصنيف يُفصل بفاصلة: «تأملات في القرآن والسنة، مقالات نفسية واجتماعية»
    meta["tag"] = tuple(t.strip() for t in re.split(r"[،,]", meta["tag"]) if t.strip())
    for t in meta["tag"]:
        if t not in CATEGORIES and t != ZAWIYA_TAG:
            raise SystemExit(f"{path}: التصنيف «{t}» غير معروف. التصنيفات المتاحة: {'، '.join(CATEGORIES)}")
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
            title, excerpt = em(en["title"]), em(en["excerpt"])
            quote = em(en.get("quote") or en["excerpt"])
            blocks = [(k, em(x)) for k, x in en_blocks]
            tags = tuple(CATEGORIES_EN[t] for t in m["tag"])
        else:
            title, excerpt, tags = m["title"], m["excerpt"], m["tag"]
            quote = m.get("quote") or excerpt
        out.append({
            "slug": slug, "tag": tags, "zawiya": ZAWIYA_TAG in m["tag"], "title": title, "excerpt": excerpt, "quote": quote, "blocks": blocks, "poem": poem,
            "date": fmt_date(lang, m["date"]), "read": read_time(lang, blocks),
            "time": fmt_time(lang, m["time"]) if m.get("time") else "",
            "minutes": word_count(blocks) / 200,
        })
    return out


def tags_html(tags, indent):
    spans = "".join(f'<span class="tag">{t}</span>' for t in tags)
    return f'{indent}<div class="tags">{spans}</div>' if len(tags) > 1 else indent + spans


# محطات جواز سفر بالترتيب: (أيقونة، النص — يقبل <b> للتأكيد، إيموجي الشارة، نوع خاص اختياري)
STATIONS = [
    ("🐪", ("<b>١٩٩٩</b> - السعودية", "<b>1999</b> - Saudi Arabia"), "👶", "start"),
    ("🎓", ("<b>بكالوريوس علاقات عامة، إعلام واتصال</b> - جامعة أم القرى، مكة المكرمة، ٢٠٢٠.",
           "<b>Bachelor's in Public Relations, Media and Communication</b> - Umm Al-Qura University, Makkah, 2020."), "🎉", ""),
    ("✍️", ("<b>كاتبة إعلانات وسيناريو</b> لما يزيد عن عشرين جهة.",
           "<b>Advertising copywriter and scriptwriter</b> for more than twenty organizations."), "📢🎬", ""),
    ("🧳", ("<b>ماجستير إعلام سياحي</b>، جامعة الملك خالد، أبها، ٢٠٢٤.",
           "<b>Master's in Tourism Media</b>, King Khalid University, Abha, 2024."), "🎓✈️", ""),
    ("🏆", ("<b>جائزة أدب العزلة</b>، هيئة الأدب والنشر والترجمة، ٢٠٢٠.",
           "<b>Literature of Solitude Award</b>, Literature, Publishing and Translation Commission, 2020."), "🥇", "award"),
    ("🔬", ("نشرت <b>ستة بحوث علمية</b>.", "I published <b>six research papers</b>."), "📜📜📜", ""),
    ("📖", ("<b>حفظ القرآن</b> ٢٠٢٦.", "<b>Memorized the Quran</b>, 2026."), "✨", "final"),
]

# كتبي: (العنوان، العنوان الفرعي، الناشر، السنة، الرابط، صورة الغلاف الأمامي، صورة الغلاف الخلفي، فقرات الوصف)
# الصور في assets/books/
BOOKS = [
    (("يا بشرى هذا غلام", "Ya Bushra Hadha Ghulam"),
     ("تأملات في حسن الظن بالله واليقين والبشرى", "Reflections on Thinking Well of Allah, Certainty, and Glad Tidings"),
     ("جمعية أدباء الأحساء", "Al-Ahsa Writers Association · In Arabic"), ("٢٠٢٦", "2026"),
     "https://elitepublishsa.com/products/%D9%8A%D8%A7%D8%A8%D8%B4%D8%B1%D9%89-%D9%87%D8%B0%D8%A7-%D8%BA%D9%84%D8%A7%D9%85-%D8%B4%D8%B1%D9%88%D9%82-%D8%A7%D9%84%D8%AD%D9%85%D8%A7%D8%AF%D9%8A",
     "ya-bushra-front.jpg", "ya-bushra-back.jpg", [
         ("لا أعرف كتابًا كتبته من قلبي مخلوطًا بدمي مثل (يا بشرى هذا غلام: تأملات في حسن الظن بالله واليقين والبشرى)، وأعتقد أن هذه المعاني الثلاثة ركائز إيمانية هامة لتعميق علاقتنا مع ربٍّ رحيمٍ ودود، وليست مزاجًا متفائلًا طارئًا.",
          "I know of no book I have written from my heart, mixed with my blood, like (Ya Bushra Hadha Ghulam: Reflections on Thinking Well of Allah, Certainty, and Glad Tidings). I believe these three meanings are important pillars of faith for deepening our relationship with a Merciful, Loving Lord, not a passing optimistic mood."),
         ("نشرت الكتاب إلكترونيًا، وقد لاقى استحسانًا وانتشارًا لم أتوقعه، ورأيت أثر كلماته بفضل الله فيمن حولي، وقد طبعناه الآن في نسخة ورقية جديدة، مُرتّبةٍ مفهرسةٍ مُدقّقةٍ، وأضفنا إليه مقالاتٍ جديدة، وجدتها مُرضية تليق بقارئي الكريم.",
          "I published the book electronically, and it met with an appreciation and a reach I did not expect, and by the grace of Allah I saw the effect of its words on those around me. We have now printed it in a new paper edition, organized, indexed and proofread, and added new articles to it that I found satisfying and worthy of my dear reader."),
     ]),
]

EMAIL = "shoroogmi1@gmail.com"
# شعارات التطبيقات (من مكتبة Simple Icons، رخصة CC0)
BRAND_ICONS = {
    "gmail": "M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z",
    "x": "M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z",
    "instagram": "M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077",
    "whatsapp": "M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z",
    "substack": "M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z",
    "facebook": "M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z",
}


CONTACTS = [
    # (الشعار من BRAND_ICONS، المنصة، النص الظاهر، الرابط أو None، ملاحظة اختيارية)
    ("gmail", ("البريد", "Email"), EMAIL, f"mailto:{EMAIL}"),
    ("x", ("إكس", "X"), "@shoroogmi", "https://x.com/shoroogmi"),
    ("instagram", ("انستغرام", "Instagram"), "@shoroogmi", "https://www.instagram.com/shoroogmi"),
    ("whatsapp", ("واتساب", "WhatsApp"), "shoroogmi", None),
    ("whatsapp", ("قناة واتساب", "WhatsApp Channel"), ("تابع القناة", "Follow the channel"), "https://whatsapp.com/channel/0029Vb6mYujKmCPUKLgBbW23"),
    ("substack", ("سبستاك", "Substack"), "@shoroogmi", "https://substack.com/@shoroogmi"),
    ("facebook", ("فيسبوك", "Facebook"), ("صفحتي على فيسبوك", "My Facebook page"), "https://www.facebook.com/share/1HsZnfQwpn/?mibextid=wwXIfr"),
]


LEGAL_UPDATED = ("١١ أكتوبر ٢٠٢٦", "October 11, 2026")

# الصفحات القانونية: (عنوان القسم، [فقرات]) بالعربية ثم بالإنجليزية
PRIVACY = [
    (("مقدمة", "Introduction"),
     [("هذا موقع شخصي للكاتبة شروق المحمادي (shoroogmi.com). لا يتطلب تسجيل حساب، ولا يبيع بيانات زوّاره ولا يؤجرها لأحد. توضّح هذه الصفحة ما يُجمع عند استخدامك الموقع، ولماذا، وأين يُحفظ.",
       "This is the personal website of the writer Shoroog Almehmadi (shoroogmi.com). It requires no account, and it never sells or rents its visitors' data to anyone. This page explains what is collected when you use the site, why, and where it is kept.")]),
    (("ما الذي نجمعه؟", "What we collect"),
     [("<b>عدّادات مجهولة الهوية:</b> عدد زوّار الموقع، والقرّاء الدائمين، والقراءات المكتملة، والإعجابات بكل مقال. هي أرقام إجمالية فقط تُحفظ في خدمة Abacus، ولا تتضمن اسمك ولا بريدك.",
       "<b>Anonymous counters:</b> the number of site visitors, regular readers, completed reads and likes for each article. These are totals only, kept with the Abacus service, and they never include your name or email."),
      ("<b>التعليقات على المقالات:</b> الاسم الذي تكتبه ونص تعليقك. تُحفظ في خدمة Supabase وتظهر لكل زوّار المقال.",
       "<b>Comments on articles:</b> the name you type and the text of your comment. They are stored with the Supabase service and are visible to everyone who reads the article."),
      ("<b>رسائل «برج المراقبة»:</b> اسمك، وبريدك إن اخترت كتابته، وموضوع الرسالة ونصها. تُرسل عبر خدمة FormSubmit إلى بريد الكاتبة، ولا تُنشر.",
       "<b>Control Tower messages:</b> your name, your email if you choose to give it, and your message. They are sent through the FormSubmit service to the writer's inbox and are never published."),
      ("<b>التقييم في الصفحة الرئيسية («قيّمنا»):</b> عدد النجوم، وتعليقك، واسمك إن كتبته. يُحفظ في خدمة Supabase ويُرسل إلى بريد الكاتبة. التقييمات الإيجابية (٤ أو ٥ نجوم مع تعليق) قد تظهر للزوّار في الصفحة الرئيسية مع الاسم الذي كتبته، وما سواها لا يُنشر.",
       "<b>The home-page rating (“Rate Us”):</b> your stars, your comment, and your name if you give one. It is stored with the Supabase service and emailed to the writer. Positive ratings (4 or 5 stars with a comment) may be shown to visitors on the home page with the name you gave; all others are never published.")]),
    (("ما يُحفظ في متصفحك", "What is stored in your browser"),
     [("يحفظ الموقع في متصفحك (التخزين المحلي localStorage) معلومات صغيرة تبقى في جهازك ولا تُرسل إلى أحد: تفضيلك للوضع الليلي أو النهاري، وهل سبق أن أعجبك مقال أو أكملت قراءته (حتى لا يُحسب مرتين)، وتاريخ أول زيارة لك، ووقت آخر تعليق كتبته. يمكنك مسحها في أي وقت من إعدادات متصفحك.",
       "The site keeps a few small notes in your browser's local storage. They stay on your device and are not sent anywhere: your light or dark theme, whether you have already liked or finished an article (so it isn't counted twice), the date of your first visit, and the time of your last comment. You can clear them at any time from your browser settings."),
      ("لا يضع الموقع ملفات تعريف ارتباط (Cookies) خاصة به، ولا يستعمل أدوات تتبّع إعلانية.",
       "The site sets no cookies of its own and uses no advertising trackers.")]),
    (("الخدمات الخارجية", "Third-party services"),
     [("يعتمد الموقع على خدمات خارجية لكل منها سياسة خصوصية خاصة بها، وقد يسجّل بعضها عنوان IP لأسباب تقنية: GitHub Pages (استضافة الموقع)، وGoogle Fonts (الخطوط)، وAbacus (العدّادات)، وSupabase (التعليقات)، وFormSubmit (الرسائل والتقييمات).",
       "The site relies on outside services, each with its own privacy policy, and some may log your IP address for technical reasons: GitHub Pages (hosting), Google Fonts (typefaces), Abacus (counters), Supabase (comments) and FormSubmit (messages and ratings)."),
      ("التسجيلات الصوتية للمقالات مولّدة مسبقًا من نص المقالات، ولا يُرسل أي شيء عنك عند تشغيلها.",
       "The audio recordings of the articles are generated in advance from the article text; nothing about you is sent when you play them.")]),
    (("كيف نستخدم هذه المعلومات؟", "How we use this information"),
     [("للرد على رسائلك، ولعرض التعليقات، ولمعرفة عدد القرّاء وما يحبونه. لا إعلانات، ولا بيع، ولا مشاركة لأغراض تسويقية.",
       "To reply to your messages, to show comments, and to know how many people read and what they enjoy. No advertising, no selling, no sharing for marketing.")]),
    (("حقوقك", "Your rights"),
     [(f'يمكنك طلب حذف تعليقك أو رسالتك في أي وقت بمراسلة <a href="mailto:{EMAIL}">{EMAIL}</a>.',
       f'You can ask for your comment or message to be deleted at any time by writing to <a href="mailto:{EMAIL}">{EMAIL}</a>.')]),
    (("التعديلات على هذه السياسة", "Changes to this policy"),
     [("قد تُحدَّث هذه السياسة من حين لآخر، ويظهر تاريخ آخر تحديث في أعلى الصفحة.",
       "This policy may be updated from time to time; the date of the latest update appears at the top of the page.")]),
]

TERMS = [
    (("قبول الشروط", "Acceptance"),
     [("باستخدامك موقع shoroogmi.com فأنت توافق على هذه الشروط. إن لم توافق عليها فنرجو ألا تستخدم الموقع.",
       "By using shoroogmi.com you agree to these terms. If you do not agree, please do not use the site.")]),
    (("حقوق المحتوى ومشاركته", "Sharing the content"),
     [("<b>المقالات والنصوص الدينية</b> (مثل «تأملات في القرآن والسنة» و«شعب العلاقة مع القرآن»): يمكن اقتباسها ونشرها دون ذكر اسم الكاتبة، ودون إذن مسبق.",
       "<b>Religious articles and texts</b> (such as “Reflections on the Quran &amp; Sunnah” and “Branches of the Relationship with the Quran”): you may quote and publish them without the writer's name and without prior permission."),
      ("<b>المقالات الإعلامية، ومقالات الذكاء الاصطناعي، والموضوعات الثقافية:</b> يمكن مشاركتها ونسخها كاملة، بشرط ذكر اسم الكاتبة (شروق المحمادي) أو الإشارة إلى الموقع (shoroogmi.com).",
       "<b>Media articles, artificial-intelligence articles and cultural topics:</b> you may share and copy them in full, provided you credit the writer (Shoroog Almehmadi) or mention the website (shoroogmi.com).")]),
    (("ما ليس ملكًا للكاتبة", "Content owned by others"),
     [("حقوق أغلفة الكتب والأعمال المقتبس منها محفوظة لأصحابها، وتُعرض للتعريف والإشارة فقط. والترجمات الإنجليزية لمعاني الآيات مأخوذة من ترجمة Saheeh International، وترجمات الأحاديث من الترجمات المنشورة على sunnah.com.",
       "Book covers and quoted works remain the property of their owners and are shown for reference only. The English renderings of Quranic verses are from the Saheeh International translation, and hadith translations are those published on sunnah.com.")]),
    (("التعليقات والرسائل", "Comments and messages"),
     [("أنت مسؤول عمّا تكتبه. يُمنع نشر الإساءة أو الشتم أو التحريض أو الإعلانات أو ما يخالف الأنظمة. وللكاتبة حذف أي تعليق دون إشعار.",
       "You are responsible for what you write. Abuse, insults, incitement, advertising and anything unlawful are not allowed, and the writer may remove any comment without notice.")]),
    (("التسجيلات الصوتية والترجمة", "Audio and translation"),
     [("التسجيلات الصوتية بصوت آلي مولَّد، وقد يقع فيها خطأ في النطق، والمرجع هو النص المكتوب. والنص العربي هو الأصل إذا اختلف عن الترجمة الإنجليزية.",
       "The audio recordings use a computer-generated voice and may mispronounce a word; the written text is the reference. Where the English translation differs from the Arabic, the Arabic original prevails.")]),
    (("إخلاء المسؤولية", "Disclaimer"),
     [("محتوى الموقع تأملات وآراء شخصية للكاتبة، ولا يُعدّ فتوى شرعية، ولا استشارة نفسية أو طبية أو قانونية متخصصة.",
       "The content of this site is the writer's personal reflection and opinion. It is not a religious ruling (fatwa), nor specialist psychological, medical or legal advice.")]),
    (("الروابط الخارجية", "External links"),
     [("قد يحتوي الموقع على روابط لمواقع أخرى، ولا تتحمل الكاتبة مسؤولية محتواها أو سياساتها.",
       "The site may link to other websites; the writer is not responsible for their content or policies.")]),
    (("تعديل الشروط", "Changes to these terms"),
     [(f'قد تُعدَّل هذه الشروط من حين لآخر، ويظهر تاريخ آخر تحديث في أعلى الصفحة. للتواصل: <a href="mailto:{EMAIL}">{EMAIL}</a>.',
       f'These terms may change from time to time; the date of the latest update appears at the top of the page. Contact: <a href="mailto:{EMAIL}">{EMAIL}</a>.')]),
]


def build(lang):
    t = lambda a, e: a if lang == "ar" else e
    L = lambda v: pick(lang, v)
    num = ar if lang == "ar" else str
    fwd = t("←", "→")
    q1, q2 = t("«", "“"), t("»", "”")
    me = t("شروق المحمادي", "Shoroog Almehmadi")

    ALL_ARTICLES = articles_for(lang)
    ARTICLES = [a for a in ALL_ARTICLES if not a["zawiya"]]
    ZAWIYA_ARTICLES = [a for a in ALL_ARTICLES if a["zawiya"]]
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

    def zawiya_card(i, z):
        title, date, text = z
        return f"""          <article class="note-card">
            <span class="note-num">#{num(i)}</span>
            <h3>{L(title)}</h3>
            <p>{L(text)}</p>
            <p class="meta">{fmt_date(lang, date)}</p>
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

    # ---------- Home ----------
    z0 = ZAWIYA_ARTICLES[0] if ZAWIYA_ARTICLES else None
    home = f"""    <section class="hero">
      <div class="sky" aria-hidden="true">
        <div class="sun"><span class="rays"></span></div>
        <span class="cloud c1"></span><span class="cloud c2"></span><span class="cloud c3"></span>
      </div>
      <div class="container hero-inner">
        <figure class="verse">
          <blockquote><span>{t("كلُّ شمسٍ لم تكُنْها ظلامُ", "Every sun that is not you is darkness")}</span></blockquote>
        </figure>
        <h1>{me}</h1>
        <p class="lead">{t("أيها القارئ: لنتفق! المقعد الأيمن مرة لي ومرة لك، وذلك طوال رحلتنا في سياحة العقول والأفكار والتجارب. طيب كابتن؟",
                           "Dear reader, let's make a deal! The right seat is mine one time and yours the next, all through our journey touring minds, ideas and experiences. Okay, Captain?")}</p>
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
          <a class="tile" href="blog/index.html"><span class="tile-icon">✍️</span><h3>{t("سجل الرحلات", "Travel Log")}</h3><p>{t("مقالات والزاوية ٣٦", "Articles and Corner 36")}</p></a>
          <a class="tile" href="books.html"><span class="tile-icon">📚</span><h3>{t("أمتعة السفر", "Luggage")}</h3><p>{t("كتب تسليك في الرحلة.", "Books to keep you company on the journey.")}</p></a>
        </div>
      </div>
    </section>

{latest("blog/", "blog/articles.html", hook=True) if ARTICLES else ""}
{f"""    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("من الزاوية ٣٦", "From Corner 36")}</h2>
          <a class="more" href="blog/zawiya-36.html">{t("افتح الزاوية", "Open the Corner")} {fwd}</a>
        </div>
        <blockquote class="quote">
          <p>{q1}{z0["quote"]}{q2}</p>
          <cite><a href="blog/articles/{z0["slug"]}.html">{z0["title"]}</a> · {z0["date"]}</cite>
        </blockquote>
      </div>
    </section>
""" if z0 else ""}

    <section class="section testimonials" hidden>
      <div class="container">
        <h2 class="section-title">{t("ماذا قال المسافرون؟", "What Travelers Said")}</h2>
        <div class="testimonial-list"></div>
      </div>
    </section>

    <section class="section">
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

    <section class="section cta">
      <div class="container cta-inner">
        <h2>{t("لديك فكرة أو سؤال؟", "Have an idea or a question?")}</h2>
        <p>{t("يسعدني أن أسمع منك دائماً.", "I'm always happy to hear from you.")}</p>
        <a href="contact.html" class="btn btn-primary">{t("برج المراقبة", "Control Tower")}</a>
      </div>
    </section>
"""
    page(lang, "index.html", "home", me, home,
         t("الموقع الشخصي لشروق المحمادي: جواز سفر، سجل الرحلات، أمتعة السفر، وبرج المراقبة.",
           "The personal website of Shoroog Almehmadi: Passport, Travel Log, Luggage, and Control Tower."))

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

    sira = page_head(t("جواز سفر", "Passport"), t("هبوط وصعود", "Landings and Takeoffs"),
                     t("مرتفعات شديدة، وهبوط قوي، تمالك قلبك حتى لا يسقط.",
                       "Steep climbs and hard drops: hold on to your heart so it doesn't fall."),
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
                     t("مقالات والزاوية ٣٦", "Articles and Corner 36")) + f"""
    <section class="section">
      <div class="container">
        <div class="blog-split">
          <a class="blog-door" href="articles.html">
            <span class="door-icon">✍️</span>
            <h2>{t("رحلات طويلة", "Long Journeys")}</h2>
            <p>{t("مقالات وتأملات بين الثقيلة والخفيفة.", "Essays and reflections, from the weighty to the light.")}</p>
            <span class="count">{num(len(ARTICLES))} {t("رحلات", "journeys")}</span>
          </a>
          <a class="blog-door night" href="zawiya-36.html">
            <span class="door-icon"><img class="door-logo" src="{"../" * out_path(lang, "blog/index.html").count("/")}{ZAWIYA_LOGO}" alt="" width="56" height="56"></span>
            <h2>{t("الزاوية ٣٦", "Corner 36")}</h2>
            <p>{t("مقالات حديثة نترجمها ونحوّرها بطريقتنا!", "Recent articles we translate and reshape our own way!")}</p>
            <span class="count">{num(len(ZAWIYA) + len(ZAWIYA_ARTICLES))} {t("مقالات", "articles")}</span>
          </a>
        </div>
      </div>
    </section>

{latest("", "articles.html") if ARTICLES else ""}
    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("أحدث مقالات الزاوية", "Latest from the Corner")}</h2>
          <a class="more" href="zawiya-36.html">{t("الزاوية ٣٦", "Corner 36")} {fwd}</a>
        </div>
        <div class="posts">
{chr(10).join(article_card(a) for a in ZAWIYA_ARTICLES[:3])}
        </div>
      </div>
    </section>
"""
    page(lang, "blog/index.html", "blog", f"{t('سجل الرحلات', 'Travel Log')} · {me}", blog,
         t("سجل رحلات شروق المحمادي: رحلات طويلة والزاوية ٣٦.", "Shoroog Almehmadi's travel log: Long Journeys and Corner 36."))

    crumbs_tpl = (f'        <nav class="crumbs" aria-label="{t("مسار التنقل", "Breadcrumb")}"><a href="index.html">'
                  f'{t("سجل الرحلات", "Travel Log")}</a> / <span>{{}}</span></nav>\n')

    # ---------- Articles ----------
    cats = CATEGORIES if lang == "ar" else [CATEGORIES_EN[c] for c in CATEGORIES]
    articles = page_head(t("سجل الرحلات", "Travel Log"), t("رحلات طويلة", "Long Journeys"),
                         t("تأملات في القرآن والسنة، ومقالات نفسية واجتماعية وفكرية، وقصائد.",
                           "Reflections on the Quran and Sunnah, psychological, social and intellectual essays, and poems."),
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
        <div class="posts" data-filterable>
{chr(10).join(article_card(a) for a in ARTICLES)}
        </div>
        <p class="empty"{" hidden" if ARTICLES else ""}>{t("لا توجد رحلات بعد.", "No journeys yet.")}</p>
      </div>
    </section>
"""
    page(lang, "blog/articles.html", "blog-articles", f"{t('رحلات طويلة', 'Long Journeys')} · {me}", articles,
         t("رحلات شروق المحمادي الطويلة.", "Shoroog Almehmadi's long journeys."))

    # ---------- Zawiya 36 ----------
    z_root = "../" * out_path(lang, "blog/zawiya-36.html").count("/")
    zawiya = page_head(t("سجل الرحلات", "Travel Log"), t("الزاوية ٣٦", "Corner 36"),
                       t("مقالات حديثة نترجمها ونحوّرها بطريقتنا!",
                         "Recent articles we translate and reshape our own way!"),
                       crumbs_tpl.format(t("الزاوية ٣٦", "Corner 36")),
                       f'        <p class="partner">{t("بالتعاون مع", "In collaboration with")} <a href="{CREATIVE_FORUM}" target="_blank" rel="noopener">{t("نادي ملتقى المبدعين الثقافي", "the Creative Forum Cultural Club")}</a></p>\n',
                       f'        <img class="page-logo" src="{z_root}{ZAWIYA_LOGO}" alt="{t("شعار الزاوية ٣٦", "Corner 36 logo")}" width="96" height="96">\n') + f"""
    <section class="section">
      <div class="container">{f"""
        <div class="posts zawiya-posts">
{chr(10).join(article_card(a) for a in ZAWIYA_ARTICLES)}
        </div>""" if ZAWIYA_ARTICLES else ""}
{f"""        <div class="notes">
{chr(10).join(zawiya_card(len(ZAWIYA) - i, z) for i, z in enumerate(ZAWIYA))}
        </div>""" if ZAWIYA else ""}
      </div>
    </section>
"""
    page(lang, "blog/zawiya-36.html", "blog-zawiya", f"{t('الزاوية ٣٦', 'Corner 36')} · {me}", zawiya,
         t("الزاوية ٣٦: مقالات حديثة تترجمها شروق المحمادي وتحوّرها بطريقتها.", "Corner 36: recent articles translated and reshaped by Shoroog Almehmadi."),
         icon=ZAWIYA_LOGO)

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

    def book_card(title, sub, pub, year, url, front, back, desc):
        title = L(title)
        book_id = "book-" + os.path.splitext(front)[0].replace("-front", "")
        link = (f'\n              <a class="btn btn-primary book-link" href="{url}" target="_blank" rel="noopener">🛒 {t("زيارة المتجر", "Visit the store")}</a>'
                if url else "")
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

    books = page_head(t("أمتعة السفر", "Luggage"), t("كتب ماتعة!", "Delightful Books!"), "") + f"""
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

    topics = [("سؤال", "Question"), ("اقتراح", "Suggestion"), ("تعاون", "Collaboration"), ("تعليق على رحلة", "Comment on a journey")]
    contact = page_head(t("برج المراقبة", "Control Tower"), t("تعيسًا أو سعيدًا كلِّم برج المراقبة", "Unhappy or happy, call the Control Tower"),
                        t("أي سؤال، وأي اقتراح، وحتى تعاون؛ موجودة وبرد لك -ما دمتُ حيًا-.",
                          "Any question, any suggestion, even a collaboration: I'm here and I'll get back to you, as long as I live.")) + f"""
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
            figs = []
            for line in text.split("\n"):
                alt, src = IMG_RE.fullmatch(line).groups()
                url = f"{art_root}assets/images/{src}"
                cap = f"<figcaption>{alt}</figcaption>" if alt else ""
                figs.append(f'<figure class="post-figure"><a href="{url}" target="_blank" rel="noopener">'
                            f'<img src="{url}" alt="{alt}" loading="lazy"></a>{cap}</figure>')
            if len(figs) == 1:
                return "        " + figs[0]
            return f'        <div class="post-gallery">{"".join(figs)}</div>'
        if kind == "h2":
            return f"        <h2>{text}</h2>"
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
        group = ZAWIYA_ARTICLES if a["zawiya"] else ARTICLES
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
        <nav class="crumbs" aria-label="{t("مسار التنقل", "Breadcrumb")}"><a href="../index.html">{t("سجل الرحلات", "Travel Log")}</a> / {f'<a href="../zawiya-36.html">{t("الزاوية ٣٦", "Corner 36")}</a>' if a["zawiya"] else f'<a href="../articles.html">{t("رحلات طويلة", "Long Journeys")}</a>'}</nav>
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
{"" if a["poem"] or excerpt in lead_blocks else f'        <p class="excerpt">{excerpt}</p>{chr(10)}'}{render_body(a)}
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
"""
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
        page(lang, f"blog/articles/{slug}.html", "blog-articles", f"{plain(title)} · {me}", body, plain(excerpt), alt)
    return len(ARTICLES)


n_ar = build("ar")
n_en = build("en")
print(f"تم: {n_ar} مقالات بالعربية، و{n_en} بالإنجليزية")
