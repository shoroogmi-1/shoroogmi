// Theme toggle (remembers the choice)
const root = document.documentElement;
const EN = root.lang === "en";
const tr = (ar, en) => (EN ? en : ar);
const themeBtn = document.querySelector(".theme-toggle");

function currentTheme() {
  return root.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}
function updateThemeIcon() {
  themeBtn.textContent = currentTheme() === "dark" ? "☀️" : "🌙";
}
updateThemeIcon();
themeBtn.addEventListener("click", () => {
  const next = currentTheme() === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch (e) {}
  updateThemeIcon();
});

// Mobile menu
const menuBtn = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");
menuBtn.addEventListener("click", () => {
  const open = navLinks.classList.toggle("open");
  menuBtn.setAttribute("aria-expanded", open);
});

// Filters (tags on articles, reading status on books) + optional search
const grid = document.querySelector("[data-filterable]");
if (grid) {
  const items = grid.querySelectorAll("[data-tag]");
  const buttons = document.querySelectorAll(".filter");
  const search = document.querySelector(".search");
  const empty = document.querySelector(".empty");
  let tag = "all";

  function apply() {
    const q = search ? search.value.trim() : "";
    let shown = 0;
    items.forEach((el) => {
      const match = (tag === "all" || el.dataset.tag.split("|").includes(tag)) && (!q || el.textContent.includes(q));
      el.classList.toggle("hidden", !match);
      if (match) shown++;
    });
    if (empty) empty.hidden = shown > 0;
  }

  buttons.forEach((btn) =>
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      tag = btn.dataset.filter;
      apply();
    })
  );
  if (search) search.addEventListener("input", apply);
}

// Reveal on scroll
const revealEls = document.querySelectorAll(
  ".section-title, .tile, .post-card, .note-card, .book, .blog-door, .quote, .stop-card, .hud, .contact"
);
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) =>
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }),
    { threshold: 0.12 }
  );
  revealEls.forEach((el) => {
    el.classList.add("reveal");
    observer.observe(el);
  });
}

// Passport map: draw the route between stations and fly the plane along it while scrolling
const map = document.querySelector(".map");
if (map) {
  const svg = map.querySelector(".route");
  const line = map.querySelector(".route-line");
  const done = map.querySelector(".route-done");
  const plane = map.querySelector(".plane");
  const list = map.querySelector(".stations");
  let length = 0;

  function centerOf(node) {
    return {
      x: list.offsetLeft + node.offsetLeft + node.offsetWidth / 2,
      y: list.offsetTop + node.offsetTop + node.offsetHeight / 2,
    };
  }

  function drawRoute() {
    const pts = [...map.querySelectorAll(".node")].map(centerOf);
    if (!pts.length) return;
    const end = map.querySelector(".map-end");
    pts.unshift({ x: pts[0].x, y: 0 });
    pts.push({ x: map.clientWidth / 2, y: end.offsetTop });
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], k = (b.y - a.y) / 2;
      d += ` C ${a.x} ${a.y + k}, ${b.x} ${b.y - k}, ${b.x} ${b.y}`;
    }
    svg.setAttribute("viewBox", `0 0 ${map.clientWidth} ${map.clientHeight}`);
    line.setAttribute("d", d);
    done.setAttribute("d", d);
    length = done.getTotalLength();
    done.style.strokeDasharray = length;
    flyPlane();
  }

  function flyPlane() {
    if (!length) return;
    const rect = map.getBoundingClientRect();
    const progress = Math.min(1, Math.max(0, (innerHeight * 0.55 - rect.top) / rect.height));
    const at = progress * length;
    const p = done.getPointAtLength(at);
    const q = done.getPointAtLength(Math.min(length, at + 2));
    const angle = progress >= 1 ? 90 : (Math.atan2(q.y - p.y, q.x - p.x) * 180) / Math.PI;
    // the ✈️ emoji points up-right (-45°), so turn it to follow the route
    plane.style.transform =
      `translate(${p.x - plane.offsetWidth / 2}px, ${p.y - plane.offsetHeight / 2}px) rotate(${angle + 45}deg)`;
    done.style.strokeDashoffset = length - at;
  }

  // a small burst of stars when a station is pressed
  map.querySelectorAll(".node").forEach((node) =>
    node.addEventListener("click", () => {
      const c = centerOf(node);
      ["⭐", "✨", "🎉", "⭐", "✨", "💫", "🎈", "⭐"].forEach((e, i) => {
        const s = document.createElement("span");
        s.className = "burst";
        s.textContent = e;
        const a = (i / 8) * 2 * Math.PI;
        s.style.left = `${c.x}px`;
        s.style.top = `${c.y}px`;
        s.style.setProperty("--dx", `${Math.cos(a) * 80}px`);
        s.style.setProperty("--dy", `${Math.sin(a) * 80}px`);
        s.addEventListener("animationend", () => s.remove());
        map.appendChild(s);
      });
    })
  );

  drawRoute();
  addEventListener("resize", drawRoute);
  addEventListener("scroll", flyPlane, { passive: true });
  if (document.fonts) document.fonts.ready.then(drawRoute);
}

