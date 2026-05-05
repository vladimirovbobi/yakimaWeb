"use client";

import Link from "next/link";
import { useState } from "react";
import { apiFetch } from "@/lib/api/fetch";
import { cn } from "@/lib/utils";
import EmptyState from "@/components/layout/EmptyState";
import type { NotificationDto } from "./page";

interface Props {
  filter: "all" | "unread";
  kind: string;
  kinds: string[];
  items: NotificationDto[];
  nextUrl: string | null;
  previousUrl: string | null;
}

function buildHref(filter: string, kind: string, cursor?: string) {
  const sp = new URLSearchParams();
  if (filter !== "all") sp.set("filter", filter);
  if (kind !== "all") sp.set("kind", kind);
  if (cursor) sp.set("cursor", cursor);
  const q = sp.toString();
  return `/dashboard/notifications${q ? `?${q}` : ""}`;
}

function cursorFromUrl(url: string | null): string | undefined {
  if (!url) return undefined;
  try {
    return new URL(url, "http://x").searchParams.get("cursor") || undefined;
  } catch {
    return undefined;
  }
}

export default function NotificationsClient({
  filter,
  kind,
  kinds,
  items,
  nextUrl,
  previousUrl,
}: Props) {
  const [rows, setRows] = useState<NotificationDto[]>(items);

  async function markAllRead() {
    try {
      await apiFetch(
        "/api/v1/me/notifications/read-all/",
        { method: "POST" },
        { auth: true },
      );
      setRows((curr) => curr.map((n) => ({ ...n, is_read: true })));
    } catch {
      // ignore
    }
  }

  async function markRead(id: number) {
    try {
      await apiFetch(
        `/api/v1/me/notifications/${id}/read/`,
        { method: "POST" },
        { auth: true },
      );
      setRows((curr) =>
        curr.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
      );
    } catch {
      // ignore
    }
  }

  return (
    <div className="max-w-3xl">
      <p className="text-[11px] uppercase tracking-luxe text-gold mb-3">
        Inbox
      </p>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h1 className="font-serif text-3xl text-ivory">Notifications</h1>
        <button
          type="button"
          onClick={markAllRead}
          className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold border border-gold/22 px-4 py-2 hover:border-gold/52 transition-colors"
        >
          Mark all read
        </button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {(["all", "unread"] as const).map((f) => (
          <Link
            key={f}
            href={buildHref(f, kind)}
            className={cn(
              "px-3 py-1.5 text-[11px] uppercase tracking-luxe rounded-full border",
              filter === f
                ? "bg-gold text-black border-gold"
                : "border-gold/30 text-mist hover:border-gold hover:text-gold",
            )}
          >
            {f}
          </Link>
        ))}
      </div>
      <div className="flex flex-wrap gap-2 mb-8">
        {kinds.map((k) => (
          <Link
            key={k}
            href={buildHref(filter, k)}
            className={cn(
              "px-3 py-1 text-[10px] uppercase tracking-luxe rounded-full border",
              kind === k
                ? "bg-gold/20 border-gold text-gold"
                : "border-gold/14 text-mist hover:border-gold hover:text-gold",
            )}
          >
            {k.replace(/_/g, " ")}
          </Link>
        ))}
      </div>

      {rows.length === 0 ? (
        <EmptyState
          kind="notifications"
          title="You're all caught up"
          body="No notifications match this filter. New activity will land here as it happens."
        />
      ) : (
        <ul className="divide-y divide-gold/14 border border-gold/14 rounded-md">
          {rows.map((n) => (
            <li
              key={n.id}
              className={cn(
                "px-5 py-4 hover:bg-warm/30",
                !n.is_read && "bg-warm/20",
              )}
            >
              <div className="flex justify-between items-start gap-4">
                <div className="min-w-0">
                  <p className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                    {n.kind.replace(/_/g, " ")} ·{" "}
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                  {n.link ? (
                    <Link
                      href={n.link}
                      onClick={() => markRead(n.id)}
                      className="font-serif text-lg text-ivory hover:text-gold"
                    >
                      {n.title}
                    </Link>
                  ) : (
                    <p className="font-serif text-lg text-ivory">{n.title}</p>
                  )}
                  {n.body && (
                    <p className="text-sm text-mist mt-1">{n.body}</p>
                  )}
                </div>
                {!n.is_read && (
                  <button
                    type="button"
                    onClick={() => markRead(n.id)}
                    className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold whitespace-nowrap"
                  >
                    Mark read
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <nav className="mt-6 flex justify-between text-[11px] uppercase tracking-luxe">
        {previousUrl ? (
          <Link
            href={buildHref(filter, kind, cursorFromUrl(previousUrl))}
            className="text-mist hover:text-gold"
          >
            ← Newer
          </Link>
        ) : (
          <span />
        )}
        {nextUrl ? (
          <Link
            href={buildHref(filter, kind, cursorFromUrl(nextUrl))}
            className="text-mist hover:text-gold"
          >
            Older →
          </Link>
        ) : (
          <span />
        )}
      </nav>
    </div>
  );
}
