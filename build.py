"""يولّد صفحات الموقع.

التشغيل:  python3 build.py

- المقالات: ملف لكل مقال في content/articles/ (انظري README.md).
- الزاوية ٣٦ والكتب والمحطات: قوائم داخل هذا الملف (ابحثي عن ZAWIYA و BOOKS و TIMELINE).
- بعد أي تعديل شغّلي الأمر أعلاه لتحديث ملفات HTML.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))


def page(path, key, title, body, desc):
    depth = path.count("/")
    p = "../" * depth

    def act(k):
        return ' class="active"' if k == key or (k == "blog" and key.startswith("blog")) else ""

    def sub(k):
        return ' class="active"' if k == key else ""

    html = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <script>try{{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Readex+Pro:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{p}assets/styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container nav">
      <a href="{p}index.html" class="logo"><span class="logo-sun" aria-hidden="true"></span>شروق المحمادي</a>
      <button class="menu-toggle" aria-label="فتح القائمة" aria-expanded="false">☰</button>
      <nav class="nav-links" aria-label="القائمة الرئيسية">
        <a href="{p}index.html"{act("home")}>صالة المغادرة</a>
        <a href="{p}sira.html"{act("sira")}>جواز السفر</a>
        <div class="has-sub">
          <a href="{p}blog/index.html"{act("blog")}>سجل الرحلات <span class="caret" aria-hidden="true">▾</span></a>
          <div class="sub">
            <a href="{p}blog/articles.html"{sub("blog-articles")}>رحلات طويلة</a>
            <a href="{p}blog/zawiya-36.html"{sub("blog-zawiya")}>الزاوية ٣٦</a>
          </div>
        </div>
        <a href="{p}books.html"{act("books")}>حقيبة السفر</a>
        <a href="{p}contact.html"{act("contact")}>برج المراقبة</a>
        <button class="theme-toggle" aria-label="تبديل الوضع الليلي">🌙</button>
      </nav>
    </div>
  </header>

  <main>
{body}
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p class="footer-name">شروق المحمادي</p>
      <nav class="footer-links" aria-label="روابط التذييل">
        <a href="{p}sira.html">جواز السفر</a>
        <a href="{p}blog/articles.html">رحلات طويلة</a>
        <a href="{p}blog/zawiya-36.html">الزاوية ٣٦</a>
        <a href="{p}books.html">حقيبة السفر</a>
        <a href="{p}contact.html">برج المراقبة</a>
      </nav>
      <p class="copy">© <span class="year"></span> جميع الحقوق محفوظة</p>
    </div>
  </footer>

  <script src="{p}assets/script.js"></script>
</body>
</html>
"""
    full = os.path.join(ROOT, path)
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
ZAWIYA = [
    ("الضوء لا يستأذن", "١ أكتوبر ٢٠٢٦",
     "يدخل الضوء من أصغر شقّ في النافذة. هكذا هي الأفكار الجيدة: لا تحتاج إلا إلى فرصة صغيرة."),
    ("قهوة الصباح", "٢٤ سبتمبر ٢٠٢٦",
     "ليست القهوة ما يوقظني، بل الدقائق الهادئة التي أمنحها لنفسي قبل أن يبدأ اليوم."),
    ("عن البدايات", "١٧ سبتمبر ٢٠٢٦",
     "كل بداية تبدو صغيرة من الداخل، وكبيرة جداً حين ننظر إليها بعد عام."),
    ("سؤال الأسبوع", "١٠ سبتمبر ٢٠٢٦",
     "ما الشيء الذي تؤجله لأنك تنتظر أن تصبح جاهزاً؟ ربما الجاهزية تأتي بعد الخطوة، لا قبلها."),
    ("غيمة عابرة", "٣ سبتمبر ٢٠٢٦",
     "الأيام الثقيلة مثل الغيوم: تحجب الشمس قليلاً، لكنها لا تطفئها."),
    ("رسالة إلى نفسي", "٢٧ أغسطس ٢٠٢٦",
     "تمهّلي. ليس كل ما هو مهم عاجلاً، وليس كل ما هو عاجل مهماً."),
]

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def ar(n):
    return str(n).translate(AR_DIGITS)


AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def ar_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{ar(d)} {AR_MONTHS[m - 1]} {ar(y)}"


def read_time(blocks):
    words = sum(len(t.split()) for _, t in blocks)
    n = max(1, round(words / 200))
    if n == 1:
        return "دقيقة"
    if n == 2:
        return "دقيقتان"
    return f"{ar(n)} {'دقائق' if n <= 10 else 'دقيقة'}"


