"""تسجيل المقالات العربية بصوت «حامد» (Microsoft Neural) إلى assets/audio/<slug>.mp3.

يُشغَّل من GitHub Actions (ملف .github/workflows/generate-site.yml). يسجّل فقط المقالات التي لا تسجيل لها،
أو التي تغيّر نصها منذ آخر تسجيل (البصمة محفوظة في assets/audio/manifest.json).
مثال: python3 tools/make_audio.py --only al-faris-al-qawwal
"""
import argparse
import asyncio
import glob
import hashlib
import json
import os
import re
import sys
import time

import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
MANIFEST = os.path.join(OUT, "manifest.json")
VOICE = "ar-SA-HamedNeural"
# سطر وسائط: ![وصف](ملف) أو [وصف](ملف.pdf) أو رابط يوتيوب وحده
MEDIA_LINE = re.compile(r"!\[[^\]]*\]\([^)\s]+\)|\[[^\]]*\]\([^)\s:]+\.\w+\)|\[[^\]]*\]\(https?://\S*(?:youtube\.com|youtu\.be)\S*\)|https?://\S*(?:youtube\.com|youtu\.be)/\S+")


def article_text(path):
    """العنوان ثم فقرات المقال كما تُقرأ، بلا علامات التنسيق."""
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    head, _, body = text.strip().partition("\n\n")
    title = re.search(r"^العنوان:\s*(.*)$", head, re.M).group(1).strip()
    blocks = []
    for para in re.split(r"\n\s*\n", body.strip()):
        lines = [line.strip() for line in para.splitlines() if line.strip()]
        if lines and all(MEDIA_LINE.fullmatch(line) for line in lines):
            continue  # فقرة صور أو فيديو أو ملفات أو روابط يوتيوب لا تُقرأ
        para = " ".join(lines)
        para = re.sub(r"^(## |> )", "", para)
        para = re.sub(r"<[^>]+>", "", para)  # روابط HTML داخل الفقرات
        if para:
            blocks.append(para)
    return title + ".\n\n" + "\n\n".join(blocks)


async def record(text, dest):
    await edge_tts.Communicate(text, VOICE).save(dest)


def record_with_retry(text, dest, tries=3):
    """يحاول التسجيل حتى ٣ مرات؛ خدمة الصوت ترفض أحيانًا الطلب مؤقتًا."""
    for i in range(tries):
        tmp = dest + ".part"  # التسجيل القديم يبقى كما هو حتى ينجح الجديد
        try:
            asyncio.run(record(text, tmp))
            os.replace(tmp, dest)
            return True
        except Exception as e:  # noqa: BLE001 — أي خطأ شبكة أو رفض من الخدمة
            print(f"  محاولة {i + 1} لم تنجح: {type(e).__name__}: {str(e)[:200]}", flush=True)
            if os.path.exists(tmp):
                os.remove(tmp)
            time.sleep(5 * (i + 1))
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="أسماء مقالات بعينها")
    ap.add_argument("--max", type=int, default=0, help="أقصى عدد يُسجَّل في هذه الدفعة (0 = الكل)")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    done, failed = 0, []
    for path in sorted(glob.glob(os.path.join(ROOT, "content", "articles", "*.md"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        if args.only and slug not in args.only:
            continue
        text = article_text(path)
        digest = hashlib.sha256((VOICE + text).encode("utf-8")).hexdigest()[:16]
        dest = os.path.join(OUT, f"{slug}.mp3")
        if manifest.get(slug) == digest and os.path.exists(dest):
            continue
        print("تسجيل:", slug, flush=True)
        if not record_with_retry(text, dest):
            failed.append(slug)
            continue
        manifest[slug] = digest
        json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
        done += 1
        if args.max and done >= args.max:
            break
    print("سُجِّل:", done)
    if failed:
        print("تعذّر تسجيل:", " ".join(failed), "— يُعاد في التشغيل القادم")
        # يفشل فقط إن لم يُسجَّل شيء، حتى تُحفظ التسجيلات الناجحة في هذه الدفعة
        if not done:
            sys.exit(1)


if __name__ == "__main__":
    main()
