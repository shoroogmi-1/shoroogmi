"""مركبات مرسومة بأبعادها الحقيقية (بالمتر) — قاعدة: نحاكي الواقع ولا نتوهّم.

المقاسات من مواصفات المصنّع:
  Toyota Avalon (2019–2022): الطول 4.975م، الارتفاع 1.435م، قاعدة العجلات 2.870م، قطر العجلة ≈ 0.68م
  Hyundai H-1 / Grand Starex: الطول 5.15–5.169م، الارتفاع 1.925م، قاعدة العجلات 3.200م، قطر العجلة ≈ 0.69م
  MQ-9 Reaper: الطول 11م، امتداد الجناحين 20م، مروحة دافعة خلفية، ذيل V مقلوب، كرة حساسات تحت المقدمة
المرجع البشري: رجل بالغ ≈ 1.72م — فالسيارة السيدان تصل تقريبًا لكتفه، والفان أطول منه قليلًا.
"""
import math

LINE = "#0c0d10"


def _wheel(cx, cy, r, ang, rim="#9aa1ab"):
    s = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="#0b0b0d" stroke="{LINE}" stroke-width="{r * 0.06:.1f}"/>'
         f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.62:.1f}" fill="#2a2d33"/>')
    for k in range(5):  # جنط بخمسة أذرع
        a = ang + k * 2 * math.pi / 5
        s += (f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + r * 0.58 * math.cos(a):.1f}" y2="{cy + r * 0.58 * math.sin(a):.1f}" '
              f'stroke="{rim}" stroke-width="{r * 0.16:.1f}" stroke-linecap="round"/>')
    s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * 0.14:.1f}" fill="{rim}"/>'
    return s


def avalon(x_rear, ground, ppm, wheel_ang=0.0, color="#121418", hi="#4a5464", lights=True, brake=False):
    """تويوتا أفالون جانبية متجهة لليمين. x_rear: طرف السيارة الخلفي بالبكسل، ppm: بكسل لكل متر."""
    def P(x, y):
        return f"{x_rear + x * ppm:.1f},{ground - y * ppm:.1f}"
    body = ("M" + P(0.05, 0.30) + " L" + P(0.0, 0.52) + " L" + P(0.08, 0.92) + " L" + P(0.55, 1.00) +
            " C" + P(0.95, 1.05) + " " + P(1.2, 1.32) + " " + P(1.55, 1.40) +
            " L" + P(2.70, 1.435) + " C" + P(3.0, 1.42) + " " + P(3.25, 1.18) + " " + P(3.55, 1.02) +
            " L" + P(4.55, 0.88) + " C" + P(4.85, 0.84) + " " + P(4.97, 0.72) + " " + P(4.975, 0.55) +
            " L" + P(4.92, 0.28) + " Z")
    s = f'<path d="{body}" fill="{color}" stroke="{LINE}" stroke-width="{ppm * 0.025:.1f}" stroke-linejoin="round"/>'
    glass = "M" + P(1.42, 1.02) + " L" + P(1.62, 1.31) + " L" + P(2.68, 1.37) + " L" + P(3.32, 1.03) + " Z"
    s += f'<path d="{glass}" fill="#1b2638" stroke="{LINE}" stroke-width="{ppm * 0.015:.1f}"/>'
    s += f'<path d="M{P(2.36, 1.37)} L{P(2.33, 1.02)}" stroke="{color}" stroke-width="{ppm * 0.07:.1f}"/>'          # العمود B
    s += f'<path d="M{P(1.75, 1.28)} L{P(2.2, 1.31)}" stroke="#56688a" stroke-width="{ppm * 0.03:.1f}" opacity="0.5"/>'  # انعكاس الزجاج
    s += f'<path d="M{P(0.1, 0.9)} L{P(4.6, 0.86)}" stroke="{hi}" stroke-width="{ppm * 0.02:.1f}" opacity="0.8"/>'      # خط الكتف (إضاءة)
    for xd in (1.45, 2.35, 3.33):                                                                                         # فواصل الأبواب
        s += f'<path d="M{P(xd, 1.0)} L{P(xd + 0.03, 0.38)}" stroke="{LINE}" stroke-width="{ppm * 0.012:.1f}"/>'
    for xh in (1.95, 2.95):                                                                                               # مقابض
        s += f'<path d="M{P(xh, 0.86)} L{P(xh + 0.18, 0.86)}" stroke="{hi}" stroke-width="{ppm * 0.025:.1f}"/>'
    s += f'<path d="M{P(0.02, 0.88)} L{P(0.32, 0.92)}" stroke="#ff2a2a" stroke-width="{ppm * 0.05:.1f}" opacity="{1 if lights else 0.4}"/>'
    if lights:
        s += f'<path d="M{P(4.68, 0.80)} L{P(4.93, 0.74)}" stroke="#f6f3e6" stroke-width="{ppm * 0.05:.1f}"/>'
    for wx in (1.05, 3.92):
        s += _wheel(x_rear + wx * ppm, ground - 0.34 * ppm, 0.34 * ppm, wheel_ang)
    return s


