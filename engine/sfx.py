"""مكتبة الأصوات السينمائية — كلها مولَّدة رياضيًا (بدون حقوق، بدون إنترنت).

كل دالة ترجع مصفوفة ستيريو float32 بشكل (n, 2) بتردد SR.
"""
import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- أدوات
def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _noise(n, seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    return r.standard_normal(n).astype(np.float32)


def _lp(x, fc, order=4):
    sos = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2), "low", output="sos")
    return signal.sosfilt(sos, x, axis=0)


def _hp(x, fc, order=4):
    sos = signal.butter(order, fc / (SR / 2), "high", output="sos")
    return signal.sosfilt(sos, x, axis=0)


def _bp(x, lo, hi, order=3):
    sos = signal.butter(order, [lo / (SR / 2), min(hi, SR / 2 - 100) / (SR / 2)], "band", output="sos")
    return signal.sosfilt(sos, x, axis=0)


def _sweep_filter(x, f_start, f_end, q=1.5, curve=1.0):
    """فلتر يتحرك مع الزمن (عبر STFT) — أساس الـ whoosh والـ riser."""
    nper = 2048
    f, tt, Z = signal.stft(x, SR, nperseg=nper)
    prog = np.linspace(0, 1, Z.shape[1]) ** curve
    fc = f_start * (f_end / f_start) ** prog
    bw = fc / q
    mask = np.exp(-0.5 * ((f[:, None] - fc[None, :]) / bw[None, :]) ** 2)
    _, y = signal.istft(Z * mask, SR, nperseg=nper)
    y = y[: len(x)]
    if len(y) < len(x):
        y = np.pad(y, (0, len(x) - len(y)))
    return y


def _env(n, a=0.01, r=0.5, shape="exp"):
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    if shape == "exp":
        rel = np.exp(-np.maximum(t - a, 0) / max(r, 1e-4))
    else:
        rel = np.clip(1 - (t - a) / max(r, 1e-4), 0, 1)
    return att * rel


def reverb(x, size=2.5, wet=0.35, seed=3):
    """ريفيرب قاعة: استجابة نبضية من ضجيج متناقص."""
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    n = int(size * SR)
    out = np.zeros((len(x) + n - 1, 2), np.float32)
    for ch in range(2):
        ir = _noise(n, seed + ch) * np.exp(-np.arange(n) / (SR * size / 6.0))
        ir = _lp(ir, 6000, 2)
        ir /= np.sqrt((ir ** 2).sum()) + 1e-9
        out[:, ch] = signal.fftconvolve(x[:, ch], ir)
    dry = np.zeros_like(out)
    dry[: len(x)] = x
    return (dry * (1 - wet) + out * wet * 3).astype(np.float32)


def stereo(x, pan=0.0, width=0.0):
    """pan من ‎-1 (يسار) إلى 1 (يمين)."""
    if x.ndim == 2:
        return x
    l = x * np.sqrt((1 - pan) / 2)
    r = x * np.sqrt((1 + pan) / 2)
    if width:
        d = int(0.012 * SR * width)
        r = np.concatenate([np.zeros(d), r[:-d]]) if d else r
    return np.stack([l, r], 1).astype(np.float32)


def normalize(x, peak=0.9):
    m = np.abs(x).max()
    return (x / m * peak).astype(np.float32) if m > 0 else x


def _saw(freq, t, detune=0.0):
    ph = np.cumsum(np.full_like(t, freq * (1 + detune)) / SR) if np.isscalar(freq) else np.cumsum(freq * (1 + detune) / SR)
    return 2 * (ph % 1.0) - 1


def _note(name):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    return 220.0 * 2 ** (names[name] / 12)


# ---------------------------------------------------------------- الأصوات
def boom(dur=4.0):
    """ضربة سينمائية ضخمة (trailer hit)."""
    t = _t(dur)
    f = 30 + 60 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1)
    crack = _lp(_noise(len(t)), 3000) * np.exp(-t / 0.08)
    body = _lp(_noise(len(t)), 400) * np.exp(-t / 0.6)
    x = sub * 1.0 + crack * 0.5 + body * 0.6
    x = np.tanh(x * 1.6)
    return normalize(reverb(stereo(x, width=1), 3.5, 0.4))


