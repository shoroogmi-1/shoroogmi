"""أدوات الحركة الفيزيائية والتمثيلية — من كتاب «Animation: The Mechanics of Motion» (Chris Webster) كاملًا.

كل دالة تطبّق مبدأً من الكتاب:
  bounce()        قوانين نيوتن + الجاذبية: الكرة/القذيفة/البالون — الكتلة تحدد الارتداد والزخم ومقاومة الهواء
  squash_stretch() ضغط عند الاصطدام ومط مع السرعة، مع حفظ الحجم دائمًا (والأجسام الصلبة لا تنضغط)
  take()          ردّة الفعل المفاجئة: انضغاط (تمهيد) ← تمدد أقصى ← استقرار، و double_take بتمهيد ثانٍ
  moving_hold()   «الوقفة المتحركة»: لا ثبات تام أبدًا؛ انجراف صغير متباطئ يُبقي الشخصية حيّة (بلا «زيتية» الحاسوب)
  boil()          «الغليان»: اهتزاز خفيف عشوائي للخطوط في اللقطات الثابتة (رسم يدوي حي) — بترتيب عشوائي لا دوري
  on_twos()       التصوير «على اثنين» (12 رسمة/ث) لإحساس الرسم اليدوي/الأنمي، أو «على واحد» للنعومة
  quad_gait()     مشية ذوات الأربع: مشي بأربع ضربات (خلفي ثم أمامي نفس الجهة)، هرولة قطرية بضربتين + تعليق، وجري/عدو
  wing_cycle()    دورة الجناح: ضربة سفلية ممدودة للأمام، صعود مطوي للخلف، تأخر أطراف الريش (سحب)، والجسم عكس الدفع
  whip()          الحركة السوطية: الكاحل ← الركبة ← الورك ← الكتف ← الذراع ← اليد، كل مفصل يتأخر عن سابقه
  phrasing()      الإيقاع/الصياغة: تغيير سرعة الأداء داخل المشهد (بطيء/سريع/توقف) بدل سرعة واحدة مملة
"""
import math
import random


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- الجاذبية والارتداد
MATERIALS = {
    #            معامل الارتداد  مقاومة الهواء  قابلية الضغط   الاحتكاك على الأرض
    "tennis": dict(rest=0.72, drag=0.02, squash=0.35, roll=0.6),
    "cannon": dict(rest=0.18, drag=0.0, squash=0.04, roll=0.97),   # ثقيل: ارتداد قليل لكن يتدحرج بعيدًا (زخم)
    "balloon": dict(rest=0.55, drag=1.6, squash=0.45, roll=0.3),   # خفيف: يسقط ببطء ويفقد زخمه سريعًا
    "rubber": dict(rest=0.85, drag=0.01, squash=0.6, roll=0.7),
    "metal": dict(rest=0.3, drag=0.0, squash=0.0, roll=0.9),       # صلب: لا ضغط ولا مط
}


def bounce(t, x0, y0, vx, ground, material="tennis", g=2400.0, dt=1 / 240):
    """يحاكي جسمًا مقذوفًا حتى الزمن t. يرجع (x, y, vx, vy, منذ_آخر_اصطدام, سرعة_الاصطدام)."""
    m = MATERIALS[material]
    x, y, vy = x0, y0, 0.0
    since, impact_v = 9.0, 0.0
    n = int(t / dt)
    for _ in range(n):
        vy += g * dt
        vx *= (1 - m["drag"] * dt)
        vy *= (1 - m["drag"] * dt)
        x += vx * dt
        y += vy * dt
        since += dt
        if y >= ground:
            y = ground
            if vy > 60:
                impact_v = vy
                vy = -vy * m["rest"]
                vx *= m["roll"] ** 0.5
                since = 0.0
            else:
                vy = 0.0
                vx *= (1 - (1 - m["roll"]) * dt * 6)
    return x, y, vx, vy, since, impact_v


def squash_stretch(vx, vy, since_impact, impact_v, material="tennis"):
    """يرجع (sx, sy, زاوية) للحجم المرئي — الحجم محفوظ: sx*sy = 1."""
    m = MATERIALS[material]
    k = m["squash"]
    if k == 0:
        return 1.0, 1.0, 0.0
    if since_impact < 0.06:                                   # ضغط عند الاصطدام فقط، يُستبدل سريعًا بالمط
        s = 1 + k * min(1.0, impact_v / 1500) * (1 - since_impact / 0.06)
        return s, 1 / s, 0.0
    speed = math.hypot(vx, vy)
    st = 1 + k * 0.5 * min(1.0, speed / 1800)                 # مط مع السرعة، ويختفي عند قمة القوس
    ang = math.degrees(math.atan2(vy, vx)) if speed > 1 else 0.0
    return st, 1 / st, ang


# ---------------------------------------------------------------- التمثيل
def take(t, t0, dur=0.9, double=False):
    """ردّة الفعل (take): يرجع (squash, stretch_scale, settle). squash<1 انضغاط، >1 تمدد."""
    u = t - t0
    if u < 0:
        return 1.0
    if double:                                                # تمهيد ثانٍ قبل ردة الفعل (للكوميديا)
        if u < 0.25:
            return 1 - 0.06 * math.sin(math.pi * u / 0.25)
        u -= 0.25
    if u < 0.18:                                              # انضغاط (تمهيد)
        return 1 - 0.12 * ease(u / 0.18)
    if u < 0.3:                                               # تمدد أقصى سريع
        return 0.88 + 0.32 * ease((u - 0.18) / 0.12)
    v = (u - 0.3) / max(dur - 0.3, 1e-3)                      # استقرار بتذبذب متخامد (متابعة)
    return 1 + 0.2 * math.exp(-v * 5) * math.cos(v * 14)


