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
  ".section-title, .tile, .post-card, .note-card, .book, .blog-door, .quote, .timeline li, .bio, .contact"
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

// Contact form (client-side validation only)
const form = document.querySelector(".contact-form");
if (form) {
  const statusEl = form.querySelector(".form-status");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const name = data.get("name").trim();
    const email = data.get("email").trim();
    const message = data.get("message").trim();

    statusEl.className = "form-status";
    if (!name || !email || !message) {
      statusEl.textContent = "يرجى تعبئة جميع الحقول.";
      statusEl.classList.add("error");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      statusEl.textContent = "يرجى إدخال بريد إلكتروني صحيح.";
      statusEl.classList.add("error");
      return;
    }
    statusEl.textContent = `شكراً ${name}! وصلت رسالتك وسأرد عليك قريباً.`;
    statusEl.classList.add("success");
    form.reset();
  });
}

document.querySelectorAll(".year").forEach((el) => (el.textContent = new Date().getFullYear()));
