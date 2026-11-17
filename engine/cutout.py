"""شخصيات الرسوم المقصوصة (Cutout 2D) — هيكل عظمي حقيقي + مشي/جري/أكل/حركة يد بإحساس بشري.

مبادئ مطبّقة (من كتاب أساسيات الرسم + أسلوب GrowKaz):
- القيم الأربع للضوء: إضاءة (highlight) ← لون أساسي (mid-tone) ← ظل جوهري (core shadow) ← ظل ساقط (cast shadow)
  + حافة ضوء دافئة (rim) لأن الضوء دافئ والظل بارد (حرارة اللون).
- وزن الخط: خط خارجي سميك وداكن للشخصية (مركز الانتباه)، أنحف للأطراف البعيدة.
- البناء من أشكال أساسية: رأس دائرة، أطراف أسطوانات، كفوف دوائر.
- الحركة: الأقدام مثبتة على الأرض بحساب IK (لا انزلاق)، تموّج الورك، تأرجح الذراعين عكس الساقين،
  تأخر الشعر والقماش (follow-through)، رمش، تنفّس، وتسارع/تباطؤ ناعم (ease in/out).
"""
import math

LINE = "#2b1c17"


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def lerp(a, b, k):
    return a + (b - a) * k


def rot(p, a, o=(0, 0)):
    """تدوير نقطة p بزاوية a (درجات) حول o."""
    r = math.radians(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * math.cos(r) - y * math.sin(r), o[1] + x * math.sin(r) + y * math.cos(r))


