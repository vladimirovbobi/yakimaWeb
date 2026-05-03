// Yakima Real Estate Hub — frontend entry
// Order matters: stylesheet → libs → app code.

import "../css/tailwind.css";

import Alpine from "alpinejs";
import intersect from "@alpinejs/intersect";
import focus from "@alpinejs/focus";
import persist from "@alpinejs/persist";
import "htmx.org";
import { animate, scroll, inView, stagger } from "motion";
import Lenis from "lenis";

// ─── Lenis smooth scroll ────────────────────────────────────────────────
if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const lenis = new Lenis({ duration: 1.0, smoothWheel: true });
  function raf(t) { lenis.raf(t); requestAnimationFrame(raf); }
  requestAnimationFrame(raf);
  window.lenis = lenis;
}

// ─── Alpine plugins + custom directives ─────────────────────────────────
Alpine.plugin(intersect);
Alpine.plugin(focus);
Alpine.plugin(persist);

// x-reveal: drop on any element to reveal on scroll-in
// Usage: <div x-reveal x-data> ... </div>  or  x-reveal:300 (delay ms)
Alpine.directive("reveal", (el, { value }, { evaluate, cleanup }) => {
  const delay = value ? parseInt(value, 10) : 0;
  el.classList.add("reveal-init");
  if (delay) el.style.setProperty("--reveal-delay", `${delay}ms`);

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) { el.classList.add("reveal-on"); return; }

  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        el.classList.add("reveal-on");
        obs.disconnect();
      }
    });
  }, { rootMargin: "0px 0px -10% 0px", threshold: 0.1 });
  obs.observe(el);
  cleanup(() => obs.disconnect());
});

// Stagger reveal — children of a x-reveal-stagger fade in with cascading delay
Alpine.directive("reveal-stagger", (el) => {
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const children = Array.from(el.children);
  children.forEach((c, i) => {
    c.classList.add("reveal-init");
    c.style.setProperty("--reveal-delay", `${i * 80}ms`);
  });
  if (reduced) { children.forEach(c => c.classList.add("reveal-on")); return; }
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        children.forEach(c => c.classList.add("reveal-on"));
        obs.disconnect();
      }
    });
  }, { rootMargin: "0px 0px -5% 0px", threshold: 0.05 });
  obs.observe(el);
});

window.Alpine = Alpine;
Alpine.start();

// ─── HTMX config ────────────────────────────────────────────────────────
document.body.addEventListener("htmx:configRequest", (evt) => {
  // CSRF for Django
  const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
  if (csrf) evt.detail.headers["X-CSRFToken"] = csrf;
});

document.body.addEventListener("htmx:responseError", (evt) => {
  console.warn("HTMX error", evt.detail);
});

// ─── Motion One helpers (page hover lifts, button presses) ──────────────
window.YW = { animate, scroll, inView, stagger };