// Counters (visitors, reads, likes) are stored in the free Abacus counter service
const COUNTER_API = "https://abacus.jasoncameron.dev";
const COUNTER_NS = "shoroogmi";
const arNum = new Intl.NumberFormat(EN ? "en-US" : "ar-EG");

async function counter(action, key) {
  try {
    const res = await fetch(`${COUNTER_API}/${action}/${COUNTER_NS}/${key}`);
    if (res.status === 404) return 0;
    if (!res.ok) return null;
    return (await res.json()).value ?? 0;
  } catch (e) {
    return null;
  }
}

function showCount(selector, value) {
  document.querySelectorAll(selector).forEach((el) => (el.textContent = value === null ? "—" : arNum.format(value)));
}

function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
    return value;
  } catch (e) {
    return null;
  }
}

// Visitors: a browser counts once as a visitor, and once more as a returning reader
// the first time it comes back on a later day.
async function trackVisit() {
  const today = new Date().toISOString().slice(0, 10);
  let canStore = false;
  try { localStorage.setItem("sm-test", "1"); canStore = true; } catch (e) {}
  if (!canStore) return {};
  const first = store("sm-first-visit");
  if (!first) {
    store("sm-first-visit", today);
    return { visitors: await counter("hit", "site-visitors") };
  }
  if (first !== today && !store("sm-returning")) {
    store("sm-returning", "1");
    return { returning: await counter("hit", "site-returning") };
  }
  return {};
}

trackVisit().then(async (fresh) => {
  if (!document.querySelector("[data-stat]")) return;
  const visitors = fresh.visitors ?? (await counter("get", "site-visitors"));
  const returning = fresh.returning ?? (await counter("get", "site-returning"));
  showCount('[data-stat="visitors"]', visitors);
  showCount('[data-stat="returning"]', returning);
});

// Article: completed reads and likes
const post = document.querySelector("#post[data-slug]");
if (post) {
  const slug = post.dataset.slug;
  const readKey = `reads-${slug}`;
  const likeKey = `likes-${slug}`;
  const likeBtn = post.querySelector(".like-btn");

  counter("get", readKey).then((v) => showCount(".read-count", v));
  counter("get", likeKey).then((v) => showCount(".like-count", v));

  // A read counts once per browser, when the reader reaches the end of the article
  // after spending at least 40% of its reading time (and never less than 15 seconds).
  const started = Date.now();
  const minMs = Math.max(15000, Number(post.dataset.minutes) * 60000 * 0.4);
  let endSeen = false;
  let timer = null;
  function tryCountRead() {
    if (!endSeen || store(`sm-read-${slug}`)) return;
    const wait = minMs - (Date.now() - started);
    if (wait > 0) {
      clearTimeout(timer);
      timer = setTimeout(tryCountRead, wait);
      return;
    }
    store(`sm-read-${slug}`, "1");
    counter("hit", readKey).then((v) => v !== null && showCount(".read-count", v));
  }
  if ("IntersectionObserver" in window) {
    const end = post.querySelector(".signature");
    new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        endSeen = true;
        tryCountRead();
      }
    }).observe(end);
  }

  // Likes: one per browser, no sign-in needed
  function markLiked() {
    likeBtn.classList.add("liked");
    likeBtn.setAttribute("aria-pressed", "true");
    likeBtn.querySelector(".heart").textContent = "❤️";
  }
  if (store(`sm-liked-${slug}`)) markLiked();
  likeBtn.addEventListener("click", async () => {
    likeBtn.classList.remove("pop");
    void likeBtn.offsetWidth;
    likeBtn.classList.add("pop");
    if (store(`sm-liked-${slug}`)) return;
    markLiked();
    store(`sm-liked-${slug}`, "1");
    const v = await counter("hit", likeKey);
    if (v !== null) showCount(".like-count", v);
  });
}