def impact(dur=1.5):
    """ضربة قصيرة حادة."""
    t = _t(dur)
    f = 45 + 120 * np.exp(-t * 25)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.25)
    snap = _bp(_noise(len(t)), 800, 7000) * np.exp(-t / 0.03)
    return normalize(reverb(stereo(np.tanh(2 * (thump + 0.6 * snap)), width=1), 1.8, 0.3))


def sub_drop(dur=3.0):
    t = _t(dur)
    f = 70 * np.exp(-t * 1.2) + 22
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.005, dur / 2.5)
    return normalize(stereo(np.tanh(x * 1.5)))


def riser(dur=5.0):
    """تصاعد توتر ينتهي عند آخر الملف — ضعه قبل الضربة."""
    t = _t(dur)
    n = _noise(len(t))
    swept = _sweep_filter(n, 200, 9000, q=2.5, curve=2.0)
    f = 110 * 2 ** (t / dur * 2)
    tone = (_saw(f, t) + _saw(f, t, 0.007)) * 0.25
    tone = _lp(tone, 4000)
    amp = (t / dur) ** 2.2
    x = (swept * 1.2 + tone) * amp
    return normalize(reverb(stereo(x, width=1), 2.0, 0.3))


def reverse_swell(dur=2.5):
    """ضربة معكوسة تشفط نحو القطع."""
    x = impact(dur)
    x = reverb(x, 2.5, 0.8)[: int(dur * SR)]
    return normalize(x[::-1].copy())


def whoosh(dur=1.2, direction=1):
    """مرور سريع (للانتقالات وحركة الكاميرا). direction: 1 من اليسار لليمين."""
    t = _t(dur)
    n = _noise(len(t))
    up = _sweep_filter(n, 300, 4000, q=1.2)
    bell = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2.5
    x = up * bell
    pan = np.linspace(-0.9, 0.9, len(t)) * direction
    l = x * np.sqrt((1 - pan) / 2)
    r = x * np.sqrt((1 + pan) / 2)
    return normalize(reverb(np.stack([l, r], 1), 1.2, 0.2))


def braam(dur=5.0, note="D"):
    """النفخة النحاسية العملاقة (أسلوب Inception)."""
    t = _t(dur)
    f0 = _note(note) / 4
    x = sum(_saw(f0 * m, t, d) for m in (1, 1.5, 2) for d in (-0.004, 0, 0.005))
    cutoff = 150 + 2500 * np.clip(t / 0.6, 0, 1) * np.exp(-t / (dur * 0.6))
    # فلتر متغير بتقسيم كتل
    out = np.zeros_like(x)
    blk = 2048
    zi = None
    for i in range(0, len(x), blk):
        sos = signal.butter(2, min(cutoff[i], 20000) / (SR / 2), "low", output="sos")
        if zi is None:
            zi = signal.sosfilt_zi(sos) * 0
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    out = np.tanh(out * 0.9) * _env(len(t), 0.05, dur * 0.45)
    return normalize(reverb(stereo(out, width=1), 4.0, 0.45))


def drone(dur=20.0, note="D", dark=True):
    """طبقة توتر مستمرة تحت المشهد."""
    t = _t(dur)
    f0 = _note(note) / (4 if dark else 2)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * t / 7)
    x = sum(_saw(f0 * m, t, d) * g for m, g in ((1, 1), (2, 0.4), (3, 0.15)) for d in (-0.003, 0.002))
    x = _lp(x, 500 if dark else 1200) * (0.6 + 0.4 * lfo)
    air = _bp(_noise(len(t)), 300, 1500) * 0.05 * lfo
    fade = np.clip(t / 2, 0, 1) * np.clip((dur - t) / 2, 0, 1)
    return normalize(reverb(stereo((x + air) * fade, width=1), 3.0, 0.5), 0.6)


def pad(dur=20.0, chord=("D", "F", "A"), octave=1.0):
    """فراش وتري حزين/ملحمي (موسيقى خلفية)."""
    t = _t(dur)
    x = np.zeros_like(t)
    for nm in chord:
        f = _note(nm) * octave
        for d in (-0.006, -0.002, 0.003, 0.007):
            x += _saw(f, t, d)
    vib = 1 + 0.15 * np.sin(2 * np.pi * t / 5)
    x = _lp(x, 1400) * vib / 12
    fade = np.clip(t / 3, 0, 1) * np.clip((dur - t) / 3, 0, 1)
    return normalize(reverb(stereo(x * fade, width=1), 4.5, 0.55), 0.6)