def ik2(root, target, l1, l2, bend=1):
    """IK لعظمتين: يرجع موضع المفصل الأوسط. bend=+1 الركبة للأمام (+x)، -1 المرفق للخلف."""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = math.hypot(dx, dy)
    d = clamp(d, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    cos_b = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(clamp(cos_b, -1, 1))
    ang = a - bend * b
    return (root[0] + l1 * math.cos(ang), root[1] + l1 * math.sin(ang))


def fk2(root, a1, a2, l1, l2):
    """FK: a1 زاوية العضد من الأسفل (موجب = للأمام)، a2 ثني المرفق (موجب = يرفع الساعد للأمام)."""
    d1 = (math.sin(math.radians(a1)), math.cos(math.radians(a1)))
    mid = (root[0] + l1 * d1[0], root[1] + l1 * d1[1])
    a = a1 + a2
    d2 = (math.sin(math.radians(a)), math.cos(math.radians(a)))
    end = (mid[0] + l2 * d2[0], mid[1] + l2 * d2[1])
    return mid, end


# ------------------------------------------------------------------ رسم الأجزاء (SVG)
def P(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def limb(a, b, w, base, dark, light_side=1, lw=6.0, rim=None):
    """طرف أسطواني من a إلى b: خط خارجي، لون أساسي، ظل جوهري على الجهة البعيدة عن الضوء، وحافة ضوء."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    if nx * light_side > 0:
        nx, ny = -nx, -ny  # الظل على الجهة المعاكسة للضوء
    off = w * 0.22
    sa = (a[0] + nx * off, a[1] + ny * off)
    sb = (b[0] + nx * off, b[1] + ny * off)
    s = (f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{LINE}" stroke-width="{w + lw:.1f}" stroke-linecap="round"/>',
         f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{base}" stroke-width="{w:.1f}" stroke-linecap="round"/>',
         f'<line x1="{sa[0]:.1f}" y1="{sa[1]:.1f}" x2="{sb[0]:.1f}" y2="{sb[1]:.1f}" stroke="{dark}" stroke-width="{w * 0.45:.1f}" stroke-linecap="round"/>')
    out = list(s)
    if rim:
        ra = (a[0] - nx * w * 0.36, a[1] - ny * w * 0.36)
        rb = (b[0] - nx * w * 0.36, b[1] - ny * w * 0.36)
        out.append(f'<line x1="{ra[0]:.1f}" y1="{ra[1]:.1f}" x2="{rb[0]:.1f}" y2="{rb[1]:.1f}" stroke="{rim}" stroke-width="{w * 0.12:.1f}" stroke-linecap="round" opacity="0.7"/>')
    return out


def limb_chain(points, widths, base, dark, light_side=1, lw=6.0, rim=None):
    """سلسلة (ورك-ركبة-كاحل) بدون خطوط داخلية عند المفاصل: كل الخطوط الخارجية أولًا ثم الألوان."""
    segs = [limb(points[i], points[i + 1], widths[i], base, dark, light_side, lw, rim) for i in range(len(points) - 1)]
    out = []
    for k in range(4):
        for s in segs:
            if k < len(s):
                out.append(s[k])
    return "".join(out)


# ------------------------------------------------------------------ الشخصية
PALETTES = {
    "reem": dict(skin="#efbd97", skin_d="#cf9273", hair="#4a2a1c", hair_d="#2e1a12", hair_hi="#8a5a3a",
                 jacket="#6f7f6a", jacket_d="#53614f", jacket_hi="#9aa88e", jeans="#4d6f9c", jeans_d="#3a557c",
                 shoe="#8b9096", shoe_d="#6c7176", sole="#f3f1ec", bag="#454a51", bag_d="#2f3338",
                 lips="#c4706a", eye="#3a2318", rim="#ffd49a", scarf=None),
    # رجل كبير بشعر ولحية رماديين، معطف داكن (شخصية تاريخية — رسم محايد غير مسيء)
    "general": dict(skin="#d6a07c", skin_d="#b07f5e", hair="#a9a49c", hair_d="#7d786f", hair_hi="#d8d4cc",
                    jacket="#2c2f35", jacket_d="#1d1f24", jacket_hi="#59606c", jeans="#25272c", jeans_d="#17181c",
                    shoe="#141416", shoe_d="#0c0c0e", sole="#2a2a2e", bag=None, bag_d=None,
                    lips="#8a5446", eye="#2a1a12", rim="#9fc0ff", scarf=None, male=True,
                    far_d="#0e0f12", far_arm_d="#121418", leg_rim="#4a5260", brow_w=8.5),
}

# أطوال الهيكل (بوحدات الرسم؛ الطول الكلي ≈ 980 ≈ 7 رؤوس)
LT, LS, ANK = 225.0, 222.0, 26.0     # فخذ، ساق، ارتفاع الكاحل
UA, FA = 150.0, 138.0                # عضد، ساعد
TORSO = 292.0                        # من الورك إلى الكتف تقريبًا
SHOULDER = (-4.0, -262.0)            # موضع الكتف في إطار الجذع


class Pose:
    """كل ما يلزم لرسم إطار واحد."""

    def __init__(self, **kw):
        self.hip = (0.0, 0.0)          # موضع الورك (عالمي)
        self.lean = 0.0                # ميل الجذع (درجات، موجب للأمام)
        self.breath = 0.0
        self.head_tilt = 0.0           # موجب = ينظر للأسفل
        self.feet = [(0, 0, 0), (0, 0, 0)]   # (x, y, زاوية القدم) لكل قدم [قريبة، بعيدة]
        self.arm_near = ("fk", 10, 10)       # ("fk", a1, a2) أو ("ik", (x,y) في إطار الجذع, bend)
        self.arm_far = ("fk", -10, 10)
        self.blink = 0.0
        self.mouth = 0.0               # 0 مغلق، 1 مفتوح
        self.jaw = 0.0                 # مضغ
        self.smile = 0.0
        self.brow = 0.0                # + يرتفع
        self.hair_swing = 0.0          # إزاحة طرف الشعر (للخلف موجب)
        self.hair_bounce = 0.0
        self.prop = None               # ("apple", bites)
        self.twist = 0.0               # دوران معاكس للكتفين والوركين (+ = الكتف القريب للأمام)
        self.scale = 1.0
        self.__dict__.update(kw)


def _torso_to_world(p, pose):
    q = rot((p[0], p[1] * (1 + pose.breath * 0.01)), pose.lean)
    return (pose.hip[0] + q[0], pose.hip[1] + q[1])


def _arm_points(pose, which):
    spec = pose.arm_near if which == "near" else pose.arm_far
    sh_off = (6 - pose.twist, 0) if which == "far" else (pose.twist, 0)
    sh = _torso_to_world((SHOULDER[0] + sh_off[0], SHOULDER[1]), pose)
    if spec[0] == "fk":
        a1, a2 = spec[1] + pose.lean, spec[2]
        el, wr = fk2(sh, a1, a2, UA, FA)
    else:
        tgt = _torso_to_world(spec[1], pose) if spec[3] == "torso" else spec[1]
        el = ik2(sh, tgt, UA, FA, bend=spec[2])
        wr = tgt
    return sh, el, wr


def draw_character(pose, pal="reem"):
    """يرجع عناصر SVG للشخصية (متجهة لليمين). الضوء من أعلى اليمين."""
    c = PALETTES[pal]
    s = []
    hip = pose.hip
    # --- الذراع البعيدة (أغمق قليلًا: بُعد)
    sh, el, wr = _arm_points(pose, "far")
    s.append(limb_chain([sh, el, wr], [44, 38], c["jacket_d"], c.get("far_arm_d", "#465442"), lw=5))
    s.append(f'<circle cx="{wr[0]:.1f}" cy="{wr[1]:.1f}" r="21" fill="{c["skin_d"]}" stroke="{LINE}" stroke-width="5"/>')
    # --- الساقان
    for k, (fx, fy, fa) in enumerate(reversed(pose.feet)):
        far = (k == 0)
        hp = (hip[0] + (5 + pose.twist * 0.6 if far else -3 - pose.twist * 0.6), hip[1] + 6)
        ankle = (fx, fy - ANK)
        knee = ik2(hp, ankle, LT, LS, bend=1)        # الركبة للأمام دائمًا (تشريح الإنسان)
        base, dark = (c["jeans_d"], c.get("far_d", "#2f4666")) if far else (c["jeans"], c["jeans_d"])
        s.append(limb_chain([hp, knee, ankle], [66, 52], base, dark, lw=5.5 if far else 6.5, rim=None if far else c.get("leg_rim", "#8fb0d8")))
        # الكم السفلي للجينز (ثنية)
        s.append(f'<line x1="{ankle[0] - 22:.1f}" y1="{ankle[1] - 6:.1f}" x2="{ankle[0] + 22:.1f}" y2="{ankle[1] - 6:.1f}" stroke="{dark}" stroke-width="6" stroke-linecap="round"/>')
        s.append(shoe(ankle, fa, c, far))
    # --- الحوض (جينز)
    pv = _torso_to_world((2, -6), pose)
    s.append(f'<ellipse cx="{pv[0]:.1f}" cy="{pv[1]:.1f}" rx="54" ry="44" fill="{c["jeans"]}" stroke="{LINE}" stroke-width="6"/>')
    # --- الجذع (في إطار محلي ثم تحويل)
    tf = f'translate({hip[0]:.1f},{hip[1]:.1f}) rotate({pose.lean:.2f}) scale(1,{1 + pose.breath * 0.01:.4f})'
    s.append(f'<g transform="{tf}">')
    if c.get("bag"):  # حقيبة الظهر
        s.append(f'<rect x="-104" y="-262" width="66" height="150" rx="22" fill="{c["bag"]}" stroke="{LINE}" stroke-width="6"/>')
        s.append(f'<rect x="-104" y="-262" width="24" height="150" rx="12" fill="{c["bag_d"]}"/>')
        s.append(f'<rect x="-98" y="-190" width="46" height="56" rx="12" fill="{c["bag_d"]}" stroke="{LINE}" stroke-width="4"/>')
    jacket = ("M-50,-6 C-56,-80 -58,-170 -50,-246 C-44,-282 -18,-298 12,-296 C36,-292 50,-270 52,-236 "
              "C54,-180 46,-110 50,-30 L52,4 C10,10 -24,10 -50,6 Z")
    s.append(f'<path d="{jacket}" fill="{c["jacket"]}" stroke="{LINE}" stroke-width="6.5" stroke-linejoin="round"/>')
    # ظل جوهري على الظهر (الجهة البعيدة عن الضوء) + حافة ضوء أمامية
    s.append(f'<clipPath id="cj"><path d="{jacket}"/></clipPath>')
    s.append(f'<g clip-path="url(#cj)"><path d="M-60,-300 C-30,-200 -34,-80 -22,20 L-70,20 Z" fill="{c["jacket_d"]}"/>'
             f'<path d="M40,-280 C56,-200 50,-100 54,0" fill="none" stroke="{c["jacket_hi"]}" stroke-width="7" opacity="0.8"/>'
             f'<rect x="-60" y="-34" width="120" height="34" fill="{c["jacket_d"]}"/>'                       # حزام الخصر المطاطي
             f'<path d="M-40,-150 C-10,-140 20,-142 44,-156" fill="none" stroke="{c["jacket_d"]}" stroke-width="4" opacity="0.7"/>'  # ثنية قماش
             f'</g>')
    s.append(f'<path d="{jacket}" fill="none" stroke="{LINE}" stroke-width="6.5" stroke-linejoin="round"/>')
    s.append(f'<path d="M44,-250 L46,-30" stroke="{c["jacket_d"]}" stroke-width="3"/>')  # السحاب
    if c.get("male"):  # أزرار المعطف وياقة القميص
        for yb in (-220, -170, -120):
            s.append(f'<circle cx="38" cy="{yb}" r="5" fill="{c["jacket_hi"]}"/>')
        s.append(f'<path d="M10,-292 L36,-262 L40,-290 Z" fill="#e8e6e0" stroke="{LINE}" stroke-width="3"/>')
    # الياقة
    s.append(f'<path d="M-36,-286 C-20,-306 18,-308 34,-290 L28,-276 C10,-290 -16,-290 -30,-274 Z" fill="{c["jacket_d"]}" stroke="{LINE}" stroke-width="5"/>')
    if c.get("bag"):  # حزام الحقيبة على الصدر
      s.append(f'<path d="M-30,-282 C0,-270 22,-250 26,-210 L22,-120" fill="none" stroke="{LINE}" stroke-width="20" stroke-linecap="round"/>'
             f'<path d="M-30,-282 C0,-270 22,-250 26,-210 L22,-120" fill="none" stroke="{c["bag"]}" stroke-width="12" stroke-linecap="round"/>')
    s.append('</g>')
    # --- الرقبة والرأس
    neck = _torso_to_world((6, -290), pose)
    s.append(head(neck, pose, c))
    # --- الذراع القريبة (أمام كل شيء)
    sh, el, wr = _arm_points(pose, "near")
    s.append(limb_chain([sh, el, wr], [48, 40], c["jacket"], c["jacket_d"], lw=6.5, rim=c["jacket_hi"]))
    cuff = (lerp(el[0], wr[0], 0.86), lerp(el[1], wr[1], 0.86))
    s.append(f'<circle cx="{cuff[0]:.1f}" cy="{cuff[1]:.1f}" r="21" fill="{c["jacket_d"]}" stroke="{LINE}" stroke-width="5"/>')
    if pose.prop:
        s.append(prop(pose.prop, wr, el))
    s.append(f'<circle cx="{wr[0]:.1f}" cy="{wr[1]:.1f}" r="23" fill="{c["skin"]}" stroke="{LINE}" stroke-width="6"/>'
             f'<path d="M{wr[0] - 14:.1f},{wr[1] + 8:.1f} A16,16 0 0 0 {wr[0] + 12:.1f},{wr[1] + 12:.1f}" fill="none" stroke="{c["skin_d"]}" stroke-width="5"/>')
    return "".join(s)


def shoe(ankle, ang, c, far):
    base = c["shoe_d"] if far else c["shoe"]
    return (f'<g transform="translate({ankle[0]:.1f},{ankle[1] + ANK:.1f}) rotate({ang:.2f})">'
            f'<path d="M-28,-2 C-30,-26 -18,-40 2,-38 C24,-34 44,-24 66,-14 C80,-8 80,4 70,6 L-24,6 Z" fill="{base}" stroke="{LINE}" stroke-width="5.5" stroke-linejoin="round"/>'
            f'<path d="M-28,-2 L72,-2 C78,0 78,6 70,7 L-24,7 Z" fill="{c["sole"]}" stroke="{LINE}" stroke-width="4"/>'
            f'<path d="M6,-30 L30,-20 M14,-34 L36,-24" stroke="{c["sole"]}" stroke-width="3" opacity="0.8"/>'
            f'</g>')


def head(neck, pose, c):
    """رأس جانبي متجه لليمين. الأصل عند أسفل الرقبة."""
    tilt = pose.head_tilt + pose.lean * 0.4
    jaw = pose.jaw * 6
    hs = pose.hair_swing
    hb = pose.hair_bounce
    hsz = c.get("head", 1.2)   # رأس أكبر قليلًا (جاذبية الشخصية الكرتونية)
    s = [f'<g transform="translate({neck[0]:.1f},{neck[1]:.1f}) rotate({tilt:.2f}) scale({hsz})">']
    male = c.get("male")
    # الشعر الخلفي (طويل، يتأخر مع الحركة: follow-through)
    tipx, tipy = -64 - hs, 150 + hb
    midx = -78 - hs * 0.5
    if not male:
      s.append(f'<path d="M-6,-158 C-60,-162 -96,-120 -92,-60 C{midx:.1f},10 {tipx + 10:.1f},{tipy - 60:.1f} {tipx:.1f},{tipy:.1f} '
             f'C{tipx + 22:.1f},{tipy - 20:.1f} {-28 - hs * 0.3:.1f},{60:.1f} -24,-6 L0,-60 Z" fill="{c["hair"]}" stroke="{LINE}" stroke-width="6" stroke-linejoin="round"/>')
      s.append(f'<path d="M-70,-90 C{midx + 12:.1f},0 {tipx + 20:.1f},{tipy - 70:.1f} {tipx + 8:.1f},{tipy - 14:.1f}" fill="none" stroke="{c["hair_d"]}" stroke-width="10" stroke-linecap="round"/>')
    # الرقبة
    s.append(f'<path d="M-14,10 L-10,-40 L22,-40 L26,10 Z" fill="{c["skin_d"]}" stroke="{LINE}" stroke-width="5"/>')
    # الوجه (الجمجمة + الملامح الجانبية)
    face = (f"M-30,-34 C-62,-60 -66,-130 -30,-156 C2,-176 46,-164 58,-126 L62,-100 C70,-92 80,-80 78,-72 "
            f"C76,-66 68,-64 64,-62 C66,-56 66,-52 63,-49 C66,-{44 - jaw:.1f} 64,-{40 - jaw:.1f} 60,-{36 - jaw:.1f} "
            f"C58,-{24 - jaw:.1f} 48,-{14 - jaw:.1f} 32,-{14 - jaw:.1f} C14,-{14 - jaw:.1f} -4,-20 -30,-34 Z")
    s.append(f'<path d="{face}" fill="{c["skin"]}" stroke="{LINE}" stroke-width="6" stroke-linejoin="round"/>')
    s.append(f'<clipPath id="cf"><path d="{face}"/></clipPath>')
    s.append(f'<g clip-path="url(#cf)"><path d="M-70,-40 C-20,-30 20,-{20 - jaw:.1f} 70,-{22 - jaw:.1f} L70,0 L-70,0 Z" fill="{c["skin_d"]}"/>'   # ظل الفك
             f'<circle cx="34" cy="-64" r="14" fill="#f08a7a" opacity="0.35"/></g>')                                             # حمرة الخد
    # العين (لوزية) + رمش
    bl = 1 - clamp(pose.blink)
    s.append(f'<g transform="translate(40,-92) scale(1,{max(bl, 0.08):.3f})">'
             f'<path d="M-12,0 C-6,-9 8,-10 14,-2 C8,6 -6,6 -12,0 Z" fill="#fff" stroke="{LINE}" stroke-width="3"/>'
             f'<circle cx="6" cy="-1" r="6" fill="{c["eye"]}"/><circle cx="8" cy="-3" r="2" fill="#fff"/></g>')
    s.append(f'<path d="M26,-100 C34,-106 46,-106 56,-99" fill="none" stroke="{LINE}" stroke-width="4" stroke-linecap="round"/>')  # الرموش
    by = -112 - pose.brow * 6
    s.append(f'<path d="M24,{by + 2:.1f} C34,{by - 4:.1f} 46,{by - 4:.1f} 56,{by + 1:.1f}" fill="none" stroke="{c["hair_d"]}" stroke-width="{c.get("brow_w", 6.5)}" stroke-linecap="round"/>')
    # الأنف (إسفين ظل)
    s.append(f'<path d="M62,-96 L74,-72 L64,-68" fill="none" stroke="{c["skin_d"]}" stroke-width="4" stroke-linejoin="round"/>')
    # الفم: مغلق/مبتسم/مفتوح للقضم
    mo = pose.mouth
    if mo > 0.1:
        s.append(f'<ellipse cx="58" cy="{-47 + jaw * 0.5:.1f}" rx="{6 + mo * 4:.1f}" ry="{2 + mo * 7:.1f}" fill="#7a2e2a" stroke="{LINE}" stroke-width="3"/>')
    else:
        sm = pose.smile * 4
        s.append(f'<path d="M50,{-48 + jaw * 0.6:.1f} C54,{-46 + sm + jaw * 0.6:.1f} 60,{-46 + sm + jaw * 0.6:.1f} 64,{-50 + jaw * 0.6:.1f}" fill="none" stroke="{c["lips"]}" stroke-width="4" stroke-linecap="round"/>')
    # الأذن
    s.append(f'<ellipse cx="-8" cy="-84" rx="11" ry="17" fill="{c["skin"]}" stroke="{LINE}" stroke-width="4"/>')
    if male:
        # لحية قصيرة رمادية تتبع الفك + شارب، وشعر قصير
        s.append(f'<path d="M-24,-60 C-20,-36 0,-{16 - jaw:.1f} 30,-{10 - jaw:.1f} C50,-{8 - jaw:.1f} 62,-{22 - jaw:.1f} 64,-{36 - jaw:.1f} '
                 f'C60,-48 52,-50 46,-46 C40,-58 20,-56 6,-62 C-6,-70 -16,-74 -24,-60 Z" fill="{c["hair"]}" stroke="{LINE}" stroke-width="5" stroke-linejoin="round"/>')
        s.append(f'<path d="M-10,-50 C10,-30 34,-{22 - jaw:.1f} 56,-{30 - jaw:.1f}" fill="none" stroke="{c["hair_d"]}" stroke-width="6" opacity="0.7"/>')
        s.append(f'<path d="M48,-56 C56,-60 66,-58 70,-54" fill="none" stroke="{c["hair_d"]}" stroke-width="7" stroke-linecap="round"/>')
        s.append(f'<path d="M-62,-104 C-70,-150 -30,-174 8,-170 C40,-168 58,-150 58,-126 C40,-136 20,-138 0,-132 C-14,-126 -22,-112 -24,-96 '
                 f'C-34,-92 -48,-94 -62,-104 Z" fill="{c["hair"]}" stroke="{LINE}" stroke-width="6" stroke-linejoin="round"/>')
        s.append(f'<path d="M-44,-152 C-14,-166 20,-162 42,-146" fill="none" stroke="{c["hair_hi"]}" stroke-width="5" stroke-linecap="round" opacity="0.8"/>')
        s.append('</g>')
        return "".join(s)
    # الشعر العلوي + الغرّة (فوق الأذن جزئيًا)
    s.append(f'<path d="M-66,-96 C-74,-150 -30,-178 10,-172 C44,-168 64,-146 60,-118 C48,-128 30,-132 14,-124 '
             f'C8,-112 -4,-108 -14,-112 C-20,-96 -30,-80 -36,-60 C-46,-70 -58,-84 -66,-96 Z" fill="{c["hair"]}" stroke="{LINE}" stroke-width="6" stroke-linejoin="round"/>')
    s.append(f'<path d="M-40,-160 C-10,-172 26,-166 46,-146" fill="none" stroke="{c["hair_hi"]}" stroke-width="6" stroke-linecap="round" opacity="0.8"/>')  # لمعة الشعر (highlight)
    s.append('</g>')
    return "".join(s)


def prop(spec, wr, el):
    kind = spec[0]
    if kind == "apple":
        bites = spec[1]
        ang = math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0]))
        cx, cy = rot((wr[0] + 26, wr[1] - 6), ang - 0, wr) if False else (wr[0] + 18, wr[1] - 22)
        s = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="27" fill="#c8302c" stroke="{LINE}" stroke-width="5"/>'
             f'<path d="M{cx - 18:.1f},{cy + 8:.1f} A22,22 0 0 0 {cx + 10:.1f},{cy + 22:.1f}" fill="none" stroke="#8e1c1a" stroke-width="7"/>'
             f'<ellipse cx="{cx + 9:.1f}" cy="{cy - 12:.1f}" rx="6" ry="4" fill="#ff9a8a" opacity="0.9"/>'
             f'<path d="M{cx:.1f},{cy - 26:.1f} L{cx + 3:.1f},{cy - 38:.1f}" stroke="{LINE}" stroke-width="4"/>'
             f'<path d="M{cx + 3:.1f},{cy - 34:.1f} C{cx + 14:.1f},{cy - 44:.1f} {cx + 22:.1f},{cy - 36:.1f} {cx + 14:.1f},{cy - 30:.1f} Z" fill="#6a9a3a" stroke="{LINE}" stroke-width="3"/>')
        for b in range(bites):
            bx, by = cx + 24 - b * 6, cy - 8 + b * 14
            s += f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="12" fill="#f6e6b8" stroke="{LINE}" stroke-width="4"/>'
        return s
    return ""


# ------------------------------------------------------------------ مشية/جري: محرك الخطوات
GAITS = {
    #        دورة(ث)  نسبة الارتكاز  طول الخطوة  رفع القدم  هبوط الورك  ميل  تأرجح الذراع  ثني المرفق
    "walk": dict(T=1.04, stance=0.62, S=300.0, lift=46.0, bob=9.0, lean=3.0, arm=20.0, elbow=14.0),
    "run": dict(T=0.66, stance=0.40, S=360.0, lift=120.0, bob=20.0, lean=12.0, arm=42.0, elbow=88.0),
}


def foot_rel(phase, g, amp):
    """موضع القدم بالنسبة للورك ضمن دورة المشي. يرجع (x, رفع, زاوية, في_ارتكاز).
    تدحرج القدم البشري: الكعب يلمس أولًا (المقدمة مرفوعة) ← القدم تنبسط ← الكعب يرتفع والقدم تدور على الأصابع ← دفعة."""
    p = phase % 1.0
    S = g["S"] * amp
    st = g["stance"]
    if p < st:
        u = p / st
        x = S / 2 - S * u
        if u < 0.14:                                         # تلامس الكعب: مقدمة القدم مرفوعة ثم تنبسط
            ang = -16 * amp * (1 - ease(u / 0.14))
            lift = 0.0
        elif u > 0.68:                                       # رفع الكعب: الدوران حول الأصابع
            k = ease((u - 0.68) / 0.32)
            ang = 30 * amp * k
            lift = math.sin(math.radians(ang)) * 70
        else:
            ang, lift = 0.0, 0.0
        return x, lift, ang, True
    u = (p - st) / (1 - st)
    e = ease_io(u)
    x = -S / 2 + S * e
    lift = g["lift"] * amp * math.sin(math.pi * u) ** 1.2 + math.sin(math.radians(30 * amp)) * 70 * (1 - ease(u / 0.3))
    ang = (30 - 46 * ease(u)) * amp                          # بعد الدفع الأصابع للأسفل، ثم ترتفع المقدمة استعدادًا للكعب
    return x, lift, ang, False


# ====================================================================== من كتاب Animation: The Mechanics of Motion
# المشية "سقوط مُتحكَّم فيه": وضعيتان مفتاحيتان — الخطوة/التلامس (الجسم في أخفض نقطة) والعبور (أعلى نقطة، ساق مستقيمة).
# الذراع عكس الساق (دوران معاكس للكتفين والوركين). الجري فيه "مرحلة تعليق" بلا قدم على الأرض، وفي العبور ينخفض الجسم
# (الساق تمتص الصدمة) عكس المشي. الشخصية تظهر في مشيتها: الواثق، الحزين، الكبير بالسن، المتسلل...
GAITS.update({
    "confident": dict(T=0.95, stance=0.6, S=340.0, lift=50.0, bob=10.0, lean=5.0, arm=26.0, elbow=16.0, head=-3.0),
    "happy": dict(T=0.88, stance=0.58, S=320.0, lift=62.0, bob=18.0, lean=-1.0, arm=30.0, elbow=20.0, head=-5.0, double=True),
    "sad": dict(T=1.5, stance=0.66, S=170.0, lift=12.0, bob=3.0, lean=9.0, arm=5.0, elbow=6.0, head=14.0),
    "old": dict(T=1.6, stance=0.7, S=150.0, lift=10.0, bob=2.0, lean=13.0, arm=4.0, elbow=28.0, head=8.0),
    "sneak": dict(T=1.8, stance=0.55, S=360.0, lift=75.0, bob=6.0, lean=16.0, arm=14.0, elbow=70.0, head=4.0),
    "jog": dict(T=0.8, stance=0.45, S=240.0, lift=80.0, bob=14.0, lean=4.0, arm=18.0, elbow=95.0, head=0.0),
})
GAITS["run"]["lean"] = 7.0      # الجري السريع منتصب نسبيًا (لا ينحني كثيرًا إلا عند الانطلاق)

ARM_LAG = 0.045    # حركة متداخلة: الذراعان تتأخران قليلًا عن الساقين (المحرّك الأساسي هو الورك)
HEAD_LAG = 0.07    # الرأس يتأخر أكثر (حركة ثالثية بعد الجذع)


def gait_pose(name, phase, amp=1.0):
    """يرجع كل قنوات الحركة لمشية ما عند طور معيّن، مع التداخل والتأخير."""
    g = GAITS[name]
    p = phase % 1.0
    is_run = g["stance"] < 0.5
    feet = [foot_rel(p + off, g, amp) for off in (0.0, 0.5)]
    if is_run:   # أخفض نقطة منتصف الارتكاز (امتصاص الصدمة)، أعلى نقطة في التعليق
        bob = g["bob"] * amp * (0.5 + 0.5 * math.cos(4 * math.pi * (p - g["stance"] / 2)))
    else:        # أخفض نقطة عند التلامس، أعلى نقطة عند العبور
        bob = g["bob"] * amp * (0.5 + 0.5 * math.cos(4 * math.pi * p))
        if g.get("double"):   # ارتداد مزدوج (مشية سعيدة/كرتونية): ضغطة إضافية قبل التلامس
            bob += g["bob"] * 0.35 * amp * max(0.0, math.sin(4 * math.pi * p - 0.6)) ** 2
    pa = p - ARM_LAG
    sw = math.cos(2 * math.pi * pa)
    arm_near = (-g["arm"] * amp * sw, g["elbow"] + (10 * amp * max(0.0, -sw) if not is_run else 0))
    arm_far = (g["arm"] * amp * sw, g["elbow"] + (10 * amp * max(0.0, sw) if not is_run else 0))
    head = g.get("head", 0.0) * amp - 1.5 * amp * math.sin(4 * math.pi * (p - HEAD_LAG))
    twist = 9.0 * amp * math.cos(2 * math.pi * (p - ARM_LAG)) * (-1)       # الكتف القريب يتقدم مع ذراعه
    lean = g["lean"] * amp + 1.6 * amp * math.cos(4 * math.pi * (p - 0.03))  # ميل خفيف للأمام عند كل تلامس (سقوط مُتحكَّم فيه)
    return dict(feet=feet, bob=bob, lean=lean, twist=twist, arm_near=arm_near, arm_far=arm_far, head=head,
                hair_bounce=6 * amp * math.sin(4 * math.pi * (p - HEAD_LAG * 2) + 0.8))


def lipsync_track(wav_path, fps, early_frames=2, levels=(0.08, 0.3)):
    """مزامنة الشفاه من ملف الصوت: شكل الفم يسبق الصوت بإطارين (مبكرًا لا متأخرًا أبدًا)،
    وبثلاثة أشكال فقط (مغلق/نصف/مفتوح) — الإفراط في تحريك الفم يبدو مصطنعًا."""
    import numpy as np
    from scipy.io import wavfile
    sr, x = wavfile.read(wav_path)
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    x /= (np.abs(x).max() + 1e-6)
    hop = int(sr / fps)
    env = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x), hop)])
    env /= env.max() + 1e-6
    shapes = np.where(env > levels[1], 1.0, np.where(env > levels[0], 0.5, 0.0))
    for i in range(1, len(shapes) - 1):           # لا شكل يظهر أقل من إطارين (وإلا يضيع على المشاهد)
        if shapes[i] != shapes[i - 1] and shapes[i] != shapes[i + 1]:
            shapes[i] = shapes[i - 1]
    return np.concatenate([shapes[early_frames:], np.zeros(early_frames)])