// Recorded audio (Hamed's voice): speed button cycles the playback rate
const audioBox = document.querySelector(".audio-player");
if (audioBox) {
  const audio = audioBox.querySelector("audio");
  const rateBtn = audioBox.querySelector(".audio-rate");
  const rates = [1, 1.25, 1.5, 0.8];
  let ri = 0;
  rateBtn.addEventListener("click", () => {
    ri = (ri + 1) % rates.length;
    audio.defaultPlaybackRate = audio.playbackRate = rates[ri];
    rateBtn.textContent = `السرعة ${arNum.format(rates[ri])}×`;
  });
  audio.addEventListener("play", () => { audio.playbackRate = rates[ri]; });
}

// Listen: read the article aloud with the browser's built-in voice for the page's language
const listen = document.querySelector(".listen");
if (listen && "speechSynthesis" in window) {
  const synth = window.speechSynthesis;
  const playBtn = listen.querySelector(".listen-btn");
  const label = listen.querySelector(".listen-label");
  const icon = listen.querySelector(".listen-icon");
  const stopBtn = listen.querySelector(".listen-stop");
  const rateBtn = listen.querySelector(".listen-rate");
  const status = listen.querySelector(".listen-status");
  const rates = [1, 1.25, 1.5, 0.8];
  let rateIndex = 0;
  let queue = [];
  let index = 0;
  let state = "idle"; // idle | playing | paused

  synth.cancel(); // stop anything left over from a previous page
  listen.hidden = false;

  // iPhone/iPad list "enhanced" voices that may not be downloaded; choosing one gives silence,
  // so on Apple devices we only set the language and let the system pick its installed voice.
  const isApple = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  let useVoice = !isApple;
  let current = null; // keep the utterance referenced so the browser doesn't drop it mid-speech
  // iPhone mutes browser speech when the ring switch is on silent. Playing a silent looping clip
  // while reading puts the page in "media playback" mode, which the silent switch doesn't mute.
  const keepAwake = new Audio("data:audio/wav;base64,UklGRmQGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YUAGAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA");
  keepAwake.loop = true;
  keepAwake.setAttribute("playsinline", "");
  function mediaOn() { keepAwake.play().catch(() => {}); }
  function mediaOff() { keepAwake.pause(); }

  function pageVoice() {
    const voices = synth.getVoices().filter((v) => !/enhanced|premium|siri/i.test(v.name));
    const [best, any] = EN ? [/^en[-_]US/i, /^en/i] : [/^ar[-_]SA/i, /^ar/i];
    return voices.find((v) => best.test(v.lang) && v.localService) || voices.find((v) => best.test(v.lang)) ||
      voices.find((v) => any.test(v.lang) && v.localService) || voices.find((v) => any.test(v.lang)) || null;
  }

  // Short sentences keep long paragraphs from being cut off in some browsers
  function buildQueue() {
    const blocks = [document.querySelector(".article-hero h1"),
      ...listen.parentElement.querySelectorAll(":scope > .excerpt, :scope > p:not(.signature), :scope > h2, :scope > blockquote p")];
    const items = [];
    blocks.filter(Boolean).forEach((el) => {
      el.textContent.split(/(?<=[.!؟?؛])\s+/).map((t) => t.trim()).filter(Boolean)
        .forEach((text) => items.push({ el, text }));
    });
    return items;
  }

  function clearHighlight() {
    document.querySelectorAll(".speaking").forEach((el) => el.classList.remove("speaking"));
  }

  function setUi() {
    icon.textContent = state === "playing" ? "⏸" : "🎧";
    label.textContent = state === "playing" ? tr("إيقاف مؤقت", "Pause") : state === "paused" ? tr("متابعة الاستماع", "Resume") : tr("استمع للمقال", "Listen to the article");
    stopBtn.hidden = rateBtn.hidden = state === "idle";
    playBtn.classList.toggle("active", state !== "idle");
  }

  function speakNext() {
    if (state !== "playing") return;
    if (index >= queue.length) return stop();
    const { el, text } = queue[index];
    clearHighlight();
    el.classList.add("speaking");
    const u = new SpeechSynthesisUtterance(text);
    current = u;
    u.lang = EN ? "en-US" : "ar-SA";
    const voice = useVoice ? pageVoice() : null;
    if (voice) u.voice = voice;
    u.rate = rates[rateIndex];
    u.onstart = () => { if (u !== current) return; started = true; clearTimeout(watchdog); };
    u.onend = () => { if (u === current && state === "playing") { index++; speakNext(); } };
    u.onerror = (e) => {
      if (u !== current || e.error === "interrupted" || e.error === "canceled") return;
      stop();
      status.textContent = tr("تعذّرت القراءة الصوتية على هذا الجهاز.", "Read-aloud isn't available on this device.");
    };
    synth.resume(); // Chrome can be left paused, which silently swallows speech
    synth.speak(u);
  }

  // Some phones accept the request but never speak (silent switch on, or no voice for the
  // language installed); after a few seconds without a sound, tell the reader why.
  let started = false;
  let watchdog = null;
  function watchStart() {
    clearTimeout(watchdog);
    if (started) return;
    watchdog = setTimeout(() => {
      if (started || state !== "playing") return;
      // First try again with the system's default voice for the language before giving up
      if (useVoice) {
        useVoice = false;
        synth.cancel();
        speakNext();
        watchStart();
        return;
      }
      stop();
      status.textContent = tr(
        "لم يصدر صوت. تأكد أن الجوال ليس على الوضع الصامت، وأن فيه صوتًا عربيًا (في الآيفون: الإعدادات ← تسهيلات الاستخدام ← المحتوى المنطوق ← الأصوات ← العربية).",
        "No sound came out. Check that your phone isn't on silent and has an English voice installed (on iPhone: Settings → Accessibility → Spoken Content → Voices)."
      );
    }, 3500);
  }

  function stop() {
    state = "idle";
    mediaOff();
    synth.cancel();
    clearHighlight();
    index = 0;
    setUi();
  }

  playBtn.addEventListener("click", () => {
    if (state === "playing") {
      state = "paused";
      mediaOff();
      synth.cancel(); // pause by stopping, then resume from the same sentence
    } else {
      if (state === "idle") {
        queue = buildQueue();
        index = 0;
        started = false;
        status.textContent = pageVoice() || !synth.getVoices().length ? "" : tr("قد لا يحتوي جهازك على صوت عربي.", "Your device may not have an English voice.");
      }
      state = "playing";
      mediaOn();
      speakNext();
      watchStart();
    }
    setUi();
  });
  stopBtn.addEventListener("click", stop);
  rateBtn.addEventListener("click", () => {
    rateIndex = (rateIndex + 1) % rates.length;
    rateBtn.textContent = `${tr("السرعة", "Speed")} ${arNum.format(rates[rateIndex])}×`;
    if (state === "playing") { synth.cancel(); speakNext(); }
  });
  addEventListener("pagehide", () => synth.cancel());
}

