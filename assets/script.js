// Theme toggle (remembers the choice)
const root = document.documentElement;
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
      const match = (tag === "all" || el.dataset.tag === tag) && (!q || el.textContent.includes(q));
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

// Contact form: opens the visitor's email app with the message ready to send
const form = document.querySelector(".contact-form");
if (form) {
  const statusEl = form.querySelector(".form-status");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const name = data.get("name").trim();
    const topic = data.get("topic");
    const message = data.get("message").trim();

    statusEl.className = "form-status";
    if (!name || !message) {
      statusEl.textContent = "يرجى كتابة اسمك ورسالتك.";
      statusEl.classList.add("error");
      return;
    }
    const subject = `${topic} من ${name}`;
    const body = `${message}\n\n— ${name}`;
    window.location.href =
      `mailto:${form.dataset.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    statusEl.textContent = "فتحنا لك تطبيق البريد والرسالة جاهزة، اضغط «إرسال» هناك.";
    statusEl.classList.add("success");
  });
}

document.querySelectorAll(".year").forEach((el) => (el.textContent = new Date().getFullYear()));
