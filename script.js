// Theme toggle (remembers the choice)
const root = document.documentElement;
const themeBtn = document.querySelector(".theme-toggle");

function applyTheme(theme) {
  root.dataset.theme = theme;
  themeBtn.textContent = theme === "dark" ? "☀️" : "🌙";
}

let savedTheme = null;
try { savedTheme = localStorage.getItem("theme"); } catch (e) {}
applyTheme(savedTheme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));

themeBtn.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("theme", next); } catch (e) {}
});

// Mobile menu
const menuBtn = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");
menuBtn.addEventListener("click", () => {
  const open = navLinks.classList.toggle("open");
  menuBtn.setAttribute("aria-expanded", open);
});
navLinks.querySelectorAll("a").forEach((link) =>
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
    menuBtn.setAttribute("aria-expanded", "false");
  })
);

// Project filters
const filters = document.querySelectorAll(".filter");
const projects = document.querySelectorAll(".project");
filters.forEach((btn) =>
  btn.addEventListener("click", () => {
    filters.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const cat = btn.dataset.filter;
    projects.forEach((p) => p.classList.toggle("hidden", cat !== "all" && p.dataset.cat !== cat));
  })
);

// Animated counters
function animateCount(el) {
  const target = Number(el.dataset.count);
  const start = performance.now();
  const duration = 1200;
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    el.textContent = "+" + Math.round(target * progress);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// Reveal sections on scroll
const revealEls = document.querySelectorAll(".section-title, .about p, .stats, .card, .project, .contact-form");
revealEls.forEach((el) => el.classList.add("reveal"));

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("visible");
      entry.target.querySelectorAll("[data-count]").forEach(animateCount);
      observer.unobserve(entry.target);
    });
  },
  { threshold: 0.15 }
);
revealEls.forEach((el) => observer.observe(el));

// Contact form (client-side validation only)
const form = document.querySelector(".contact-form");
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
  statusEl.textContent = `شكراً ${name}! تم استلام رسالتك وسأرد عليك قريباً.`;
  statusEl.classList.add("success");
  form.reset();
});

document.getElementById("year").textContent = new Date().getFullYear();