// Comments: stored in Supabase. The section stays hidden until both values are filled in.
const COMMENTS_URL = "https://fownwnktsvpzfyyndgtt.supabase.co";
const COMMENTS_KEY = "sb_publishable_xfQjqLqa091AzMM30SRp6g_llc9fjPx"; // public key, safe to publish
const commentsBox = document.querySelector(".comments");
if (commentsBox && post && COMMENTS_URL && COMMENTS_KEY) {
  const slug = post.dataset.slug;
  const api = `${COMMENTS_URL}/rest/v1/comments`;
  const headers = { apikey: COMMENTS_KEY, Authorization: `Bearer ${COMMENTS_KEY}`, "Content-Type": "application/json" };
  const list = commentsBox.querySelector(".comment-list");
  const empty = commentsBox.querySelector(".no-comments");
  const cForm = commentsBox.querySelector(".comment-form");
  const cStatus = commentsBox.querySelector(".comment-status");
  const when = new Intl.DateTimeFormat(EN ? "en-US" : "ar-EG", { day: "numeric", month: "long", year: "numeric", hour: "numeric", minute: "2-digit" });

  function addComment(c) {
    const li = document.createElement("li");
    const head = document.createElement("p");
    const name = document.createElement("b");
    name.textContent = c.name;
    const time = document.createElement("time");
    time.dateTime = c.created_at;
    time.textContent = when.format(new Date(c.created_at));
    head.append(name, " · ", time);
    const body = document.createElement("p");
    body.textContent = c.body;
    li.append(head, body);
    list.appendChild(li);
    empty.hidden = true;
  }

  commentsBox.hidden = false;
  fetch(`${api}?slug=eq.${encodeURIComponent(slug)}&select=name,body,created_at&order=created_at.asc`, { headers })
    .then((r) => (r.ok ? r.json() : Promise.reject()))
    .then((rows) => { rows.forEach(addComment); empty.hidden = rows.length > 0; })
    .catch(() => { empty.hidden = false; empty.textContent = tr("تعذّر تحميل التعليقات الآن.", "Comments couldn't be loaded right now."); });

  cForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(cForm);
    const name = data.get("name").trim();
    const body = data.get("body").trim();
    cStatus.className = "comment-status";
    if (data.get("website")) return; // a bot filled the hidden field
    if (!name || !body) {
      cStatus.textContent = tr("اكتب اسمك وتعليقك.", "Write your name and comment.");
      cStatus.classList.add("error");
      return;
    }
    const last = Number(store("sm-last-comment") || 0);
    if (Date.now() - last < 30000) {
      cStatus.textContent = tr("تمهّل قليلًا قبل التعليق مرة أخرى ☕", "Take a moment before commenting again ☕");
      cStatus.classList.add("error");
      return;
    }
    const button = cForm.querySelector("button");
    button.disabled = true;
    try {
      const res = await fetch(api, {
        method: "POST",
        headers: { ...headers, Prefer: "return=representation" },
        body: JSON.stringify({ slug, name, body }),
      });
      if (!res.ok) throw new Error();
      const [saved] = await res.json();
      addComment(saved || { name, body, created_at: new Date().toISOString() });
      store("sm-last-comment", String(Date.now()));
      cForm.reset();
      cStatus.textContent = tr("وصل تعليقك إلى البرج ✈️", "Your comment reached the tower ✈️");
      cStatus.classList.add("success");
    } catch (err) {
      cStatus.textContent = tr("لم يُرسل التعليق، حاول مرة أخرى.", "Your comment wasn't sent, please try again.");
      cStatus.classList.add("error");
    } finally {
      button.disabled = false;
    }
  });
}