# أسماء حقول الترويسة بالعربية (والإنجليزية مقبولة أيضاً)
FIELDS = {"العنوان": "title", "التاريخ": "date", "التصنيف": "tag", "الملخص": "excerpt"}


def load_article(path):
    """ترويسة (مفتاح: قيمة) ثم سطر فارغ ثم النص.
    في النص: سطر يبدأ بـ ## عنوان فرعي، وسطر يبدأ بـ > اقتباس، والباقي فقرات."""
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    head, _, body = text.strip().partition("\n\n")
    meta = {}
    for line in head.splitlines():
        key, _, value = line.partition(":")
        key = key.strip()
        meta[FIELDS.get(key, key)] = value.strip()
    for ar_key, key in FIELDS.items():
        if not meta.get(key):
            raise SystemExit(f"{path}: الحقل «{ar_key}» مفقود في الترويسة")
    blocks = []
    for para in re.split(r"\n\s*\n", body.strip()):
        para = " ".join(line.strip() for line in para.splitlines())
        if para.startswith("## "):
            blocks.append(("h2", para[3:]))
        elif para.startswith("> "):
            blocks.append(("quote", para[2:]))
        elif para:
            blocks.append(("p", para))
    slug = os.path.splitext(os.path.basename(path))[0]
    return meta, slug, blocks


# newest first
_loaded = sorted((load_article(f) for f in glob.glob(os.path.join(ROOT, "content", "articles", "*.md"))),
                 key=lambda x: x[0]["date"], reverse=True)
ARTICLES = [(m["tag"], m["title"], ar_date(m["date"]), read_time(b), m["excerpt"]) for m, _, b in _loaded]
SLUGS = [slug for _, slug, _ in _loaded]
BODIES = {slug: b for _, slug, b in _loaded}


def slug_of(a):
    return SLUGS[ARTICLES.index(a)]


def article_card(a, p=""):
    """p is the path prefix from the current page to the blog folder."""
    tag, title, date, read, excerpt = a
    return f"""          <article class="post-card" data-tag="{tag}">
            <span class="tag">{tag}</span>
            <h3><a class="stretched" href="{p}articles/{slug_of(a)}.html">{title}</a></h3>
            <p>{excerpt}</p>
            <p class="meta">{date} · {read} قراءة</p>
          </article>"""


def zawiya_card(i, z):
    title, date, text = z
    return f"""          <article class="note-card">
            <span class="note-num">#{ar(i)}</span>
            <h3>{title}</h3>
            <p>{text}</p>
            <p class="meta">{date}</p>
          </article>"""


# ---------- Home ----------
home = f"""    <section class="hero">
      <div class="sky" aria-hidden="true">
        <div class="sun"><span class="rays"></span></div>
        <span class="cloud c1"></span><span class="cloud c2"></span><span class="cloud c3"></span>
      </div>
      <div class="container hero-inner">
        <figure class="verse">
          <blockquote><span>كلُّ شمسٍ لم تكُنْها ظلامُ</span></blockquote>
        </figure>
        <h1>شروق المحمادي</h1>
        <p class="lead">أيها القارئ: لنتفق! المقعد الأيمن مرة لي ومرة لك، وذلك طوال رحلتنا في سياحة العقول والأفكار والتجارب. طيب كابتن؟</p>
        <div class="hero-actions">
          <a href="blog/index.html" class="btn btn-primary">سجل الرحلات</a>
          <a href="sira.html" class="btn btn-ghost">تعرّف عليّ</a>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <h2 class="section-title">تصفّح الموقع</h2>
        <div class="tiles">
          <a class="tile" href="sira.html"><span class="tile-icon">🛂</span><h3>جواز السفر</h3><p>من أنا، وما الذي أعمل عليه، ومحطات رحلتي.</p></a>
          <a class="tile" href="blog/articles.html"><span class="tile-icon">✍️</span><h3>رحلات طويلة</h3><p>نصوص أطول في التأمل والقراءة والكتابة.</p></a>
          <a class="tile" href="blog/zawiya-36.html"><span class="tile-icon">🌙</span><h3>الزاوية ٣٦</h3><p>خواطر قصيرة وملاحظات سريعة من يومي.</p></a>
          <a class="tile" href="books.html"><span class="tile-icon">📚</span><h3>حقيبة السفر</h3><p>ما قرأت وما أقرأ الآن وما ينتظر على الرف.</p></a>
        </div>
      </div>
    </section>

    <section class="section alt">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">أحدث الرحلات الطويلة</h2>
          <a class="more" href="blog/articles.html">كل الرحلات ←</a>
        </div>
        <div class="posts">
{chr(10).join(article_card(a, "blog/") for a in ARTICLES[:3])}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">من الزاوية ٣٦</h2>
          <a class="more" href="blog/zawiya-36.html">كل الخواطر ←</a>
        </div>
        <blockquote class="quote">
          <p>«{ZAWIYA[0][2]}»</p>
          <cite>{ZAWIYA[0][0]} · {ZAWIYA[0][1]}</cite>
        </blockquote>
      </div>
    </section>

    <section class="section cta">
      <div class="container cta-inner">
        <h2>لديك فكرة أو سؤال؟</h2>
        <p>يسعدني أن أسمع منك دائماً.</p>
        <a href="contact.html" class="btn btn-primary">تواصل معنا</a>
      </div>
    </section>
"""
page("index.html", "home", "شروق المحمادي", home,
     "الموقع الشخصي لشروق المحمادي: جواز السفر، سجل الرحلات، حقيبة السفر، وبرج المراقبة.")

