"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

const navLinks = [
  { name: "Marketplace", href: "/marketplace" },
  { name: "Community", href: "/community" },
  { name: "Tools", href: "/tools" },
  { name: "Blog", href: "/blog" },
  { name: "About", href: "/about" },
];

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 20);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      <header
        className={cn(
          "fixed top-0 left-0 right-0 z-[100] transition-[background-color,backdrop-filter,border-color] duration-300",
          isScrolled
            ? "bg-dark-bg/95 supports-[backdrop-filter]:bg-dark-bg/70 backdrop-blur-xl border-b border-gold/22"
            : "bg-transparent border-b border-transparent",
        )}
      >
        <div className="max-w-[1280px] mx-auto h-[72px] sm:h-[88px] px-4 sm:px-6 lg:px-12 flex items-center justify-between">
          <Link
            href="/"
            className={cn(
              "flex items-center gap-3 min-w-0 flex-shrink-0",
            )}
            aria-label="Yakima Real Estate Hub home"
          >
            <span
              className={cn(
                "font-serif tracking-luxe uppercase text-base sm:text-lg md:text-xl transition-colors",
                isScrolled ? "text-gold-hi" : "text-gold",
              )}
            >
              Yakima Web
            </span>
            <span
              className={cn(
                "hidden md:inline text-xs tracking-luxe uppercase pl-3 border-l transition-colors",
                isScrolled
                  ? "text-dark-mist/70 border-gold/22"
                  : "text-mist/70 border-gold/22",
              )}
            >
              Real Estate Hub
            </span>
          </Link>

          <nav className="hidden lg:flex items-center gap-7">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  "transition-colors text-xs uppercase tracking-luxe font-light hover:text-gold-hi",
                  isScrolled ? "text-dark-mist" : "text-ivory",
                )}
              >
                {link.name}
              </Link>
            ))}
            <Link
              href="/login"
              className={cn(
                "transition-colors text-xs uppercase tracking-luxe font-light pl-6 border-l border-gold/22 hover:text-gold-hi",
                isScrolled ? "text-dark-mist" : "text-ivory",
              )}
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className={cn(
                "inline-flex items-center text-xs uppercase tracking-cap border px-5 py-3 transition-colors",
                isScrolled
                  ? "text-gold-hi border-gold/52 hover:bg-gold-hi hover:text-dark-bg"
                  : "text-gold border-gold/52 hover:bg-dark-bg hover:text-dark-text hover:border-dark-bg",
              )}
            >
              Get started
            </Link>
          </nav>

          <button
            type="button"
            className={cn(
              "lg:hidden inline-flex items-center justify-center w-11 h-11 -mr-2 relative z-[101] transition-colors",
              isScrolled ? "text-gold-hi" : "text-gold",
            )}
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            aria-controls="mobile-nav"
          >
            {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {open && (
        <div
          className="lg:hidden fixed inset-0 z-[90] bg-dark-bg/70 backdrop-blur-sm top-[72px] sm:top-[88px]"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}

      {open && (
        <div
          id="mobile-nav"
          role="dialog"
          aria-modal="true"
          aria-label="Site navigation"
          className="lg:hidden fixed left-0 right-0 top-[72px] sm:top-[88px] bottom-0 z-[95] bg-dark-bg border-t border-gold/14 overflow-y-auto safe-bottom"
        >
          <nav className="max-w-[1180px] mx-auto px-6 py-8 space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                data-touch
                className="block text-dark-mist hover:text-gold-hi uppercase text-sm tracking-luxe py-4 border-b border-gold/14"
              >
                {link.name}
              </Link>
            ))}
            <div className="pt-8 space-y-3">
              <Link
                href="/login"
                onClick={() => setOpen(false)}
                data-touch
                className="flex items-center justify-center text-gold-hi uppercase text-xs tracking-cap py-4 border border-gold/40"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                onClick={() => setOpen(false)}
                data-touch
                className="flex w-full items-center justify-center bg-gold-hi text-dark-bg uppercase text-xs tracking-cap py-4 font-medium"
              >
                Get started
              </Link>
            </div>
          </nav>
        </div>
      )}
    </>
  );
}
