"""فاحص خطة الفيلم (story.yaml): يحوّل ما تعلّمناه إلى قواعد برمجية تُطبَّق على أي فيلم.

المراجع:
  - Writing for Animation (Beaumont & Larson) — docs/writing-for-animation.md
  - Story (Robert McKee)                      — docs/story-mckee.md
  - مبادئ التحريك وقاعدة محاكاة الواقع        — docs/animation-principles.md و CLAUDE.md
  - مستوى فيلم سليماني (الحد الأدنى للجودة)    — films/soleimani_mckee/

  python3 studio.py plan films/<slug>/story.yaml     # يطبع تقريرًا ويخرج برمز 1 إن وُجد خطأ
  python3 studio.py qa   films/<slug>/out.mp4 [films/<slug>/story.yaml]
"""
import json
import subprocess
import yaml

EMPATHY_TOOLS = {"skill", "funny", "early", "resolve", "nice", "adversity"}   # أدوات الارتباط العاطفي الست
SIGN = {"+": 1, "-": -1, "+-": 0, "-+": 0, "0": 0}
ANCHOR_WPS = 2.4          # سرعة نطق المذيع (كلمة/ثانية) — كريم بملف anchor
LEVEL = {"soleimani": dict(fps=60, min_short_side=1080, voice="anchor", loudness=-14.0)}


class Report:
    def __init__(self):
        self.err, self.warn, self.ok = [], [], []

    def check(self, cond, ok_msg, fail_msg, severe=True):
        if cond:
            self.ok.append(ok_msg)
        else:
            (self.err if severe else self.warn).append(fail_msg)
        return cond

    def print(self):
        for m in self.ok:
            print("  ✓", m)
        for m in self.warn:
            print("  ⚠", m)
        for m in self.err:
            print("  ✗", m)
        print(f"\nالنتيجة: {len(self.ok)} سليم، {len(self.warn)} تنبيه، {len(self.err)} خطأ")
        return 1 if self.err else 0


def _words(s):
    return len([w for w in (s or "").replace("…", " ").split() if w.strip()])