def starex(x_rear, ground, ppm, wheel_ang=0.0, color="#2b2e33", hi="#5d6672", lights=True):
    """هيونداي ستاريكس (H-1) فان جانبي متجه لليمين — جسم صندوقي، مقدمة قصيرة مائلة."""
    def P(x, y):
        return f"{x_rear + x * ppm:.1f},{ground - y * ppm:.1f}"
    body = ("M" + P(0.04, 0.30) + " L" + P(0.0, 1.80) + " C" + P(0.02, 1.90) + " " + P(0.12, 1.925) + " " + P(0.3, 1.925) +
            " L" + P(3.95, 1.925) + " C" + P(4.15, 1.92) + " " + P(4.45, 1.55) + " " + P(4.75, 1.18) +
            " L" + P(5.02, 1.02) + " C" + P(5.11, 0.95) + " " + P(5.125, 0.75) + " " + P(5.12, 0.5) + " L" + P(5.06, 0.28) + " Z")
    s = f'<path d="{body}" fill="{color}" stroke="{LINE}" stroke-width="{ppm * 0.025:.1f}" stroke-linejoin="round"/>'
    s += f'<path d="M{P(0.25, 1.28)} L{P(0.25, 1.72)} L{P(3.95, 1.74)} L{P(4.55, 1.25)} Z" fill="#1b2638" stroke="{LINE}" stroke-width="{ppm * 0.015:.1f}"/>'
    for xp in (1.25, 2.35, 3.45):                                                                                         # أعمدة النوافذ
        s += f'<path d="M{P(xp, 1.26)} L{P(xp, 1.74)}" stroke="{color}" stroke-width="{ppm * 0.07:.1f}"/>'
    s += f'<path d="M{P(2.35, 1.22)} L{P(2.35, 0.36)} M{P(3.45, 1.22)} L{P(3.45, 0.36)}" stroke="{LINE}" stroke-width="{ppm * 0.012:.1f}"/>'  # الباب المنزلق
    s += f'<path d="M{P(0.1, 1.15)} L{P(4.8, 1.12)}" stroke="{hi}" stroke-width="{ppm * 0.02:.1f}" opacity="0.7"/>'
    s += f'<path d="M{P(0.0, 1.1)} L{P(0.0, 0.75)}" stroke="#ff2a2a" stroke-width="{ppm * 0.06:.1f}" opacity="{1 if lights else 0.4}"/>'
    if lights:
        s += f'<path d="M{P(4.9, 0.92)} L{P(5.1, 0.86)}" stroke="#f6f3e6" stroke-width="{ppm * 0.06:.1f}"/>'
    for wx in (0.95, 4.15):
        s += _wheel(x_rear + wx * ppm, ground - 0.345 * ppm, 0.345 * ppm, wheel_ang, rim="#7d848e")
    return s


def reaper_planform(cx, cy, ppm, heading=180.0):
    """MQ-9 من الأسفل (منظر سفلي): جسم 11م، جناحان 20م مستقيمان، ذيل V، مروحة دافعة خلفية، كرة حساسات أمامية."""
    def R(x, y):
        a = math.radians(heading)
        return f"{cx + (x * math.cos(a) - y * math.sin(a)) * ppm:.1f},{cy + (x * math.sin(a) + y * math.cos(a)) * ppm:.1f}"
    fus = ("M" + R(5.5, 0) + " C" + R(5.4, -0.55) + " " + R(4.2, -0.6) + " " + R(3.0, -0.45) + " L" + R(-4.8, -0.32) +
           " L" + R(-5.4, -0.15) + " L" + R(-5.4, 0.15) + " L" + R(-4.8, 0.32) + " L" + R(3.0, 0.45) +
           " C" + R(4.2, 0.6) + " " + R(5.4, 0.55) + " " + R(5.5, 0) + " Z")
    wing = ("M" + R(0.9, -0.3) + " L" + R(0.55, -10.0) + " L" + R(-0.25, -10.0) + " L" + R(-0.45, -0.3) +
            " L" + R(-0.45, 0.3) + " L" + R(-0.25, 10.0) + " L" + R(0.55, 10.0) + " L" + R(0.9, 0.3) + " Z")
    tail = ("M" + R(-3.9, -0.2) + " L" + R(-5.0, -2.6) + " L" + R(-5.5, -2.6) + " L" + R(-5.0, -0.2) + " Z " +
            "M" + R(-3.9, 0.2) + " L" + R(-5.0, 2.6) + " L" + R(-5.5, 2.6) + " L" + R(-5.0, 0.2) + " Z")
    s = (f'<path d="{wing}" fill="#3a404c" stroke="{LINE}" stroke-width="{ppm * 0.06:.1f}" stroke-linejoin="round"/>'
         f'<path d="{tail}" fill="#3a404c" stroke="{LINE}" stroke-width="{ppm * 0.05:.1f}"/>'
         f'<path d="{fus}" fill="#4a515e" stroke="{LINE}" stroke-width="{ppm * 0.06:.1f}"/>'
         f'<circle cx="{R(4.6, 0).split(",")[0]}" cy="{R(4.6, 0).split(",")[1]}" r="{0.38 * ppm:.1f}" fill="#22262d" stroke="{LINE}" stroke-width="{ppm * 0.04:.1f}"/>')
    for side in (-1, 1):   # صاروخان تحت الجناح (Hellfire)
        s += f'<path d="M{R(0.9, side * 3.2)} L{R(-0.8, side * 3.2)}" stroke="#20242a" stroke-width="{0.22 * ppm:.1f}" stroke-linecap="round"/>'
    pa, pb = R(-5.55, -1.15), R(-5.55, 1.15)
    s += f'<path d="M{pa} L{pb}" stroke="#7d8698" stroke-width="{0.14 * ppm:.1f}" opacity="0.55"/>'   # المروحة الدافعة (ضبابية بالدوران)
    return s
