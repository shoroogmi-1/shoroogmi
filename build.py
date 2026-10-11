"""يولّد صفحات الموقع بالعربية (في جذر الموقع) وبالإنجليزية (في مجلد en/).

التشغيل:  python3 build.py

- المقالات: ملف لكل مقال في content/articles/، وترجمته الإنجليزية بالاسم نفسه في content/en/articles/ (انظري README.md).
- الزاوية ٣٦ والكتب ومحطات جواز السفر والتواصل: قوائم داخل هذا الملف (ابحثي عن ZAWIYA و BOOKS و STATIONS و CONTACTS).
  النص الذي يختلف بين اللغتين يُكتب زوجًا: ("النص العربي", "English text").
- بعد أي تعديل شغّلي الأمر أعلاه لتحديث ملفات HTML.
"""
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


def page(lang, path, key, title, body, desc, alt=None):
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
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <link rel="alternate" hreflang="{other}" href="{switch}">
  <script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Readex+Pro:wght@300;400;500;600;700&family=Amiri+Quran&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p}assets/styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container nav">
      <a href="{h}index.html" class="logo"><span class="logo-sun" aria-hidden="true"></span>{t("شروق المحمادي", "Shoroog Almehmadi")}</a>
      <button class="menu-toggle" aria-label="{t("فتح القائمة", "Open menu")}" aria-expanded="false">☰</button>
      <nav class="nav-links" aria-label="{t("القائمة الرئيسية", "Main menu")}">
        <a href="{h}index.html"{act("home")}>{t("صالة المغادرة", "Departure Lounge")}</a>
        <a href="{h}sira.html"{act("sira")}>{t("جواز السفر", "Passport")}</a>
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
        <a href="{h}sira.html">{t("جواز السفر", "Passport")}</a>
        <a href="{h}blog/articles.html">{t("رحلات طويلة", "Long Journeys")}</a>
        <a href="{h}blog/zawiya-36.html">{t("الزاوية ٣٦", "Corner 36")}</a>
        <a href="{h}books.html">{t("أمتعة السفر", "Luggage")}</a>
        <a href="{h}contact.html">{t("برج المراقبة", "Control Tower")}</a>
      </nav>
      <p class="copy">© <span class="year"></span> {t("جميع الحقوق محفوظة", "All rights reserved")}</p>
    </div>
  </footer>

  <script src="{p}assets/script.js"></script>
</body>
</html>
"""
    full = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)


def page_head(eyebrow, heading, lead, crumbs=""):
    return f"""    <section class="page-hero">
      <div class="clouds" aria-hidden="true"><span class="cloud c1"></span><span class="cloud c2"></span></div>
      <div class="container">
{crumbs or f'        <p class="eyebrow">{eyebrow}</p>{chr(10)}'}        <h1>{heading}</h1>
        <p class="lead">{lead}</p>
      </div>
    </section>