def taiko(dur=8.0, bpm=90, pattern="x..x..x.x.x..x.."):
    """طبول حرب/ملحمية بنمط إيقاعي."""
    t = _t(dur)
    out = np.zeros(len(t))
    step = 60 / bpm / 4
    hit_t = _t(1.2)
    f = 40 + 70 * np.exp(-hit_t * 18)
    hit = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-hit_t / 0.35)
    hit += _lp(_noise(len(hit_t)), 1500) * np.exp(-hit_t / 0.05) * 0.4
    i, k = 0, 0
    while i * step < dur:
        if pattern[k % len(pattern)] == "x":
            s = int(i * step * SR)
            e = min(len(out), s + len(hit))
            out[s:e] += hit[: e - s] * (0.8 + 0.2 * RNG.random())
        i += 1
        k += 1
    return normalize(reverb(stereo(np.tanh(out * 1.3), width=1), 2.5, 0.35))


def heartbeat(dur=6.0, bpm=62):
    t = _t(dur)
    out = np.zeros(len(t))
    b = _t(0.25)
    lub = np.sin(2 * np.pi * 50 * b) * np.exp(-b / 0.05)
    period = 60 / bpm
    k = 0.0
    while k < dur:
        for off, g in ((0, 1.0), (0.28, 0.7)):
            s = int((k + off) * SR)
            e = min(len(out), s + len(lub))
            if s < len(out):
                out[s:e] += lub[: e - s] * g
        k += period
    return normalize(stereo(_lp(out, 200)))


def wind(dur=10.0):
    t = _t(dur)
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * t / 4.3) * np.sin(2 * np.pi * t / 1.7 + 1)
    l = _sweep_filter(_noise(len(t), 1), 400, 900, q=1.0) * mod
    r = _sweep_filter(_noise(len(t), 2), 900, 400, q=1.0) * mod[::-1]
    fade = np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)
    return normalize(np.stack([l, r], 1) * fade[:, None], 0.6)


def rain(dur=10.0):
    t = _t(dur)
    bed = _bp(_noise(len(t)), 1500, 9000) * 0.25
    drops = np.zeros(len(t))
    idx = RNG.integers(0, len(t), int(dur * 120))
    drops[idx] = RNG.uniform(0.3, 1, len(idx))
    drops = _hp(signal.lfilter([1], [1, -0.93], drops), 2000)
    x = stereo(bed + drops * 0.5, width=1)
    fade = np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)
    return normalize(x * fade[:, None], 0.6)


def thunder(dur=6.0):
    t = _t(dur)
    crack = _hp(_noise(len(t)), 1500) * np.exp(-t / 0.15)
    roll = _lp(_noise(len(t)), 180) * (np.exp(-t / 1.8) * (1 + 0.6 * np.sin(2 * np.pi * t * 1.3)))
    return normalize(reverb(stereo(crack * 0.5 + roll * 2.5, width=1), 4.0, 0.5))


def fire(dur=8.0):
    t = _t(dur)
    bed = _lp(_noise(len(t)), 700) * 0.4
    cr = np.zeros(len(t))
    idx = RNG.integers(0, len(t), int(dur * 35))
    cr[idx] = RNG.uniform(0.2, 1, len(idx))
    cr = _bp(signal.lfilter([1], [1, -0.6], cr), 1500, 8000)
    return normalize(stereo(bed + cr * 1.5, width=1), 0.6)


def clock_tick(dur=6.0, bpm=60):
    t = _t(dur)
    out = np.zeros(len(t))
    tk = _t(0.04)
    click = _bp(_noise(len(tk)), 2000, 6000) * np.exp(-tk / 0.006)
    k = 0
    while k * 60 / bpm < dur:
        s = int(k * 60 / bpm * SR)
        e = min(len(out), s + len(click))
        out[s:e] += click[: e - s] * (1 if k % 2 else 0.75)
        k += 1
    return normalize(reverb(stereo(out), 0.6, 0.15))


def shimmer(dur=4.0, note="A"):
    """لمعة/جرس (للعناوين والكشف)."""
    t = _t(dur)
    f = _note(note) * 4
    x = sum(np.sin(2 * np.pi * f * m * t) / m * np.exp(-t / (1.5 / m)) for m in (1, 2.01, 3.03, 4.2))
    return normalize(reverb(stereo(x * _env(len(t), 0.005, 1.2), width=1), 3.0, 0.6), 0.7)