# ---------- Sira ----------
TIMELINE = [
    ("٢٠٢٦", "إطلاق هذا الموقع", "مساحة شخصية تجمع الكتابة والقراءة في مكان واحد."),
    ("٢٠٢٤", "بداية الكتابة بانتظام", "تحدّي الكتابة الأسبوعية الذي تحوّل لاحقاً إلى المدونة."),
    ("٢٠٢٢", "التخرج من الجامعة", "اكتب هنا تخصصك والجامعة التي تخرجت منها."),
    ("٢٠١٨", "أول كتاب أحببته حقاً", "اللحظة التي تحولت فيها القراءة من واجب إلى شغف."),
]
sira = page_head("جواز السفر", "مرحباً، أنا شروق",
                 "أحب الضوء والكلمات والبدايات الجديدة. هنا شيء من قصتي.") + f"""
    <section class="section">
      <div class="container bio">
        <div class="bio-photo" aria-hidden="true"><span>ش</span></div>
        <div class="bio-text">
          <h2>نبذة</h2>
          <p>أنا شروق المحمادي، أؤمن بأن لكل يوم شروقه الخاص. أكتب لأفهم العالم من حولي، وأقرأ لأرى بعيون الآخرين. أهتم بالتأمل والكتابة والقراءة، وأحاول أن أحوّل ما أتعلمه إلى كلمات قد تفيد غيري.</p>
          <p>هذه النبذة مثال مؤقت؛ استبدليها بقصتك الحقيقية: عملك، اهتماماتك، وما الذي يحركك.</p>
          <ul class="chips">
            <li>الكتابة</li><li>القراءة</li><li>التأمل</li><li>التعلّم المستمر</li><li>السماء 🌤️</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="section alt">
      <div class="container">
        <h2 class="section-title">محطات</h2>
        <ol class="timeline">
{chr(10).join(f'''          <li><span class="year-badge">{y}</span><div><h3>{t}</h3><p>{d}</p></div></li>''' for y, t, d in TIMELINE)}
        </ol>
      </div>
    </section>
"""
page("sira.html", "sira", "جواز السفر · شروق المحمادي", sira, "سيرة شروق المحمادي ومحطات رحلتها.")

# ---------- Blog hub ----------
blog = page_head("سجل الرحلات", "سجل الرحلات", "مساحتان للكتابة: مقالات مطوّلة، وزاوية للخواطر القصيرة.") + f"""
    <section class="section">
      <div class="container">
        <div class="blog-split">
          <a class="blog-door" href="articles.html">
            <span class="door-icon">✍️</span>
            <h2>رحلات طويلة</h2>
            <p>نصوص أطول أتعمّق فيها في فكرة أو تجربة أو كتاب.</p>
            <span class="count">{ar(len(ARTICLES))} مقالات</span>
          </a>
          <a class="blog-door night" href="zawiya-36.html">
            <span class="door-icon">🌙</span>
            <h2>الزاوية ٣٦</h2>
            <p>خواطر قصيرة، أسئلة، وملاحظات عابرة من يومي.</p>
            <span class="count">{ar(len(ZAWIYA))} خواطر</span>
          </a>
        </div>
      </div>
    </section>

    <section class="section alt">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">أحدث الرحلات الطويلة</h2>
          <a class="more" href="articles.html">كل الرحلات ←</a>
        </div>
        <div class="posts">
{chr(10).join(article_card(a) for a in ARTICLES[:3])}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2 class="section-title">أحدث الخواطر</h2>
          <a class="more" href="zawiya-36.html">الزاوية ٣٦ ←</a>
        </div>
        <div class="notes">
{chr(10).join(zawiya_card(len(ZAWIYA) - i, z) for i, z in enumerate(ZAWIYA[:3]))}
        </div>
      </div>
    </section>
"""
page("blog/index.html", "blog", "سجل الرحلات · شروق المحمادي", blog, "مدونة شروق المحمادي: المقالات والزاوية ٣٦.")

