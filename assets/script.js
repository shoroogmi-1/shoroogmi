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

  const intros = document.querySelectorAll(".cat-intro");
  function choose(btn) {
    buttons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    tag = btn.dataset.filter;
    intros.forEach((el) => (el.hidden = el.dataset.for !== tag));
    apply();
  }
  buttons.forEach((btn) => btn.addEventListener("click", () => choose(btn)));
  if (search) search.addEventListener("input", apply);
  // رابط مثل articles.html#الزاوية ٣٦ يفتح الصفحة على ذلك التصنيف
  const fromHash = decodeURIComponent(location.hash.slice(1));
  const hashBtn = fromHash && [...buttons].find((b) => b.dataset.filter === fromHash);
  if (hashBtn) choose(hashBtn);
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

// Book downloads: each click on «تحميل الكتاب PDF» adds one to that book's counter
document.querySelectorAll("[data-count-of]").forEach((el) =>
  counter("get", el.dataset.countOf).then((v) => (el.textContent = v === null ? "—" : arNum.format(v))));
document.querySelectorAll(".book-dl").forEach((a) =>
  a.addEventListener("click", () =>
    counter("hit", a.dataset.count).then((v) => {
      if (v !== null) document.querySelectorAll(`[data-count-of="${a.dataset.count}"]`).forEach((el) => (el.textContent = arNum.format(v)));
    })));

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