def check_plan(path):
    P = yaml.safe_load(open(path, encoding="utf-8"))
    R = Report()
    shots = P.get("shots", [])
    ids = [s["id"] for s in shots]
    dur = max((s["t1"] for s in shots), default=0)
    print(f"خطة: {P.get('title', '?')} — {len(shots)} لقطة، {dur:.1f} ث\n")

    # ---- 1) الفكرة الحاكمة (مكّي): قيمة + سبب في جملة واحدة
    ci = P.get("controlling_idea", {}) or {}
    R.check(ci.get("value") and ci.get("cause") and ci.get("sentence"),
            "الفكرة الحاكمة: قيمة + سبب في جملة واحدة", "الفكرة الحاكمة ناقصة (value + cause + sentence)")

    # ---- 2) القيمة المركزية تنقلب انقلابًا لا رجعة فيه
    cv = P.get("central_value", {}) or {}
    R.check(cv.get("start") and cv.get("end") and cv.get("start") != cv.get("end"),
            f"القيمة المركزية «{cv.get('name')}» تنقلب {cv.get('start')} ← {cv.get('end')}",
            "القيمة المركزية لا تنقلب بين البداية والنهاية — ليست قصة")

    # ---- 3) شخصية محورية واحدة تظهر مبكرًا مع أداة ارتباط
    cc = P.get("central_character", {}) or {}
    first = cc.get("first_on_screen_s", 99)
    R.check(first <= 0.25 * dur, f"الشخصية المحورية تظهر عند {first} ث", "الشخصية المحورية تتأخر عن الربع الأول")
    R.check(first <= 2.5, "ظهور الشخصية (أو أثرها) في أول ثانيتين", "الأفضل أن تظهر الشخصية أو أثرها في أول ثانيتين", severe=False)
    tools = set(cc.get("empathy", []))
    R.check(tools and tools <= EMPATHY_TOOLS, f"أداة ارتباط عاطفي: {', '.join(sorted(tools))}",
            f"حدّد أداة ارتباط واحدة على الأقل من {sorted(EMPATHY_TOOLS)}")

    # ---- 4) الهدف: مادي محدد قابل للشطب وله مهلة
    g = P.get("goal", {}) or {}
    R.check(g.get("object") and g.get("tickable"), "هدف مادي محدد قابل للشطب", "الهدف غير محدد أو غير قابل للشطب")
    R.check(bool(g.get("deadline")), "للهدف مهلة / ساعة تدق", "لا مهلة للهدف (ticking clock)", severe=False)

    # ---- 5) الحادثة المحرّضة على الشاشة وفي الربع الأول، والمشهد الملزم يتحقق
    ii = P.get("inciting_incident", {}) or {}
    R.check(ii.get("on_screen") and ii.get("t", 99) <= 0.25 * dur,
            f"الحادثة المحرّضة على الشاشة عند {ii.get('t')} ث", "الحادثة المحرّضة غائبة أو خارج الشاشة أو متأخرة عن الربع الأول")
    ob = P.get("obligatory_scene", {}) or {}
    R.check(ob.get("shot") in ids and ids.index(ob["shot"]) > ids.index(ii.get("shot", ids[0])) if ob.get("shot") in ids else False,
            f"المشهد الملزم ({ob.get('shot')}) يأتي بعد الحادثة المحرّضة", "المشهد الملزم مفقود — الجمهور ينتظره")

    # ---- 6) كل لقطة حدث: تقلب قيمة وفيها فجوة بين المتوقع والواقع
    signs = []
    for s in shots:
        v = s.get("value", {}) or {}
        turned = v.get("start") != v.get("end")
        R.check(turned, f"[{s['id']}] تقلب «{v.get('name')}» {v.get('start')}←{v.get('end')}",
                f"[{s['id']}] لا تقلب قيمة — «نشاط» لا «حدث»: احذفها أو أعد بناءها", severe=False)
        gap = s.get("gap", {}) or {}
        R.check(gap.get("expected") and gap.get("got"), f"[{s['id']}] فجوة: توقّع «{gap.get('expected')}» فحدث «{gap.get('got')}»",
                f"[{s['id']}] بلا فجوة بين المتوقع والواقع", severe=False)
        R.check(s.get("action", False), f"[{s['id']}] فيها فعل مرئي", f"[{s['id']}] رؤوس متكلمة بلا فعل مرئي", severe=False)
        signs.append(SIGN.get(str(v.get("end")), 0))
        # الإيجاز: سرعة التعليق ضمن قدرة المذيع
        n = s.get("narration")
        if n:
            wps = _words(n) / max(0.1, s["t1"] - s["t0"] + s.get("narration_overflow", 0))
            R.check(wps <= ANCHOR_WPS * 1.05, f"[{s['id']}] التعليق {wps:.1f} كلمة/ث", f"[{s['id']}] التعليق مزدحم ({wps:.1f} كلمة/ث > {ANCHOR_WPS}) — اختصر")

    # ---- 7) الفكرة ونقيضها: تأرجح الشحنة (+/−) مرتين على الأقل
    changes = sum(1 for a, b in zip(signs, signs[1:]) if a and b and a != b)
    R.check(changes >= 2, f"تأرجح الفكرة ونقيضها: {changes} انقلابات", "لا تأرجح بين + و − — النقيض ضعيف والقصة خطية", severe=False)

    # ---- 8) التصاعد: الشدة لا تهبط قبل الذروة، والذروة أقوى لحظة ولا رجعة فيها
    inten = [s.get("intensity", 0) for s in shots]
    cl = P.get("climax", {}) or {}
    if cl.get("shot") in ids:
        k = ids.index(cl["shot"])
        R.check(inten[k] == max(inten), "الذروة أقوى لحظة في الفيلم", "توجد لقطة أشد من الذروة — احفظ الأفضل للنهاية")
        drops = [ids[i + 1] for i in range(k) if inten[i + 1] < inten[i] - 1]
        R.check(not drops, "العقبات تتصاعد حتى الذروة", f"هبوط في التصاعد عند {drops}", severe=False)
        R.check(cl.get("irreversible"), "الذروة تغيير لا رجعة فيه", "الذروة قابلة للتراجع")
    else:
        R.err.append("لم تُحدَّد لقطة الذروة")

    # ---- 9) الزرع والحصاد: كل حلّ في النهاية مزروع مسبقًا
    for pp in P.get("plants", []):
        a, b = pp.get("plant"), pp.get("payoff")
        R.check(a in ids and b in ids and ids.index(a) < ids.index(b), f"زرع «{pp.get('what')}» في {a} ← حصاد في {b}",
                f"زرع/حصاد غير صحيح: {pp}")
    R.check(bool(P.get("plants")), "يوجد زرع وحصاد", "لا زرع ولا حصاد — النهاية قد تبدو مصادفة", severe=False)

    # ---- 10) محاكاة الواقع: المصادر والمراجع المرئية والمقاييس
    if P.get("real_events", True):
        R.check(bool(P.get("sources")), f"{len(P.get('sources', []))} مصادر للوقائع", "فيلم وقائع بلا مصادر")
    R.check(bool(P.get("visual_refs")), "مراجع بصرية حقيقية بُحث عنها قبل الرسم", "ابحث عن صور/مواصفات حقيقية قبل الرسم", severe=False)

    # ---- 11) مستوى الإخراج
    rd = P.get("render", {}) or {}
    lv = LEVEL.get(P.get("level", "soleimani"), LEVEL["soleimani"])
    R.check(rd.get("fps", 0) >= lv["fps"], f"{rd.get('fps')} إطارًا/ث", f"أقل من {lv['fps']} إطارًا/ث")
    R.check(rd.get("voice") == lv["voice"], "صوت المذيع (anchor)", "استعمل صوت anchor بأسلوب العربية/الجزيرة", severe=False)
    return R.print()