crumbs_tpl = '        <nav class="crumbs" aria-label="مسار التنقل"><a href="index.html">سجل الرحلات</a> / <span>{}</span></nav>\n'

# ---------- Articles ----------
tags = sorted({a[0] for a in ARTICLES})
articles = page_head("سجل الرحلات", "رحلات طويلة", "نصوص في التأمل والقراءة والكتابة.",
                     crumbs_tpl.format("رحلات طويلة")) + f"""
    <section class="section">
      <div class="container">
        <div class="toolbar">
          <div class="filters">
            <button class="filter active" data-filter="all">الكل</button>
{chr(10).join(f'            <button class="filter" data-filter="{t}">{t}</button>' for t in tags)}
          </div>
          <input class="search" type="search" placeholder="ابحث في الرحلات…" aria-label="ابحث في الرحلات الطويلة">
        </div>
        <div class="posts" data-filterable>
{chr(10).join(article_card(a) for a in ARTICLES)}
        </div>
        <p class="empty" hidden>لا توجد مقالات مطابقة.</p>
      </div>
    </section>
"""
page("blog/articles.html", "blog-articles", "رحلات طويلة · شروق المحمادي", articles, "مقالات شروق المحمادي.")

# ---------- Zawiya 36 ----------
zawiya = page_head("سجل الرحلات", "الزاوية ٣٦", "زاوية صغيرة للخواطر القصيرة والأسئلة والملاحظات العابرة.",
                   crumbs_tpl.format("الزاوية ٣٦")) + f"""
    <section class="section">
      <div class="container">
        <div class="notes">
{chr(10).join(zawiya_card(len(ZAWIYA) - i, z) for i, z in enumerate(ZAWIYA))}
        </div>
      </div>
    </section>
"""
page("blog/zawiya-36.html", "blog-zawiya", "الزاوية ٣٦ · شروق المحمادي", zawiya, "الزاوية ٣٦: خواطر قصيرة من شروق المحمادي.")

# ---------- Books ----------
BOOKS = [
    ("الأيام", "طه حسين", "قرأته", "سيرة تُقرأ كأنها رواية، وتعلّم معنى الإصرار.", "b1"),
    ("ثلاثية غرناطة", "رضوى عاشور", "قرأته", "حكاية مدينة وذاكرة، بلغة دافئة لا تُنسى.", "b2"),
    ("موسم الهجرة إلى الشمال", "الطيب صالح", "أقرأه الآن", "رحلة بين عالمين، وأسئلة عن الهوية.", "b3"),
    ("رجال في الشمس", "غسان كنفاني", "قرأته", "قصيرة ومؤلمة، وتبقى معك طويلاً.", "b4"),
    ("مئة عام من العزلة", "غابرييل غارسيا ماركيز", "في القائمة", "ملحمة عائلة وقرية بين الواقع والسحر.", "b5"),
    ("الخيميائي", "باولو كويلو", "في القائمة", "عن الأحلام والطريق إليها.", "b6"),
]
statuses = ["قرأته", "أقرأه الآن", "في القائمة"]
books = page_head("حقيبة السفر", "الكتب التي ترافقني", "ما قرأت، وما أقرأ الآن، وما ينتظر دوره على الرف.") + f"""
    <section class="section">
      <div class="container">
        <div class="filters">
          <button class="filter active" data-filter="all">الكل</button>
{chr(10).join(f'          <button class="filter" data-filter="{s}">{s}</button>' for s in statuses)}
        </div>
        <div class="books" data-filterable>
{chr(10).join(f'''          <article class="book" data-tag="{s}">
            <div class="cover {c}"><span>{t}</span></div>
            <div class="book-info">
              <span class="status">{s}</span>
              <h3>{t}</h3>
              <p class="author">{a}</p>
              <p>{n}</p>
            </div>
          </article>''' for t, a, s, n, c in BOOKS)}
        </div>
      </div>
    </section>
"""
page("books.html", "books", "حقيبة السفر · شروق المحمادي", books, "رفوف كتب شروق المحمادي.")

