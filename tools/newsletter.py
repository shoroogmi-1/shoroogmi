"""إرسال المقالات الجديدة إلى القائمة البريدية (يعمل من GitHub Actions بعد نشر الصفحات).

- المقال الجديد = ملف في content/articles لم يُرسل من قبل (السجل في content/newsletter-sent.json)،
  وتاريخه من يوم تفعيل الإرسال فما بعد، ولم يُطفأ فيه «أرسله للمشتركين» (notify: false).
- لا يُرسل المقال حتى تكون صفحته منشورة فعلًا على الموقع؛ وإلا يُعاد في التشغيل التالي.
- يحتاج سرّين في GitHub: GMAIL_APP_PASSWORD و NEWSLETTER_TOKEN. إن غابا لا يُرسل شيئًا.
"""
import datetime
import glob
import html
import json
import os
import re
import smtplib
import sys
import time
import urllib.error
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "content", "newsletter-sent.json")
SITE = "https://shoroogmi.com/"
SUPABASE = "https://fownwnktsvpzfyyndgtt.supabase.co"
ANON_KEY = "sb_publishable_xfQjqLqa091AzMM30SRp6g_llc9fjPx"  # المفتاح العام نفسه المستعمل في الموقع
SENDER = "shoroogmi1@gmail.com"
SENDER_NAME = "شروق المحمادي"


def article_meta(path):
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n").lstrip("﻿")
    if text.startswith("---\n"):
        _, head, body = text.split("---\n", 2)
        m = yaml.safe_load(head) or {}
    else:
        head, _, body = text.strip().partition("\n\n")
        keys = {"العنوان": "title", "التاريخ": "date", "اقتباس": "quote", "الملخص": "excerpt"}
        m = {}
        for line in head.splitlines():
            k, _, v = line.partition(":")
            if k.strip() in keys:
                m[keys[k.strip()]] = v.strip()
    first = next((p.strip() for p in re.split(r"\n\s*\n", body) if p.strip() and not p.lstrip().startswith(("!", "#", ">", "["))), "")
    return {"title": str(m.get("title", "")).strip(), "date": str(m.get("date", "")),
            "quote": str(m.get("quote") or m.get("excerpt") or first[:220]).strip(), "notify": m.get("notify", True) is not False}


def page_is_live(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url + f"?nl={int(time.time())}", method="HEAD"), timeout=20) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def recipients(token):
    req = urllib.request.Request(f"{SUPABASE}/rest/v1/rpc/newsletter_recipients", method="POST",
                                 data=json.dumps({"p_token": token}).encode(),
                                 headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def message(art, url, rcpt):
    unsub = f"{SITE}unsubscribe.html?t={rcpt['unsub_token']}"
    title, quote = html.escape(art["title"]), html.escape(art["quote"])
    body_html = f"""<!doctype html><html lang="ar" dir="rtl"><body style="margin:0;background:#f5fbfe;font-family:Tahoma,Arial,sans-serif;color:#16324f">
<div style="max-width:560px;margin:0 auto;padding:28px 18px;text-align:right">
  <p style="margin:0 0 6px;color:#a86d00;font-weight:bold">☀️ رحلة جديدة من شروق المحمادي</p>
  <h1 style="margin:0 0 14px;font-size:24px;line-height:1.6">{title}</h1>
  <blockquote style="margin:0 0 22px;padding:12px 16px;border-right:4px solid #fbc93d;background:#fff;border-radius:10px;font-size:17px;line-height:1.9">«{quote}»</blockquote>
  <p><a href="{url}" style="display:inline-block;background:#fbc93d;color:#16324f;font-weight:bold;text-decoration:none;padding:12px 26px;border-radius:999px">اقرأ المقال ←</a></p>
  <hr style="border:0;border-top:1px solid #d2eaf6;margin:28px 0 12px">
  <p style="font-size:13px;color:#4d6a85">وصلتك هذه الرسالة لأنك اشتركت في القائمة البريدية لموقع <a href="{SITE}" style="color:#a86d00">shoroogmi.com</a>.
  <br><a href="{unsub}" style="color:#4d6a85">إلغاء الاشتراك</a></p>
</div></body></html>"""
    msg = EmailMessage()
    msg["Subject"] = f"رحلة جديدة: {art['title']}"
    msg["From"] = formataddr((SENDER_NAME, SENDER))
    msg["To"] = rcpt["email"]
    msg["Message-ID"] = make_msgid(domain="shoroogmi.com")
    msg["List-Unsubscribe"] = f"<{unsub}>, <mailto:{SENDER}?subject=unsubscribe>"
    msg.set_content(f"{art['title']}\n\n«{art['quote']}»\n\nاقرأ المقال: {url}\n\nلإلغاء الاشتراك: {unsub}\n")
    msg.add_alternative(body_html, subtype="html")
    return msg


def main():
    log = json.load(open(LOG, encoding="utf-8")) if os.path.exists(LOG) else None
    slugs = sorted(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(ROOT, "content", "articles", "*.md")))
    if log is None:  # أول تشغيل: المقالات الموجودة تُعدّ مُرسلة، والإرسال للجديد فقط
        log = {"since": datetime.date.today().isoformat(), "sent": slugs}
        json.dump(log, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("بدأ سجل الإرسال؛ لا إرسال في هذه المرة")
        return
    password, token = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", ""), os.environ.get("NEWSLETTER_TOKEN", "").strip()
    todo = []
    for slug in slugs:
        if slug in log["sent"]:
            continue
        art = article_meta(os.path.join(ROOT, "content", "articles", f"{slug}.md"))
        if not art["notify"] or art["date"][:10] < log["since"]:
            log["sent"].append(slug)  # لا يُرسل أبدًا (مقال قديم أو أُطفئ إرساله)
            continue
        todo.append((slug, art))
    if todo and not (password and token):
        print("لم يُضبط GMAIL_APP_PASSWORD أو NEWSLETTER_TOKEN في GitHub؛ لم يُرسل:", " ".join(s for s, _ in todo))
        todo = []
    if todo:
        people = recipients(token)
        print("المشتركون:", len(people))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as smtp:
            smtp.login(SENDER, password)
            for slug, art in todo:
                url = f"{SITE}blog/articles/{slug}.html"
                if not page_is_live(url):
                    print("الصفحة لم تُنشر بعد، يُعاد لاحقًا:", slug)
                    continue
                sent = 0
                for r in people:
                    try:
                        smtp.send_message(message(art, url, r))
                        sent += 1
                    except smtplib.SMTPRecipientsRefused:
                        print("  رُفض:", r["email"])
                    time.sleep(0.5)
                log["sent"].append(slug)
                json.dump(log, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)  # يُحفظ فورًا حتى لا يتكرر
                print(f"أُرسل «{art['title']}» إلى {sent} مشترك")
    log["sent"] = sorted(set(log["sent"]))
    json.dump(log, open(LOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — لا يوقف الموقع؛ يُعاد في التشغيل القادم
        print("تعذّر الإرسال:", type(e).__name__, str(e)[:300])
        sys.exit(1)