"""


# ---------- shared content ----------
# الخواطر، الأحدث أولاً: (العنوان، التاريخ، النص)
ZAWIYA = [
    (("الضوء لا يستأذن", "Light Doesn't Knock"), "2026-10-01",
     ("يدخل الضوء من أصغر شقّ في النافذة. هكذا هي الأفكار الجيدة: لا تحتاج إلا إلى فرصة صغيرة.",
      "Light comes in through the smallest crack in the window. Good ideas are like that: all they need is a small chance.")),
    (("قهوة الصباح", "Morning Coffee"), "2026-09-24",
     ("ليست القهوة ما يوقظني، بل الدقائق الهادئة التي أمنحها لنفسي قبل أن يبدأ اليوم.",
      "It isn't the coffee that wakes me, but the quiet minutes I give myself before the day begins.")),
    (("عن البدايات", "On Beginnings"), "2026-09-17",
     ("كل بداية تبدو صغيرة من الداخل، وكبيرة جداً حين ننظر إليها بعد عام.",
      "Every beginning looks small from the inside, and very big when we look back at it a year later.")),
    (("سؤال الأسبوع", "Question of the Week"), "2026-09-10",
     ("ما الشيء الذي تؤجله لأنك تنتظر أن تصبح جاهزاً؟ ربما الجاهزية تأتي بعد الخطوة، لا قبلها.",
      "What are you putting off because you're waiting to be ready? Maybe readiness comes after the step, not before it.")),
    (("غيمة عابرة", "A Passing Cloud"), "2026-09-03",
     ("الأيام الثقيلة مثل الغيوم: تحجب الشمس قليلاً، لكنها لا تطفئها.",
      "Heavy days are like clouds: they hide the sun a little, but they don't put it out.")),
    (("رسالة إلى نفسي", "A Note to Myself"), "2026-08-27",
     ("تمهّلي. ليس كل ما هو مهم عاجلاً، وليس كل ما هو عاجل مهماً.",
      "Slow down. Not everything important is urgent, and not everything urgent is important.")),
]

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
    return sum(len(t.split()) for _, t in blocks)


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
OPTIONAL_FIELDS = {"الوقت": "time", "النوع": "kind"}  # الوقت بنظام ٢٤ ساعة مثل 21:30، والنوع «قصيدة» يعرض الأبيات في المنتصف
# ترويسة الترجمة الإنجليزية (التاريخ والتصنيف والوقت تؤخذ من المقال العربي)
EN_FIELDS = {"Title": "title", "Excerpt": "excerpt"}

# تصنيفات «رحلات طويلة» بالترتيب الذي تظهر به أزرار الفرز. «التصنيف» في كل مقال يجب أن يكون واحدًا منها.
CATEGORIES = ["تأملات في القرآن والسنة", "شعب العلاقة مع القرآن", "مقالات نفسية واجتماعية", "مقالات فكرية", "مقالات تربوية", "الشهرة والمشاهير", "قصائد"]
# اسم كل تصنيف في النسخة الإنجليزية
CATEGORIES_EN = {
    "تأملات في القرآن والسنة": "Reflections on the Quran & Sunnah",
    "شعب العلاقة مع القرآن": "Branches of the Relationship with the Quran",
    "مقالات نفسية واجتماعية": "Psychological & Social Essays",
    "مقالات فكرية": "Intellectual Essays",
    "مقالات تربوية": "Parenting & Education Essays",
    "الشهرة والمشاهير": "Fame & Celebrities",
    "قصائد": "Poems",
}


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
        para = " ".join(line.strip() for line in para.splitlines())
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
        if t not in CATEGORIES:
            raise SystemExit(f"{path}: التصنيف «{t}» غير معروف. التصنيفات المتاحة: {'، '.join(CATEGORIES)}")
    if meta.get("time") and not re.fullmatch(r"\d{1,2}:\d{2}", meta["time"]):
        raise SystemExit(f"{path}: اكتبي الوقت بهذا الشكل 21:30")
    slug = os.path.splitext(os.path.basename(path))[0]
    return meta, slug, blocks


# newest first
_loaded = sorted((load_article(f) for f in glob.glob(os.path.join(ROOT, "content", "articles", "*.md"))),
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
            blocks = [(k, em(x)) for k, x in en_blocks]
            tags = tuple(CATEGORIES_EN[t] for t in m["tag"])
        else:
            title, excerpt, tags = m["title"], m["excerpt"], m["tag"]
        out.append({
            "slug": slug, "tag": tags, "title": title, "excerpt": excerpt, "blocks": blocks, "poem": poem,
            "date": fmt_date(lang, m["date"]), "read": read_time(lang, blocks),
            "time": fmt_time(lang, m["time"]) if m.get("time") else "",
            "minutes": word_count(blocks) / 200,
        })
    return out


def tags_html(tags, indent):
    spans = "".join(f'<span class="tag">{t}</span>' for t in tags)
    return f'{indent}<div class="tags">{spans}</div>' if len(tags) > 1 else indent + spans


# محطات جواز السفر بالترتيب: (أيقونة، النص — يقبل <b> للتأكيد، إيموجي الشارة، نوع خاص اختياري)
STATIONS = [
    ("🐪", ("<b>١٩٩٩</b> - السعودية", "<b>1999</b> - Saudi Arabia"), "👶", "start"),
    ("📕", ("<b>«نكت ونكت»</b> أول كتاب سخيف قرأته وأنا في الابتدائية.",
           "<b>“Nukat wa Nukat”</b> (Jokes and More Jokes), the first silly book I read, back in elementary school."), "🤡", ""),
    ("🎓", ("<b>بكالوريوس علاقات عامة، إعلام واتصال</b> - جامعة أم القرى، مكة المكرمة، ٢٠٢٠.",
           "<b>Bachelor's in Public Relations, Media and Communication</b> - Umm Al-Qura University, Makkah, 2020."), "🎉", ""),
    ("✍️", ("<b>كاتبة إعلانات وسيناريو</b> لما يزيد عن عشرين جهة.",
           "<b>Advertising copywriter and scriptwriter</b> for more than twenty organizations."), "📢🎬", ""),
    ("🧳", ("<b>ماجستير إعلام سياحي</b>، جامعة الملك خالد، أبها، ٢٠٢٤.",
           "<b>Master's in Tourism Media</b>, King Khalid University, Abha, 2024."), "🎓✈️", ""),
    ("🧠", ("قرأت <b>«سيكولوجية الجماهير»</b> ٣ مرات! وذلك فقط لأفهم معنى الطبقات الاجتماعية والعِرق الذي لم أفهمه إلا في ٢٠٢٦.",
           "I read <b>“The Crowd: A Study of the Popular Mind”</b> 3 times! Just to understand what social classes and race mean, which I didn't understand until 2026."), "🔁🔁🔁", ""),
    ("🏆", ("<b>جائزة أدب العزلة</b>، هيئة الأدب والنشر والترجمة، ٢٠٢٠.",
           "<b>Literature of Solitude Award</b>, Literature, Publishing and Translation Commission, 2020."), "🥇", "award"),
    ("🗑️", ("رميت أول كتاب في سلة المهملات <b>«قانون الجذب»</b>، ثم توالت الكتب الساقطة بعدها. إنه لإنجاز أن تفرّق بين الجهل والعلم! وتضع كلًّا منهما في مكانه الصحيح.",
            "The first book I threw in the trash was <b>“The Law of Attraction”</b>, and more failed books followed. It's an achievement to tell ignorance from knowledge! And to put each in its rightful place."), "⚔️🗑️", ""),
    ("🔬", ("نشرت <b>ستة بحوث علمية</b>.", "I published <b>six research papers</b>."), "📜📜📜", ""),
    ("📘", ("<b>«Positive Thinking»</b> أول كتاب إنجليزي قرأته.",
           "<b>“Positive Thinking”</b>, the first English book I read."), "🇬🇧", ""),
    ("📖", ("<b>حفظت القرآن</b>: وهذا هو الإنجاز الحقيقي الذي أستشعر طعمه ونكهته بين شهادات لا نكهة لها.",
           "<b>I memorized the Quran</b>: this is the real achievement, the one whose taste and flavor I savor among certificates that have no flavor."), "✨", "final"),
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
CONTACTS = [
    # (أيقونة، المنصة، النص الظاهر، الرابط أو None، ملاحظة اختيارية)
    ("✉️", ("البريد", "Email"), EMAIL, f"mailto:{EMAIL}"),
    ("𝕏", ("إكس", "X"), "@shoroogmi", "https://x.com/shoroogmi"),
    ("📷", ("انستغرام", "Instagram"), "@shoroogmi", "https://www.instagram.com/shoroogmi"),
    ("💬", ("واتساب", "WhatsApp"), "shoroogmi", None, ("مفتاح الواتس: 6006", "WhatsApp key: 6006")),
    ("📢", ("قناة واتساب", "WhatsApp Channel"), ("تابع القناة", "Follow the channel"), "https://whatsapp.com/channel/0029Vb6mYujKmCPUKLgBbW23"),
    ("📰", ("سبستاك", "Substack"), "@shoroogmi", "https://substack.com/@shoroogmi"),
    ("📘", ("فيسبوك", "Facebook"), ("صفحتي على فيسبوك", "My Facebook page"), "https://www.facebook.com/share/1HsZnfQwpn/?mibextid=wwXIfr"),
]


def build(lang):
    t = lambda a, e: a if lang == "ar" else e
    L = lambda v: pick(lang, v)
    num = ar if lang == "ar" else str
    fwd = t("←", "→")
    q1, q2 = t("«", "“"), t("»", "”")
    me = t("شروق المحمادي", "Shoroog Almehmadi")

    ARTICLES = articles_for(lang)
    SLUGS = [a["slug"] for a in ARTICLES]

    def article_card(a, p=""):
        """p is the path prefix from the current page to the blog folder."""
        return f"""          <article class="post-card" data-tag="{'|'.join(a["tag"])}">
{tags_html(a["tag"], "            ")}
            <h3><a class="stretched" href="{p}articles/{a["slug"]}.html">{a["title"]}</a></h3>
            <p>{a["excerpt"]}</p>
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

    def latest(prefix, more):
        return f"""    <section class="section alt">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("أحدث الرحلات الطويلة", "Latest Long Journeys")}</h2>
          <a class="more" href="{more}">{t("كل الرحلات", "All journeys")} {fwd}</a>
        </div>
        <div class="posts">
{chr(10).join(article_card(a, prefix) for a in ARTICLES[:3])}
        </div>
      </div>
    </section>
"""

    # ---------- Home ----------
    z0 = ZAWIYA[0]
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
          <a href="sira.html" class="btn btn-ghost">{t("جواز السفر", "Passport")}</a>
        </div>
        <ul class="site-stats" aria-label="{t("إحصاءات الموقع", "Site stats")}">
          <li>🧳 {t("زوار الموقع", "Site visitors")}: <b data-stat="visitors">…</b></li>
          <li>🔁 {t("قرّاء دائمون", "Regular readers")}: <b data-stat="returning">…</b></li>
        </ul>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2 class="section-title">{t("تصفّح الموقع", "Explore the Site")}</h2>
        <div class="tiles">
          <a class="tile" href="sira.html"><span class="tile-icon">🛂</span><h3>{t("جواز السفر", "Passport")}</h3><p>{t("من أنا، وما الذي أعمل عليه، ومحطات رحلتي.", "Who I am, what I'm working on, and the stops along my journey.")}</p></a>
          <a class="tile" href="blog/articles.html"><span class="tile-icon">✍️</span><h3>{t("رحلات طويلة", "Long Journeys")}</h3><p>{t("نصوص أطول في التأمل والقراءة والكتابة.", "Longer pieces on reflection, reading and writing.")}</p></a>
          <a class="tile" href="blog/zawiya-36.html"><span class="tile-icon">🌙</span><h3>{t("الزاوية ٣٦", "Corner 36")}</h3><p>{t("خواطر قصيرة وملاحظات سريعة من يومي.", "Short reflections and quick notes from my day.")}</p></a>
          <a class="tile" href="books.html"><span class="tile-icon">📚</span><h3>{t("أمتعة السفر", "Luggage")}</h3><p>{t("كتبي.", "My books.")}</p></a>
        </div>
      </div>
    </section>