// Contact form: sends the message straight to the writer's inbox through FormSubmit (no email app needed)
const form = document.querySelector(".contact-form");
if (form) {
  const statusEl = form.querySelector(".form-status");
  const btn = form.querySelector('button[type="submit"]');
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const name = data.get("name").trim();
    const email = (data.get("email") || "").trim();
    const topic = data.get("topic");
    const message = data.get("message").trim();

    statusEl.className = "form-status";
    if (!name || !message) {
      statusEl.textContent = tr("يرجى كتابة اسمك ورسالتك.", "Please write your name and message.");
      statusEl.classList.add("error");
      return;
    }
    if (data.get("_honey")) return;
    btn.disabled = true;
    statusEl.textContent = tr("جارٍ الإرسال…", "Sending…");
    try {
      const res = await fetch(`https://formsubmit.co/ajax/${form.dataset.email}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          _subject: `${tr("برج المراقبة", "Control Tower")}: ${topic} ${tr("من", "from")} ${name}`,
          _template: "box",
          _captcha: "false",
          name, ...(email ? { email } : {}), topic, message,
        }),
      });
      const out = await res.json().catch(() => ({}));
      if (!res.ok || out.success === false || out.success === "false") throw new Error(out.message || res.status);
      form.reset();
      statusEl.textContent = tr("وصلت رسالتك إلى البرج ✈️ شكرًا لك!", "Your message reached the Tower ✈️ Thank you!");
      statusEl.classList.add("success");
    } catch (err) {
      statusEl.textContent = tr("تعذّر الإرسال الآن، حاول مرة أخرى بعد قليل.", "Couldn't send right now. Please try again shortly.");
      statusEl.classList.add("error");
    } finally {
      btn.disabled = false;
    }
  });
}

document.querySelectorAll(".year").forEach((el) => (el.textContent = new Date().getFullYear()));