def moving_hold(t, t0, amount=1.0, dur=1.5):
    """بعد الوصول للوضعية المفتاحية: استمرار صغير متباطئ في نفس الاتجاه (لا ثبات ميت ولا تساوٍ في التباعد)."""
    u = clamp((t - t0) / dur)
    return amount * (1 - (1 - u) ** 3)


def boil(seed_t, fps=12, amp=1.2, n_variants=3):
    """إزاحة (dx, dy) صغيرة تتغير «على اثنين» بترتيب عشوائي بين 3 نسخ — تبقي الخط حيًا في اللقطة الثابتة."""
    frame = int(seed_t * fps)
    r = random.Random(frame * 7919)
    v = r.randrange(n_variants)
    r2 = random.Random(v * 104729)
    return r2.uniform(-amp, amp), r2.uniform(-amp, amp)


def on_twos(t, fps=24, step=2):
    """يقرّب الزمن لخطوات (رسمة كل إطارين) — إحساس الرسوم اليدوية والأنمي."""
    f = int(t * fps)
    return (f - f % step) / fps


def phrasing(t, beats):
    """beats: [(زمن_البداية, السرعة)...] — يحوّل الزمن الحقيقي إلى «زمن الأداء» بسرعات متغيرة وانتقالات ناعمة."""
    acc, last_t, last_s = 0.0, 0.0, beats[0][1] if beats else 1.0
    for (bt, sp) in beats:
        if t < bt:
            break
        acc += (bt - last_t) * last_s
        last_t, last_s = bt, sp
    return acc + (t - last_t) * last_s


def whip(t, t0, joints=6, lag=0.05, dur=0.5):
    """الحركة السوطية: يرجع قائمة تقدّم (0..1) لكل مفصل بدءًا من الكاحل حتى اليد، كل واحد متأخر عن سابقه."""
    return [ease((t - t0 - i * lag) / dur) for i in range(joints)]


# ---------------------------------------------------------------- ذوات الأربع
QUAD = {
    # إزاحات الطور لكل رجل: [أمامي أيسر، أمامي أيمن، خلفي أيسر، خلفي أيمن]
    "walk": dict(T=1.1, stance=0.65, offsets=[0.0, 0.5, 0.75, 0.25], lift=0.18, bob=0.02, susp=False),   # أربع ضربات منفصلة
    "trot": dict(T=0.62, stance=0.42, offsets=[0.0, 0.5, 0.5, 0.0], lift=0.3, bob=0.05, susp=True),     # قطري بضربتين + تعليق
    "gallop": dict(T=0.45, stance=0.3, offsets=[0.0, 0.1, 0.55, 0.65], lift=0.35, bob=0.07, susp=True),  # أربع ضربات غير متساوية
    "pace": dict(T=0.6, stance=0.45, offsets=[0.0, 0.5, 0.0, 0.5], lift=0.25, bob=0.04, susp=True),     # الجمل: نفس الجهة معًا
}


def quad_gait(name, phase, stride=1.0):
    """يرجع لكل رجل (x نسبي, رفع, على_الأرض) بوحدات طول الساق، + حركة الجسم (ارتفاع، ميل، أرجحة الرأس)."""
    g = QUAD[name]
    legs = []
    for off in g["offsets"]:
        p = (phase + off) % 1.0
        if p < g["stance"]:
            u = p / g["stance"]
            legs.append((0.5 * stride - stride * u, 0.0, True))
        else:
            u = (p - g["stance"]) / (1 - g["stance"])
            legs.append((-0.5 * stride + stride * ease(u), g["lift"] * math.sin(math.pi * u), False))
    down = sum(1 for l in legs if l[2])
    body_y = -g["bob"] * (1 if (g["susp"] and down == 0) else -0.5 * (down - 2) / 2)
    pitch = 4 * math.sin(2 * math.pi * phase) * (1.6 if name == "gallop" else 0.6)
    head = 6 * math.sin(2 * math.pi * (phase - 0.12) * (2 if name != "gallop" else 1))   # الرأس والعنق حركة ثانوية متأخرة
    return dict(legs=legs, body_y=body_y, pitch=pitch, head=head, beats=down)


# ---------------------------------------------------------------- الطيور
def wing_cycle(phase, size=1.0):
    """دورة جناح: يرجع (زاوية الكتف, طي الجناح 0..1, زاوية طرف الريش, إزاحة الجسم).
    الطائر الأكبر = ضربات أبطأ (اضبطي T بالحجم). أبطأ عند الأعلى والأسفل."""
    p = phase % 1.0
    if p < 0.5:                                    # ضربة سفلية: الجناح ممدود ويتحرك للأمام (الدفع)
        u = ease(p / 0.5)
        shoulder = 70 - 140 * u
        fold = 0.0
    else:                                          # صعود: مطوي لتقليل المقاومة
        u = ease((p - 0.5) / 0.5)
        shoulder = -70 + 140 * u
        fold = math.sin(math.pi * u) * 0.6
    tip_lag = 35 * math.sin(2 * math.pi * (p - 0.08))   # أطراف الريش تتأخر وتنحني (سحب)
    body = -8 * math.sin(2 * math.pi * p) * size         # الجسم يتحرك عكس دفع الجناح
    return shoulder, fold, tip_lag, body
