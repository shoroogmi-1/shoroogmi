"""أصوات الذكاء الاصطناعي العربية (تعمل بدون إنترنت بعد أول تنزيل).

  man      رجل  — صوت "كريم" (piper ar_JO-kareem-medium) — الصوت المعتمد للراوي
  deep     راوٍ عميق — كريم بطبقة أخفض وإيقاع أبطأ (للتريلرات والوثائقي الثقيل)
  woman    امرأة — مشتق من كريم بإزاحة الطبقة + الرنين (formant)
  child    طفل  — مشتق من كريم بإزاحة أعلى
  elder    شيخ كبير — أخفض وأبطأ مع اهتزاز خفيف

ملاحظة صادقة: لا يوجد حاليًا نموذج عربي مفتوح بصوت امرأة أو طفل أصلي، لذلك المرأة والطفل مشتقان
من صوت كريم؛ جودتهما مقبولة لكنها أقل طبيعية من صوت الرجل.
النص يجب أن يكون مشكولًا بالكامل لنطق صحيح.
"""
import os
import subprocess
import tarfile
import hashlib

HOME = os.path.expanduser("~/.cache/cinema-voices")
ENGINE_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.12.15/sherpa-onnx-v1.12.15-linux-x64-static.tar.bz2"
MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-ar_JO-kareem-medium.tar.bz2"
BIN = os.path.join(HOME, "sherpa-onnx-v1.12.15-linux-x64-static", "bin", "sherpa-onnx-offline-tts")
MODEL = os.path.join(HOME, "vits-piper-ar_JO-kareem-medium")

# formant = إزاحة الرنين، pitch = الطبقة الكلية النهائية، speed = سرعة الكلام
VOICES = {
    "man": dict(label="رجل (كريم)", formant=1.0, pitch=1.0, speed=0.95),
    "deep": dict(label="راوٍ عميق", formant=0.94, pitch=0.9, speed=1.05, fx="aecho=0.8:0.6:40:0.15"),
    "woman": dict(label="امرأة", formant=1.17, pitch=1.59, speed=0.95),
    "child": dict(label="طفل", formant=1.32, pitch=2.14, speed=0.92),
    "elder": dict(label="شيخ كبير", formant=0.96, pitch=0.92, speed=1.12, fx="vibrato=f=5:d=0.08"),
}


def _fetch(url, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    arc = os.path.join(dest_dir, os.path.basename(url))
    if not os.path.exists(arc):
        print("تنزيل:", url)
        subprocess.run(["curl", "-sSL", "--fail", "-o", arc, url], check=True)
    with tarfile.open(arc) as tf:
        tf.extractall(dest_dir)


def ensure():
    if not os.path.exists(BIN):
        _fetch(ENGINE_URL, HOME)
    if not os.path.exists(os.path.join(MODEL, "tokens.txt")):
        _fetch(MODEL_URL, HOME)


def say(text, out_wav, voice="man", cache=True):
    """يحوّل نصًا مشكولًا إلى ملف صوت wav (48kHz ستيريو)."""
    v = VOICES[voice]
    if cache:
        key = hashlib.md5((voice + "|" + text).encode()).hexdigest()[:12]
        cdir = os.path.join(HOME, "said")
        os.makedirs(cdir, exist_ok=True)
        cached = os.path.join(cdir, key + ".wav")
        if os.path.exists(cached):
            subprocess.run(["cp", cached, out_wav], check=True)
            return out_wav
    ensure()
    raw = out_wav + ".raw.wav"
    subprocess.run([BIN, f"--vits-model={MODEL}/ar_JO-kareem-medium.onnx", f"--vits-tokens={MODEL}/tokens.txt",
                    f"--vits-data-dir={MODEL}/espeak-ng-data", f"--vits-length-scale={v['speed']}",
                    f"--output-filename={raw}", text], check=True, capture_output=True)
    fr, pt = v["formant"], v["pitch"]
    chain = []
    if fr != 1.0 or pt != 1.0:
        chain += [f"asetrate=22050*{fr}", "aresample=22050", f"atempo={1 / fr:.4f}"]
        if pt / fr != 1.0:
            chain += [f"rubberband=pitch={pt / fr:.4f}:formant=preserved:pitchq=quality"]
    if v.get("fx"):
        chain.append(v["fx"])
    chain += ["highpass=f=70", "acompressor=threshold=-20dB:ratio=3:attack=5:release=80", "loudnorm=I=-16:TP=-1.5"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", ",".join(chain), "-ar", "48000", "-ac", "2", out_wav], check=True)
    os.remove(raw)
    if cache:
        subprocess.run(["cp", out_wav, cached], check=True)
    return out_wav