def _probe(mp4):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", mp4],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def _loudness(mp4):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    for line in reversed(r.stderr.splitlines()):
        if line.strip().startswith("I:"):
            return float(line.split()[1])
    return None


def check_video(mp4, plan=None, level="soleimani"):
    R = Report()
    lv = LEVEL[level]
    J = _probe(mp4)
    v = next((s for s in J["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in J["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    fps = num / den
    dur = float(J["format"]["duration"])
    print(f"فحص: {mp4}\n")
    R.check(min(v["width"], v["height"]) >= lv["min_short_side"], f"الدقة {v['width']}×{v['height']}", "الدقة أقل من 1080")
    R.check(fps >= lv["fps"] - 0.5, f"{fps:.0f} إطارًا/ث", f"{fps:.0f} إطارًا/ث أقل من {lv['fps']}")
    R.check(v.get("pix_fmt") == "yuv420p", "yuv420p (يعمل على الجوال)", "صيغة البكسل ليست yuv420p")
    R.check(a is not None, "يوجد صوت", "لا يوجد صوت")
    if a is not None:
        L = _loudness(mp4)
        R.check(L is not None and abs(L - lv["loudness"]) <= 2.0, f"علوّ الصوت {L} LUFS", f"علوّ الصوت {L} بعيد عن {lv['loudness']}")
    if plan:
        P = yaml.safe_load(open(plan, encoding="utf-8"))
        pd = max(s["t1"] for s in P["shots"])
        R.check(abs(pd - dur) <= 0.5, f"المدة {dur:.1f} ث تطابق الخطة", f"المدة {dur:.1f} ث لا تطابق الخطة ({pd:.1f})")
    return R.print()