def footsteps(dur=4.0, bpm=110):
    t = _t(dur)
    out = np.zeros(len(t))
    st = _t(0.15)
    step = _lp(_noise(len(st)), 900) * np.exp(-st / 0.03)
    k = 0
    while k * 60 / bpm < dur:
        s = int(k * 60 / bpm * SR)
        e = min(len(out), s + len(step))
        out[s:e] += step[: e - s] * (0.7 + 0.3 * RNG.random())
        k += 1
    return normalize(reverb(stereo(out), 0.8, 0.2), 0.7)


def crowd(dur=8.0):
    """همهمة جمع بعيدة."""
    t = _t(dur)
    x = np.zeros(len(t))
    for i in range(18):
        f = RNG.uniform(140, 320)
        am = np.clip(np.sin(2 * np.pi * t * RNG.uniform(2, 5) + RNG.uniform(0, 6)), 0, 1)
        x += _bp(_noise(len(t), 100 + i), f, f * 4) * am
    fade = np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)
    return normalize(reverb(stereo(x * fade, width=1), 2.0, 0.5), 0.5)


def glitch(dur=0.6):
    t = _t(dur)
    x = np.sign(np.sin(2 * np.pi * RNG.choice([200, 400, 800, 1600], len(t) // 800 + 1).repeat(800)[: len(t)] * t))
    x *= (RNG.random(len(t) // 600 + 1) > 0.4).repeat(600)[: len(t)]
    return normalize(stereo(x * 0.5 * _env(len(t), 0.002, dur)), 0.6)


LIBRARY = {
    "boom": (boom, "ضربة سينمائية ضخمة"),
    "impact": (impact, "ضربة قصيرة حادة"),
    "sub_drop": (sub_drop, "هبوط عميق (باس)"),
    "riser": (riser, "تصاعد توتر"),
    "reverse_swell": (reverse_swell, "شفط معكوس قبل القطع"),
    "whoosh": (whoosh, "مرور سريع / انتقال"),
    "braam": (braam, "نفخة نحاسية عملاقة"),
    "drone": (drone, "طبقة توتر مستمرة"),
    "pad": (pad, "موسيقى وترية حزينة/ملحمية"),
    "taiko": (taiko, "طبول ملحمية"),
    "heartbeat": (heartbeat, "نبض قلب"),
    "wind": (wind, "رياح"),
    "rain": (rain, "مطر"),
    "thunder": (thunder, "رعد"),
    "fire": (fire, "طقطقة نار"),
    "clock_tick": (clock_tick, "تكتكة ساعة"),
    "shimmer": (shimmer, "لمعة / جرس كشف"),
    "footsteps": (footsteps, "خطوات"),
    "crowd": (crowd, "همهمة جمع"),
    "glitch": (glitch, "تشويش رقمي"),
}


# ---------------------------------------------------------------- أصوات بشرية هادئة (Foley)
def _clicks(dur, times, make_one):
    t = _t(dur)
    out = np.zeros(len(t))
    for tt in times:
        one = make_one()
        s = int(tt * SR)
        e = min(len(out), s + len(one))
        if s < len(out):
            out[s:e] += one[: e - s]
    return out


def steps_soft(dur=4.0, pace=1.9, surface="stone"):
    """مشي طبيعي هادئ (كعب ثم مقدمة القدم) — surface: stone/grass/wood."""
    per = 1 / pace
    times = []
    k = 0.15
    while k < dur:
        times.append(k + RNG.normal(0, 0.012))
        k += per * RNG.uniform(0.96, 1.04)
    cut = {"stone": (300, 5000), "grass": (800, 7000), "wood": (150, 2500)}[surface]

    def one():
        tt = _t(0.22)
        heel = _bp(_noise(len(tt)), *cut) * np.exp(-tt / 0.018)
        toe = np.roll(_bp(_noise(len(tt)), cut[0] * 1.5, cut[1]) * np.exp(-tt / 0.03) * 0.5, int(0.07 * SR))
        if surface == "grass":
            heel = heel * 0.5 + _hp(_noise(len(tt)), 2500) * np.exp(-tt / 0.06) * 0.4
        return (heel + toe) * RNG.uniform(0.7, 1.0)
    x = _clicks(dur, times, one)
    return normalize(reverb(stereo(x), 0.5, 0.12), 0.5)


def run_steps(dur=3.0):
    return steps_soft(dur, pace=3.0)


def cloth(dur=0.8):
    """حفيف قماش (حركة يد على اللبس/الجاكيت)."""
    t = _t(dur)
    env = np.sin(np.pi * t / dur) ** 2 * (0.7 + 0.3 * np.sin(2 * np.pi * t * 9))
    x = _bp(_noise(len(t)), 1200, 7000) * env
    return normalize(stereo(x, width=0.5), 0.35)


def bite(dur=0.5):
    """قضمة مقرمشة خفيفة."""
    t = _t(dur)
    x = np.zeros(len(t))
    for i in range(int(RNG.integers(4, 8))):
        s = int(RNG.uniform(0, 0.15) * SR)
        g = _t(0.03)
        c = _bp(_noise(len(g)), 1500, 9000) * np.exp(-g / 0.006)
        x[s:s + len(c)] += c[: len(x) - s] * RNG.uniform(0.4, 1)
    return normalize(stereo(x), 0.4)


def chew(dur=2.0, rate=1.6):
    """مضغ هادئ."""
    times = np.arange(0.1, dur, 1 / rate)

    def one():
        tt = _t(0.25)
        return _bp(_noise(len(tt)), 300, 2500) * np.exp(-tt / 0.07) * np.sin(np.pi * np.clip(tt / 0.25, 0, 1))
    return normalize(stereo(_clicks(dur, times, one)), 0.3)


def sip(dur=0.9):
    t = _t(dur)
    x = _sweep_filter(_noise(len(t)), 900, 2200, q=3) * np.sin(np.pi * t / dur) ** 2
    return normalize(stereo(x), 0.3)


def breath(dur=1.6, heavy=False):
    t = _t(dur)
    inh = np.sin(np.pi * np.clip(t / (dur * 0.45), 0, 1)) ** 2 * (t < dur * 0.45)
    exh = np.sin(np.pi * np.clip((t - dur * 0.5) / (dur * 0.5), 0, 1)) ** 2 * (t >= dur * 0.5)
    x = _bp(_noise(len(t)), 500, 3500) * (inh * 0.6 + exh)
    return normalize(stereo(x), 0.45 if heavy else 0.25)


def bag(dur=0.6):
    """خشخشة حقيبة/حزام."""
    t = _t(dur)
    x = _bp(_noise(len(t)), 2000, 8000) * (RNG.random(len(t)) > 0.97) * 3
    x = signal.lfilter([1], [1, -0.7], x) * np.sin(np.pi * t / dur)
    return normalize(stereo(x), 0.3)


def park(dur=12.0):
    """جو حديقة: عصافير بعيدة + نسيم + همهمة خفيفة."""
    t = _t(dur)
    air = _lp(_noise(len(t)), 600) * 0.15
    birds = np.zeros(len(t))
    for _ in range(int(dur * 0.9)):
        s = RNG.uniform(0, dur - 0.5)
        tt = _t(RNG.uniform(0.08, 0.2))
        f0 = RNG.uniform(2800, 5200)
        ch = np.sin(2 * np.pi * np.cumsum(f0 + 900 * np.sin(2 * np.pi * tt * RNG.uniform(15, 40))) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2
        for rep in range(int(RNG.integers(1, 4))):
            i = int((s + rep * 0.15) * SR)
            e = min(len(birds), i + len(ch))
            birds[i:e] += ch[: e - i] * RNG.uniform(0.05, 0.15)
    fade = np.clip(t / 1.5, 0, 1) * np.clip((dur - t) / 1.5, 0, 1)
    x = reverb(stereo((air + birds) * fade, width=1), 1.5, 0.35)
    return normalize(x, 0.35)


LIBRARY.update({
    "steps_soft": (steps_soft, "مشي هادئ طبيعي (حجر/عشب/خشب)"),
    "run_steps": (run_steps, "جري"),
    "cloth": (cloth, "حفيف القماش / حركة اليد على اللبس"),
    "bite": (bite, "قضمة"),
    "chew": (chew, "مضغ"),
    "sip": (sip, "رشفة شرب"),
    "breath": (breath, "تنفس"),
    "bag": (bag, "خشخشة حقيبة"),
    "park": (park, "جو حديقة وعصافير"),
})


def make(name, **kw):
    fn = LIBRARY[name][0]
    return fn(**kw)
