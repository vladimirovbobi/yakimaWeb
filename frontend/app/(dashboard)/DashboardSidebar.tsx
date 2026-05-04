"use client";

import Link from "next/link";
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

      <nav
        aria-label="Dashboard navigation"
        className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-black border-t border-gold/22 px-2 py-2"
      >
        <ul className="flex items-center justify-around">
          {[
            { label: "Home", href: "/dashboard" },
            { label: "Profile", href: "/dashboard/profile" },
            { label: "Tools", href: "/dashboard/tools/furniture-remover" },
            { label: "Settings", href: "/dashboard/settings" },
          ].map((l) => {
            const active =
              pathname === l.href ||
              (l.href !== "/dashboard" && pathname.startsWith(l.href));
            return (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className={cn(
                    "flex flex-col items-center justify-center px-3 py-2 text-[10px] uppercase tracking-luxe transition-colors min-w-[60px]",
                    active ? "text-gold" : "text-mist",
                  )}
                >
                  {l.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
