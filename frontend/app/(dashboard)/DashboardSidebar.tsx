"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import type { CurrentUser } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

interface NavLink {
  label: string;
  href: string;
  group?: string;
}

function buildLinks(user: CurrentUser): NavLink[] {
  const all: NavLink[] = [
    { label: "Home", href: "/dashboard", group: "Account" },
    { label: "Profile", href: "/dashboard/profile", group: "Account" },
    { label: "Settings", href: "/dashboard/settings", group: "Account" },
    { label: "Furniture remover", href: "/dashboard/tools/furniture-remover", group: "Tools" },
    { label: "Description writer", href: "/dashboard/tools/description-writer", group: "Tools" },
  ];

  if (user.is_realtor) {
    all.push(
      { label: "My posts", href: "/dashboard/realtor/posts", group: "Realtor" },
      { label: "License status", href: "/dashboard/realtor", group: "Realtor" },
    );
  }
  if (user.is_vendor) {
    all.push(
      { label: "My services", href: "/dashboard/vendor", group: "Vendor" },
      { label: "Bundles", href: "/dashboard/vendor/bundles", group: "Vendor" },
      { label: "Leads", href: "/dashboard/vendor/leads", group: "Vendor" },
      { label: "Onboarding", href: "/dashboard/vendor/onboard", group: "Vendor" },
    );
  }
  if (user.is_staff) {
    all.push(
      { label: "Mod queue", href: "/dashboard/mod/queue", group: "Staff" },
      { label: "Investigate", href: "/dashboard/mod", group: "Staff" },
      { label: "Operations", href: "/dashboard/ops", group: "Staff" },
    );
  }

  return all;
}

/**
 * Build the 5-item bottom-nav slate by role priority. Last slot is always
 * "More" which opens a sheet with everything else.
 */
function bottomNavFor(user: CurrentUser): { label: string; href: string }[] {
  if (user.is_staff) {
    return [
      { label: "Queue", href: "/dashboard/mod/queue" },
      { label: "Stats", href: "/dashboard/mod/stats" },
      { label: "Investigate", href: "/dashboard/mod/investigate" },
      { label: "Notifications", href: "/dashboard/notifications" },
    ];
  }
  if (user.is_vendor) {
    return [
      { label: "Home", href: "/dashboard" },
      { label: "Leads", href: "/dashboard/vendor/leads" },
      { label: "Services", href: "/dashboard/vendor" },
      { label: "Notifications", href: "/dashboard/notifications" },
    ];
  }
  if (user.is_realtor) {
    return [
      { label: "Home", href: "/dashboard" },
      { label: "Posts", href: "/dashboard/realtor/posts" },
      { label: "License", href: "/dashboard/realtor" },
      { label: "Notifications", href: "/dashboard/notifications" },
    ];
  }
  return [
    { label: "Home", href: "/dashboard" },
    { label: "Notifications", href: "/dashboard/notifications" },
    { label: "Tools", href: "/dashboard/tools/furniture-remover" },
    { label: "Profile", href: "/dashboard/profile" },
  ];
}

export default function DashboardSidebar({ user }: { user: CurrentUser }) {
  const pathname = usePathname();
  const links = buildLinks(user);

  const groups: Record<string, NavLink[]> = {};
  for (const l of links) {
    const g = l.group || "Account";
    if (!groups[g]) groups[g] = [];
    groups[g].push(l);
  }

  return (
    <>
      <aside className="hidden lg:block w-60 flex-shrink-0 border-r border-gold/14 bg-deep min-h-[calc(100vh-4rem)] sticky top-16 self-start">
        <nav className="p-6 space-y-7">
          {Object.entries(groups).map(([group, items]) => (
            <div key={group}>
              <p className="text-[10px] uppercase tracking-luxe text-dim mb-3">
                {group}
              </p>
              <ul className="space-y-0.5">
                {items.map((l) => {
                  const active =
                    pathname === l.href ||
                    (l.href !== "/dashboard" && pathname.startsWith(l.href));
                  return (
                    <li key={l.href}>
                      <Link
                        href={l.href}
                        className={cn(
                          "block px-3 py-2 text-sm transition-colors rounded",
                          active
                            ? "bg-gold/15 text-gold-hi border-l-2 border-gold"
                            : "text-mist hover:text-ivory hover:bg-warm/40",
                        )}
                      >
                        {l.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      <MobileBottomNav user={user} />
    </>
  );
}

function MobileBottomNav({ user }: { user: CurrentUser }) {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(false);
  const primary = bottomNavFor(user);
  const allLinks = buildLinks(user);

  // Lock body scroll when sheet open
  useEffect(() => {
    if (!moreOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMoreOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [moreOpen]);

  return (
    <>
      <nav
        aria-label="Dashboard navigation"
        className="lg:hidden fixed inset-x-0 bottom-0 z-40 bg-black/95 backdrop-blur-lg border-t border-gold/22 pb-[env(safe-area-inset-bottom)]"
      >
        <ul className="grid grid-cols-5 max-w-md mx-auto">
          {primary.map((l) => {
            const active =
              pathname === l.href ||
              (l.href !== "/dashboard" && pathname.startsWith(l.href));
            return (
              <li key={l.href}>
                <Link
                  href={l.href}
                  data-touch
                  className={cn(
                    "flex flex-col items-center justify-center min-h-[56px] px-2 py-2 text-[10px] uppercase tracking-luxe transition-colors",
                    active ? "text-gold" : "text-mist",
                  )}
                >
                  {l.label}
                </Link>
              </li>
            );
          })}
          <li>
            <button
              type="button"
              onClick={() => setMoreOpen(true)}
              className="w-full flex flex-col items-center justify-center min-h-[56px] px-2 py-2 text-[10px] uppercase tracking-luxe text-mist hover:text-gold"
              aria-label="More navigation"
              aria-haspopup="dialog"
              aria-expanded={moreOpen}
            >
              More
            </button>
          </li>
        </ul>
      </nav>

      {moreOpen && (
        <>
          <div
            className="lg:hidden fixed inset-0 z-50 bg-black/70"
            onClick={() => setMoreOpen(false)}
            aria-hidden
          />
          <div
            role="dialog"
            aria-modal="true"
            aria-label="More navigation"
            className="lg:hidden fixed inset-x-0 bottom-0 z-50 bg-deep border-t border-gold/22 max-h-[70vh] overflow-y-auto safe-bottom"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-gold/14 sticky top-0 bg-deep">
              <p className="text-[11px] uppercase tracking-luxe text-gold">
                More
              </p>
              <button
                type="button"
                onClick={() => setMoreOpen(false)}
                aria-label="Close more navigation"
                className="inline-flex items-center justify-center w-11 h-11 text-mist hover:text-gold"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
                  <path d="M2 2l12 12M14 2L2 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <nav className="px-5 py-4 space-y-2">
              {allLinks.map((l) => {
                const active =
                  pathname === l.href ||
                  (l.href !== "/dashboard" && pathname.startsWith(l.href));
                return (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={() => setMoreOpen(false)}
                    data-touch
                    className={cn(
                      "flex items-center justify-between min-h-11 px-3 py-3 rounded text-sm border-b border-gold/14 last:border-0",
                      active
                        ? "bg-gold/15 text-gold-hi"
                        : "text-mist hover:text-ivory hover:bg-warm/40",
                    )}
                  >
                    <span>{l.label}</span>
                    {l.group && (
                      <span className="text-[10px] uppercase tracking-luxe text-dim">
                        {l.group}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>
        </>
      )}
    </>
  );
}