# ---------- Contact ----------
contact = page_head("برج المراقبة", "يسعدني سماعك", "لأي سؤال أو اقتراح أو تعاون، اكتب لي وسأرد عليك قريباً.") + """
    <section class="section">
      <div class="container contact">
        <form class="contact-form" novalidate>
          <label>الاسم
            <input type="text" name="name" required autocomplete="name">
          </label>
          <label>البريد الإلكتروني
            <input type="email" name="email" required autocomplete="email">
          </label>
          <label>الموضوع
            <select name="topic">
              <option>سؤال عام</option>
              <option>تعليق على مقال</option>
              <option>اقتراح كتاب</option>
              <option>تعاون</option>
            </select>
          </label>
          <label>رسالتك
            <textarea name="message" rows="6" required></textarea>
          </label>
          <button type="submit" class="btn btn-primary">إرسال</button>
          <p class="form-status" role="status"></p>
        </form>
        <aside class="contact-side">
          <h2>طرق أخرى</h2>
          <ul>
            <li><span>✉️</span><a href="mailto:hello@example.com">hello@example.com</a></li>
            <li><span>𝕏</span><a href="#">@username</a></li>
            <li><span>📷</span><a href="#">انستقرام</a></li>
          </ul>
          <p class="hint">استبدلي هذه الروابط بحساباتك الحقيقية.</p>
        </aside>
      </div>
    </section>
"""
page("contact.html", "contact", "برج المراقبة · شروق المحمادي", contact, "تواصل مع شروق المحمادي.")

# ---------- Article pages ----------
def render_block(kind, text):
    if kind == "h2":
        return f"        <h2>{text}</h2>"
    if kind == "quote":
        return f"        <blockquote><p>{text}</p></blockquote>"
    return f"        <p>{text}</p>"


for old in glob.glob(os.path.join(ROOT, "blog", "articles", "*.html")):
    if os.path.splitext(os.path.basename(old))[0] not in SLUGS:
        os.remove(old)

for i, a in enumerate(ARTICLES):
    tag, title, date, read, excerpt = a
    slug = SLUGS[i]
    newer = ARTICLES[i - 1] if i > 0 else None
    older = ARTICLES[i + 1] if i + 1 < len(ARTICLES) else None
    nav = ""
    if older:
        nav += f'<a class="pn prev" href="{SLUGS[i + 1]}.html"><span>المقال السابق</span>{older[1]}</a>'
    if newer:
        nav += f'<a class="pn next" href="{SLUGS[i - 1]}.html"><span>المقال التالي</span>{newer[1]}</a>'
    related = [r for r in ARTICLES if r[0] == tag and r is not a][:2]
    body = f"""    <section class="page-hero article-hero">
      <div class="clouds" aria-hidden="true"><span class="cloud c1"></span><span class="cloud c2"></span></div>
      <div class="container narrow">
        <nav class="crumbs" aria-label="مسار التنقل"><a href="../index.html">سجل الرحلات</a> / <a href="../articles.html">رحلات طويلة</a></nav>
        <span class="tag">{tag}</span>
        <h1>{title}</h1>
        <p class="meta">{date} · {read} قراءة</p>
      </div>
    </section>

    <article class="section">
      <div class="container narrow prose">
        <p class="excerpt">{excerpt}</p>
{chr(10).join(render_block(k, t) for k, t in BODIES[slug])}
        <p class="signature">— شروق المحمادي</p>
        <nav class="post-nav" aria-label="تنقل بين المقالات">{nav}</nav>
      </div>
    </article>
"""
    if related:
        body += f"""
    <section class="section alt">
      <div class="container">
        <h2 class="section-title">مقالات أخرى في «{tag}»</h2>
        <div class="posts">
{chr(10).join(article_card(r, "../") for r in related)}
        </div>
      </div>
    </section>
"""
    page(f"blog/articles/{slug}.html", "blog-articles", f"{title} · شروق المحمادي", body, excerpt)
print(f"تم: {len(ARTICLES)} مقالات")
