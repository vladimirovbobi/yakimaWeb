"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api/fetch";
import { cn } from "@/lib/utils";

export interface NotificationDto {
  id: number;
  kind: string;
  title: string;
  body: string;
  link: string;
  is_read: boolean;
  created_at: string;
}

interface UnreadCount {
  count: number;
}

const POLL_MS = 30_000;

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(0);
  const [items, setItems] = useState<NotificationDto[]>([]);
  const [loading, setLoading] = useState(false);
  const popRef = useRef<HTMLDivElement>(null);

  // Poll unread count.
  useEffect(() => {
    let cancel = false;

    async function tick() {
      try {
        const data = await apiFetch<UnreadCount>(
          "/api/v1/me/notifications/unread-count/",
          {},
          { auth: true },
        );
        if (!cancel) setCount(data.count || 0);
      } catch {
        // session may be expired; silent
      }
    }

    void tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      cancel = true;
      clearInterval(id);
    };
  }, []);

  // Fetch first page when opening.
  useEffect(() => {
    if (!open) return;
    let cancel = false;
    setLoading(true);
    apiFetch<{ results?: NotificationDto[] } | NotificationDto[]>(
      "/api/v1/me/notifications/",
      {},
      { auth: true },
    )
      .then((data) => {
        if (cancel) return;
        const rows = Array.isArray(data) ? data : data?.results || [];
        setItems(rows.slice(0, 10));
      })
      .catch(() => {
        if (!cancel) setItems([]);
      })
      .finally(() => {
        if (!cancel) setLoading(false);
      });
    return () => {
      cancel = true;
    };
  }, [open]);

  // Close on outside click.
  useEffect(() => {
    if (!open) return;
    function onClick(e: MouseEvent) {
      if (popRef.current && !popRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  async function markAllRead() {
    try {
      await apiFetch(
        "/api/v1/me/notifications/read-all/",
        { method: "POST" },
        { auth: true },
      );
      setItems((curr) => curr.map((n) => ({ ...n, is_read: true })));
      setCount(0);
    } catch {
      // ignore
    }
  }

  return (
    <div className="relative" ref={popRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={`Notifications, ${count} unread`}
        className="relative inline-flex items-center justify-center w-10 h-10 text-mist hover:text-gold border border-gold/22 hover:border-gold/52 rounded-md transition-colors"
      >
        <BellIcon />
        {count > 0 && (
          <span
            aria-hidden
            className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 text-[10px] font-medium rounded-full bg-rose-500 text-black flex items-center justify-center"
          >
            {count > 99 ? "99+" : count}
          </span>
        )}
      </button>
      {open && (
        <div
          role="dialog"
          className="absolute right-0 top-12 w-80 sm:w-96 bg-panel border border-gold/22 rounded-md shadow-card z-50 overflow-hidden"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-gold/14">
            <p className="text-[11px] uppercase tracking-luxe text-gold">
              Notifications
            </p>
            <button
              type="button"
              onClick={markAllRead}
              className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold"
            >
              Mark all read
            </button>
          </div>
          <ul className="max-h-96 overflow-y-auto divide-y divide-gold/14">
            {loading ? (
              <li className="px-4 py-6 text-center text-mist text-sm">
                Loading…
              </li>
            ) : items.length === 0 ? (
              <li className="px-4 py-6 text-center text-mist text-sm">
                You're all caught up.
              </li>
            ) : (
              items.map((n) => (
                <li key={n.id}>
                  <Link
                    href={n.link || "/dashboard/notifications"}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "block px-4 py-3 hover:bg-warm/40",
                      !n.is_read && "bg-warm/30",
                    )}
                  >
                    <p className="text-[10px] uppercase tracking-luxe text-dim mb-0.5">
                      {n.kind.replace(/_/g, " ")}
                    </p>
                    <p className="text-sm text-ivory line-clamp-1">
                      {n.title}
                    </p>
                    {n.body && (
                      <p className="text-xs text-mist line-clamp-2 mt-1">
                        {n.body}
                      </p>
                    )}
                  </Link>
                </li>
              ))
            )}
          </ul>
          <div className="px-4 py-3 border-t border-gold/14 text-center">
            <Link
              href="/dashboard/notifications"
              onClick={() => setOpen(false)}
              className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
            >
              View all
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function BellIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9z" />
      <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
    </svg>
  );
}