// Home page "Rate us": star rating + quick comment. Each rating is saved in Supabase (the database only lets the
// public read positive ones: 4–5 stars with a comment) and also emailed to the writer through FormSubmit.
const RATINGS_API = `${COMMENTS_URL}/rest/v1/ratings`;
const sbHeaders = { apikey: COMMENTS_KEY, Authorization: `Bearer ${COMMENTS_KEY}`, "Content-Type": "application/json" };
const rateBox = document.querySelector(".rate-box");
if (rateBox) {
  const statusEl = rateBox.querySelector(".form-status");
  const btn = rateBox.querySelector('button[type="submit"]');
  rateBox.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = new FormData(rateBox);
    const stars = Number(data.get("stars") || 0);
    const note = (data.get("note") || "").trim();
    const name = (data.get("name") || "").trim();
    statusEl.className = "form-status";
    if (!stars) {
      statusEl.textContent = tr("اختر عدد النجوم أولًا ⭐", "Please pick a number of stars first ⭐");
      statusEl.classList.add("error");
      return;
    }
    if (data.get("_honey")) return;
    btn.disabled = true;
    statusEl.textContent = tr("جارٍ الإرسال…", "Sending…");
    const starText = "★".repeat(stars) + "☆".repeat(5 - stars) + ` (${stars}/5)`;
    const saved = fetch(RATINGS_API, {
      method: "POST",
      headers: { ...sbHeaders, Prefer: "return=minimal" },
      body: JSON.stringify({ stars, name: name || null, body: note || null, lang: EN ? "en" : "ar" }),
    }).then((r) => r.ok).catch(() => false);
    const mailed = fetch(`https://formsubmit.co/ajax/${rateBox.dataset.email}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        _subject: `${tr("تقييم الموقع", "Site rating")}: ${starText}`,
        _template: "box",
        _captcha: "false",
        rating: starText,
        name: name || "—",
        comment: note || "—",
        page: EN ? "English" : "العربية",
      }),
    }).then(async (r) => { const out = await r.json().catch(() => ({})); return r.ok && out.success !== false && out.success !== "false"; })
      .catch(() => false);
    const [ok1, ok2] = await Promise.all([saved, mailed]);
    if (ok1 || ok2) {
      rateBox.reset();
      statusEl.textContent = tr("وصل تقييمك ✈️ شكرًا لأنك سافرت معنا!", "Your rating has landed ✈️ Thank you for traveling with us!");
      statusEl.classList.add("success");
      if (ok1 && stars >= 4 && note) loadTestimonials();
    } else {
      statusEl.textContent = tr("تعذّر الإرسال الآن، حاول مرة أخرى بعد قليل.", "Couldn't send right now. Please try again shortly.");
      statusEl.classList.add("error");
    }
    btn.disabled = false;
  });
}

// "What travelers said": positive ratings only (the database returns only 4–5 stars with a comment).
// On the home page it is a strip that scrolls sideways; testimonials.html shows them all.
const testimonialList = document.querySelector(".testimonial-list");
function loadTestimonials() {
  if (!testimonialList) return;
  const limit = Number(testimonialList.dataset.limit || 12);
  const esc = (str) => str.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  fetch(`${RATINGS_API}?select=stars,name,body,created_at&order=created_at.desc&limit=${limit}`, { headers: sbHeaders })
    .then((r) => (r.ok ? r.json() : []))
    .then((rows) => {
      rows = rows.filter((r) => r.stars >= 4 && r.body);
      if (!rows.length) return; // keep the "be the first" message
      testimonialList.innerHTML = rows.map((r) => `
        <figure class="testimonial">
          <p class="t-stars" aria-label="${r.stars}/5">${"★".repeat(r.stars)}</p>
          <blockquote dir="auto">${esc(r.body)}</blockquote>
          <figcaption>— ${esc(r.name || tr("مسافر", "A traveler"))}</figcaption>
        </figure>`).join("");
    })
    .catch(() => {});
}
loadTestimonials();

// Share buttons: the phone's share sheet when available, otherwise copy the link
document.querySelectorAll(".share-btn").forEach((btn) => {
  const original = btn.innerHTML;
  const done = (msg) => {
    btn.textContent = msg;
    btn.classList.add("done");
    setTimeout(() => { btn.innerHTML = original; btn.classList.remove("done"); }, 2200);
  };
  btn.addEventListener("click", async () => {
    const { url, title } = btn.dataset;
    if (navigator.share) {
      try { await navigator.share({ title, url }); } catch (e) { /* closed by the reader */ }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      done(tr("✓ شارك الرابط", "✓ Share the link"));
    } catch (e) {
      window.prompt(tr("انسخ الرابط:", "Copy the link:"), url);
    }
  });
});

// Reader highlights & notes: select text inside an article paragraph to highlight it, add a private note,
// or share the quote. Everything stays in this browser (localStorage); nobody else sees it.
if (post) {
  const prose = post.querySelector(".prose");
  const slug = post.dataset.slug;
  const KEY = `sm-hl-${EN ? "en" : "ar"}-${slug}`;
  const blocks = () => [...prose.querySelectorAll(":scope > p:not(.signature):not(.excerpt), :scope > h2, :scope > blockquote p")];
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } };
  const save = (list) => { try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {} };
  let list = load();

  const bar = document.createElement("div");
  bar.className = "hl-bar";
  bar.hidden = true;
  document.body.appendChild(bar);

  // offset of (node, offset) inside a block's text
  function textOffset(block, node, offset) {
    const r = document.createRange();
    r.setStart(block, 0);
    r.setEnd(node, offset);
    return r.toString().length;
  }

  function wrap(block, start, end, id) {
    const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
    let pos = 0, n;
    const parts = [];
    while ((n = walker.nextNode())) {
      const len = n.data.length, a = Math.max(start - pos, 0), b = Math.min(end - pos, len);
      if (a < b) parts.push([n, a, b]);
      pos += len;
    }
    parts.forEach(([node, a, b]) => {
      const r = document.createRange();
      r.setStart(node, a);
      r.setEnd(node, b);
      const m = document.createElement("mark");
      m.className = "hl";
      m.dataset.hl = id;
      r.surroundContents(m);
    });
  }

  function render() {
    prose.querySelectorAll("mark.hl").forEach((m) => m.replaceWith(...m.childNodes));
    prose.normalize();
    const bs = blocks();
    list.forEach((h) => {
      const b = bs[h.b];
      if (!b || b.textContent.slice(h.s, h.e) !== h.t) return; // text changed since: skip quietly
      wrap(b, h.s, h.e, h.id);
      if (h.note) prose.querySelectorAll(`mark[data-hl="${h.id}"]`).forEach((m) => m.classList.add("has-note"));
    });
  }

  function place(rect) {
    bar.hidden = false;
    const top = window.scrollY + rect.bottom + 10;
    const left = Math.min(Math.max(window.scrollX + rect.left + rect.width / 2 - bar.offsetWidth / 2, 8), window.innerWidth - bar.offsetWidth - 8);
    bar.style.top = `${top}px`;
    bar.style.left = `${left}px`;
  }
  const hide = () => { bar.hidden = true; };

  async function shareQuote(text) {
    const title = document.querySelector(".article-hero h1")?.textContent.trim() || document.title;
    const msg = `«${text}»\n— ${title}`;
    if (navigator.share) { try { await navigator.share({ text: msg, url: location.href.split("#")[0] }); } catch (e) {} return; }
    try { await navigator.clipboard.writeText(`${msg}\n${location.href.split("#")[0]}`); flash(tr("✓ نُسخ الاقتباس", "✓ Quote copied")); } catch (e) {}
  }
  function flash(msg) {
    bar.innerHTML = `<span class="hl-msg">${msg}</span>`;
    setTimeout(hide, 1600);
  }

  function noteDialog(h) {
    const v = window.prompt(tr("ملاحظتك على هذا الاقتباس (تبقى في جهازك فقط):", "Your note on this passage (stays on your device only):"), h.note || "");
    if (v === null) return;
    h.note = v.trim();
    save(list);
    render();
  }

  // a fresh selection inside one paragraph → toolbar
  let pending = null;
  function onSelect() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return;
    const range = sel.getRangeAt(0);
    const bs = blocks();
    const bi = bs.findIndex((b) => b.contains(range.startContainer) && b.contains(range.endContainer));
    if (bi === -1) return;
    const b = bs[bi];
    const s = textOffset(b, range.startContainer, range.startOffset), e = textOffset(b, range.endContainer, range.endOffset);
    const text = b.textContent.slice(s, e);
    if (!text.trim()) return;
    pending = { b: bi, s, e, t: text };
    bar.innerHTML = `<button type="button" data-a="hl">🖍 ${tr("ظلّل", "Highlight")}</button><button type="button" data-a="note">✍️ ${tr("ملاحظة", "Note")}</button><button type="button" data-a="share">🔗 ${tr("شارك الاقتباس", "Share quote")}</button>`;
    place(range.getBoundingClientRect());
  }
  let selTimer = null;
  document.addEventListener("selectionchange", () => { clearTimeout(selTimer); selTimer = setTimeout(onSelect, 250); });

  // clicking an existing highlight → its menu
  prose.addEventListener("click", (e) => {
    const m = e.target.closest("mark.hl");
    if (!m || !window.getSelection().isCollapsed) return;
    const h = list.find((x) => x.id === m.dataset.hl);
    if (!h) return;
    pending = { existing: h };
    bar.innerHTML = (h.note ? `<p class="hl-note">✍️ ${h.note.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c])}</p>` : "") +
      `<button type="button" data-a="note">✍️ ${h.note ? tr("عدّل الملاحظة", "Edit note") : tr("أضف ملاحظة", "Add note")}</button><button type="button" data-a="share">🔗 ${tr("شارك", "Share")}</button><button type="button" data-a="del">🗑 ${tr("أزل التظليل", "Remove")}</button>`;
    place(m.getBoundingClientRect());
  });

  bar.addEventListener("mousedown", (e) => e.preventDefault()); // keep the selection while tapping the bar
  bar.addEventListener("click", (e) => {
    const a = e.target.closest("button")?.dataset.a;
    if (!a || !pending) return;
    if (pending.existing) {
      const h = pending.existing;
      if (a === "del") { list = list.filter((x) => x !== h); save(list); render(); hide(); }
      if (a === "note") { hide(); noteDialog(h); }
      if (a === "share") shareQuote(h.t);
      return;
    }
    if (a === "share") { shareQuote(pending.t); return; }
    const h = { id: Date.now().toString(36), ...pending };
    list.push(h);
    save(list);
    window.getSelection().removeAllRanges();
    render();
    hide();
    if (a === "note") noteDialog(h);
  });
  document.addEventListener("click", (e) => { if (!bar.contains(e.target) && !e.target.closest("mark.hl") && window.getSelection().isCollapsed) hide(); });
  window.addEventListener("resize", hide);

  render();
}

// Site search: titles and full article text. Arabic is matched ignoring diacritics and
// letter variants (أ/إ/آ → ا، ة → ه، ى → ي), English ignoring case.
const searchForm = document.querySelector(".site-search");
if (searchForm) {
  const input = searchForm.querySelector("input");
  const countEl = document.querySelector(".search-count");
  const list = document.querySelector(".search-results");
  let docs = null;

  const DIAC = /[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/;
  function normChar(c) {
    if (DIAC.test(c)) return "";
    if ("إأآٱ".includes(c)) return "ا";
    if (c === "ى") return "ي";
    if (c === "ة") return "ه";
    if (c === "ؤ") return "و";
    if (c === "ئ") return "ي";
    return c.toLowerCase();
  }
  // normalized text plus, for each normalized char, its index in the original
  function normMap(str) {
    let n = "";
    const map = [];
    for (let i = 0; i < str.length; i++) {
      const c = normChar(str[i]);
      for (const ch of c) { n += ch; map.push(i); }
    }
    return { n, map };
  }
  const norm = (str) => normMap(str).n;
  const esc = (str) => str.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

  function highlight(text, words) {
    const { n, map } = normMap(text);
    const spans = [];
    words.forEach((w) => {
      let i = n.indexOf(w);
      while (i !== -1) { spans.push([map[i], map[i + w.length - 1] + 1]); i = n.indexOf(w, i + w.length); }
    });
    spans.sort((a, b) => a[0] - b[0]);
    let out = "", pos = 0;
    spans.forEach(([a, b]) => { if (a < pos) return; out += esc(text.slice(pos, a)) + "<mark>" + esc(text.slice(a, b)) + "</mark>"; pos = b; });
    return out + esc(text.slice(pos));
  }

  function snippet(text, words) {
    const { n, map } = normMap(text);
    const i = n.indexOf(words[0]);
    if (i === -1) return highlight(text.slice(0, 180), words) + (text.length > 180 ? "…" : "");
    const start = Math.max(0, map[i] - 80);
    const end = Math.min(text.length, map[i] + 140);
    return (start > 0 ? "…" : "") + highlight(text.slice(start, end), words) + (end < text.length ? "…" : "");
  }

  function run() {
    const q = input.value.trim();
    const words = norm(q).split(/\s+/).filter((w) => w.length > 1);
    const url = new URL(location.href);
    if (q) url.searchParams.set("q", q); else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    if (!words.length) { list.innerHTML = ""; countEl.textContent = ""; return; }
    const hits = [];
    docs.forEach((d) => {
      const t = d.nt, x = d.nx;
      if (!words.every((w) => t.includes(w) || x.includes(w))) return;
      let score = 0;
      const phrase = words.join(" ");
      if (words.length > 1) { if (t.includes(phrase)) score += 60; if (x.includes(phrase)) score += 25; }
      words.forEach((w) => { if (t.includes(w)) score += 20; score += Math.min(10, x.split(w).length - 1); });
      hits.push({ d, score });
    });
    hits.sort((a, b) => b.score - a.score);
    countEl.textContent = hits.length
      ? tr(`عدد النتائج: ${arNum.format(hits.length)}`, `${hits.length} result${hits.length > 1 ? "s" : ""}`)
      : tr("لا توجد نتائج لهذه الكلمة.", "No results for that word.");
    list.innerHTML = hits.slice(0, 60).map(({ d }) => `
      <li class="search-hit">
        <a href="${d.u}"><h3>${highlight(d.t, words)}</h3></a>
        <p>${snippet(d.x, words)}</p>
        <p class="meta">${esc(d.d)} · ${d.c.map(esc).join("، ")}</p>
      </li>`).join("");
  }

  let timer = null;
  input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => docs && run(), 150); });
  searchForm.addEventListener("submit", (e) => { e.preventDefault(); docs && run(); });

  countEl.textContent = tr("جارٍ تحميل الفهرس…", "Loading the index…");
  fetch(searchForm.dataset.index)
    .then((r) => r.json())
    .then((data) => {
      docs = data.map((d) => ({ ...d, nt: norm(d.t), nx: norm(d.x) }));
      countEl.textContent = "";
      const q = new URLSearchParams(location.search).get("q");
      if (q) input.value = q;
      run();
    })
    .catch(() => { countEl.textContent = tr("تعذّر تحميل البحث، حدّث الصفحة.", "Couldn't load search. Please refresh."); });
  input.focus();
}

document.querySelectorAll(".year").forEach((el) => (el.textContent = new Date().getFullYear()));
