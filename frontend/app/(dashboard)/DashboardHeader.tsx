"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api/fetch";
import type { CurrentUser } from "@/lib/auth/server";
import { useToast } from "@/components/ui/Toast";

interface DashboardHeaderProps {
  user: CurrentUser;
}

export default function DashboardHeader({ user }: DashboardHeaderProps) {
  const router = useRouter();
  const toast = useToast();

  async function logout() {
    try {
      await apiFetch(
        "/api/v1/auth/logout/",
        { method: "POST" },
        { auth: true },
      );
    } catch {
      // even if API rejects, drop the client state
    }
    toast.push("Signed out", "info");
    router.push("/");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-40 bg-black border-b border-gold/14 backdrop-blur supports-[backdrop-filter]:bg-black/85">
      <div className="px-6 lg:px-10 h-16 flex items-center justify-between gap-4">
        <Link
          href="/"
          className="font-serif tracking-luxe uppercase text-gold text-base"
        >
          Yakima Web
        </Link>
        <div className="flex items-center gap-5">
          <Link
            href="/dashboard"
            className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold hidden sm:inline"
          >
            Dashboard
          </Link>
          <span className="text-xs text-mist hidden md:inline truncate max-w-[180px]">
            {user.display_name || user.email}
          </span>
          <button
            type="button"
            onClick={logout}
            className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold border border-gold/22 px-4 py-2 hover:border-gold/52 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
