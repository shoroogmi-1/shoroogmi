"""تسجيل المقالات العربية بصوت «حامد» (Microsoft Neural) إلى assets/audio/<slug>.mp3.

يُشغَّل من GitHub Actions (ملف .github/workflows/audio.yml). يسجّل فقط المقالات التي لا تسجيل لها،
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

import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
MANIFEST = os.path.join(OUT, "manifest.json")
VOICE = "ar-SA-HamedNeural"


def article_text(path):
    """العنوان ثم فقرات المقال كما تُقرأ، بلا علامات التنسيق."""
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    head, _, body = text.strip().partition("\n\n")
    title = re.search(r"^العنوان:\s*(.*)$", head, re.M).group(1).strip()
    blocks = []
    for para in re.split(r"\n\s*\n", body.strip()):
        para = " ".join(line.strip() for line in para.splitlines())
        para = re.sub(r"^(## |> )", "", para)
        para = re.sub(r"<[^>]+>", "", para)  # روابط HTML داخل الفقرات
        if para:
            blocks.append(para)
    return title + ".\n\n" + "\n\n".join(blocks)


async def record(text, dest):
    await edge_tts.Communicate(text, VOICE).save(dest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="أسماء مقالات بعينها")
    ap.add_argument("--max", type=int, default=0, help="أقصى عدد يُسجَّل في هذه الدفعة (0 = الكل)")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {}
    done = 0
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
        asyncio.run(record(text, dest))
        manifest[slug] = digest
        json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
        done += 1
        if args.max and done >= args.max:
            break
    print("سُجِّل:", done)


if __name__ == "__main__":
    main()