{latest("blog/", "blog/articles.html") if ARTICLES else ""}
    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("من الزاوية ٣٦", "From Corner 36")}</h2>
          <a class="more" href="blog/zawiya-36.html">{t("كل الخواطر", "All notes")} {fwd}</a>
        </div>
        <blockquote class="quote">
          <p>{q1}{L(z0[2])}{q2}</p>
          <cite>{L(z0[0])} · {fmt_date(lang, z0[1])}</cite>
        </blockquote>
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
         t("الموقع الشخصي لشروق المحمادي: جواز السفر، سجل الرحلات، أمتعة السفر، وبرج المراقبة.",
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

    sira = page_head(t("جواز السفر", "Passport"), t("هبوط وصعود", "Landings and Takeoffs"),
                     t("مرتفعات شديدة، وهبوط قوي، تمالك قلبك حتى لا يسقط.",
                       "Steep climbs and hard drops: hold on to your heart so it doesn't fall.")) + f"""
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
    page(lang, "sira.html", "sira", f"{t('جواز السفر', 'Passport')} · {me}", sira,
         t("جواز سفر شروق المحمادي: خريطة رحلتها من ١٩٩٩.", "Shoroog Almehmadi's passport: the map of her journey since 1999."))

    # ---------- Blog hub ----------
    blog = page_head(t("سجل الرحلات", "Travel Log"), t("سجل الرحلات", "Travel Log"),
                     t("مساحتان للكتابة: رحلات طويلة، وزاوية للخواطر القصيرة.",
                       "Two spaces for writing: long journeys, and a corner for short reflections.")) + f"""
    <section class="section">
      <div class="container">
        <div class="blog-split">
          <a class="blog-door" href="articles.html">
            <span class="door-icon">✍️</span>
            <h2>{t("رحلات طويلة", "Long Journeys")}</h2>
            <p>{t("نصوص أطول أتعمّق فيها في فكرة أو تجربة أو كتاب.", "Longer pieces where I go deep into an idea, an experience or a book.")}</p>
            <span class="count">{num(len(ARTICLES))} {t("رحلات", "journeys")}</span>
          </a>
          <a class="blog-door night" href="zawiya-36.html">
            <span class="door-icon">🌙</span>
            <h2>{t("الزاوية ٣٦", "Corner 36")}</h2>
            <p>{t("خواطر قصيرة، أسئلة، وملاحظات عابرة من يومي.", "Short reflections, questions and passing notes from my day.")}</p>
            <span class="count">{num(len(ZAWIYA))} {t("خواطر", "notes")}</span>
          </a>
        </div>
      </div>
    </section>

{latest("", "articles.html") if ARTICLES else ""}
    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">{t("أحدث الخواطر", "Latest Notes")}</h2>
          <a class="more" href="zawiya-36.html">{t("الزاوية ٣٦", "Corner 36")} {fwd}</a>
        </div>
        <div class="notes">
{chr(10).join(zawiya_card(len(ZAWIYA) - i, z) for i, z in enumerate(ZAWIYA[:3]))}
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
    zawiya = page_head(t("سجل الرحلات", "Travel Log"), t("الزاوية ٣٦", "Corner 36"),
                       t("زاوية صغيرة للخواطر القصيرة والأسئلة والملاحظات العابرة.",
                         "A small corner for short reflections, questions and passing notes."),
                       crumbs_tpl.format(t("الزاوية ٣٦", "Corner 36"))) + f"""
    <section class="section">
      <div class="container">
        <div class="notes">
{chr(10).join(zawiya_card(len(ZAWIYA) - i, z) for i, z in enumerate(ZAWIYA))}
        </div>
      </div>
    </section>
"""
    page(lang, "blog/zawiya-36.html", "blog-zawiya", f"{t('الزاوية ٣٦', 'Corner 36')} · {me}", zawiya,
         t("الزاوية ٣٦: خواطر قصيرة من شروق المحمادي.", "Corner 36: short reflections by Shoroog Almehmadi."))

    # ---------- Books ----------
    a_root = "../" * out_path(lang, "books.html").count("/")

    def book_card(title, sub, pub, year, url, front, back, desc):
        title = L(title)
        link = (f'\n              <a class="btn btn-primary book-link" href="{url}" target="_blank" rel="noopener">🛒 {t("زيارة المتجر", "Visit the store")}</a>'
                if url else "")
        covers = "".join(
            f'\n              <a href="{a_root}assets/books/{img}" target="_blank" rel="noopener"><img src="{a_root}assets/books/{img}" alt="{alt} {title}" width="900" height="1253" loading="lazy"></a>'
            for img, alt in ((front, t("الغلاف الأمامي لكتاب", "Front cover of")), (back, t("الغلاف الخلفي لكتاب", "Back cover of"))))
        return f"""          <article class="book mine">
            <div class="covers">{covers}
            </div>
            <div class="book-info">
              <h3>{title}</h3>
              <p class="subtitle">{L(sub)}</p>
              <p class="author">{L(pub)} · {L(year)}</p>
              <div class="book-desc">
{chr(10).join(f"                <p>{L(d)}</p>" for d in desc)}
              </div>{link}
            </div>
          </article>"""

    books = page_head(t("أمتعة السفر", "Luggage"), t("كتبي", "My Books"), "") + f"""
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
        return f"""            <li><span class="ci" aria-hidden="true">{icon}</span><div><strong>{L(label)}</strong>{value}</div></li>"""

    topics = [("سؤال", "Question"), ("اقتراح", "Suggestion"), ("تعاون", "Collaboration"), ("تعليق على رحلة", "Comment on a journey")]
    contact = page_head(t("برج المراقبة", "Control Tower"), t("تعيسًا أو سعيدًا كلِّم برج المراقبة", "Unhappy or happy, call the Control Tower"),
                        t("أي سؤال، وأي اقتراح، وحتى تعاون؛ موجودة وبرد لك.",
                          "Any question, any suggestion, even a collaboration: I'm here and I'll get back to you.")) + f"""
    <section class="section">
      <div class="container contact">
        <form class="contact-form" data-email="{EMAIL}" novalidate>
          <label>{t("الاسم", "Name")}
            <input type="text" name="name" required autocomplete="name">
          </label>
          <label>{t("الموضوع", "Topic")}
            <select name="topic">
{chr(10).join(f"              <option>{L(o)}</option>" for o in topics)}
            </select>
          </label>
          <label>{t("رسالتك", "Your message")}
            <textarea name="message" rows="6" required></textarea>
          </label>
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
    def render_block(kind, text):
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

    for i, a in enumerate(ARTICLES):
        slug, tag, title, excerpt = a["slug"], a["tag"], a["title"], a["excerpt"]
        newer = ARTICLES[i - 1] if i > 0 else None
        older = ARTICLES[i + 1] if i + 1 < len(ARTICLES) else None
        nav = ""
        if older:
            nav += f'<a class="pn prev" href="{older["slug"]}.html"><span>{t("الرحلة السابقة", "Previous journey")}</span>{older["title"]}</a>'
        if newer:
            nav += f'<a class="pn next" href="{newer["slug"]}.html"><span>{t("الرحلة التالية", "Next journey")}</span>{newer["title"]}</a>'
        related = [r for r in ARTICLES if set(r["tag"]) & set(tag) and r is not a][:2]
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
        <div class="listen" hidden>
          <button class="listen-btn" type="button"><span class="listen-icon" aria-hidden="true">🎧</span> <span class="listen-label">{t("استمع للمقال", "Listen to the article")}</span></button>
          <button class="listen-stop" type="button" hidden>⏹ {t("إيقاف", "Stop")}</button>
          <button class="listen-rate" type="button" hidden>{t("السرعة ١×", "Speed 1×")}</button>
          <span class="listen-status" role="status"></span>
        </div>
{"" if a["poem"] or excerpt in lead_blocks else f'        <p class="excerpt">{excerpt}</p>{chr(10)}'}{render_body(a)}
        <p class="signature">— {me}</p>
        <div class="engage">
          <button class="like-btn" type="button" aria-pressed="false"><span class="heart" aria-hidden="true">🤍</span> {t("أعجبتني", "I liked it")} <b class="like-count">…</b></button>
          <p class="reads-note">📖 <b class="read-count">…</b> {t("قراءة مكتملة", "completed reads")} <small>{t("(تُحسب حين يصل القارئ إلى آخر المقال بعد وقت كافٍ للقراءة)", "(counted when a reader reaches the end of the article after enough time to read it)")}</small></p>
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
          <p class="no-comments" hidden>{t("لا تعليقات بعد… كن أول من يعلّق", "No comments yet… be the first to comment")} ✈️</p>
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
