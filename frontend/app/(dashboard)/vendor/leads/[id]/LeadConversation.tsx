"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api/fetch";
import LeadStatusPill, {
  type LeadStatus,
} from "@/components/vendor/leads/LeadStatusPill";
import MessageList, {
  type ApiMessage,
} from "@/components/vendor/leads/MessageList";
import ReplyComposer from "@/components/vendor/leads/ReplyComposer";
import Button from "@/components/ui/Button";

export interface LeadDetail {
  id: number;
  status: LeadStatus | string;
  message: string;
  buyer: { id: number; display_name?: string; email?: string };
  vendor: { id: number; business_name: string };
  service?: { id: number; title: string } | null;
  package?: { id: number; tier: string; name: string } | null;
  bundle?: { id: number; name: string } | null;
  created_at: string;
}

export interface LeadMessageDto extends ApiMessage {}

interface Props {
  currentUserId: number;
  lead: LeadDetail;
  initialMessages: LeadMessageDto[];
}

const POLL_MS = 10_000;

type Tab = "conversation" | "details" | "buyer";

export default function LeadConversation({
  currentUserId,
  lead,
  initialMessages,
}: Props) {
  const [tab, setTab] = useState<Tab>("conversation");
  const [status, setStatus] = useState<string>(lead.status);
  const [messages, setMessages] = useState<LeadMessageDto[]>(initialMessages);
  const [statusUpdating, setStatusUpdating] = useState(false);
  const [statusError, setStatusError] = useState<string | null>(null);
  const sseRef = useRef<EventSource | null>(null);

  // Live updates: SSE first, fall back to 10s polling.
  useEffect(() => {
    let cancelled = false;
    let interval: ReturnType<typeof setInterval> | null = null;

    function startPolling() {
      interval = setInterval(async () => {
        if (cancelled) return;
        try {
          const data = await apiFetch<
            { results?: LeadMessageDto[] } | LeadMessageDto[]
          >(`/api/v1/leads/${lead.id}/messages/`, {}, { auth: true });
          const next = Array.isArray(data) ? data : data?.results || [];
          setMessages(next);
        } catch {
          // ignore — keep polling
        }
      }, POLL_MS);
    }

    try {
      const url = `${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/api/v1/streams/leads/${lead.id}/messages/`;
      const es = new EventSource(url, { withCredentials: true });
      sseRef.current = es;
      es.addEventListener("message", (ev: MessageEvent) => {
        try {
          const m = JSON.parse(ev.data) as LeadMessageDto;
          setMessages((curr) =>
            curr.find((x) => x.id === m.id) ? curr : [...curr, m],
          );
        } catch {
          // bad payload — ignore
        }
      });
      es.onerror = () => {
        es.close();
        sseRef.current = null;
        startPolling();
      };
    } catch {
      startPolling();
    }

    return () => {
      cancelled = true;
      if (sseRef.current) sseRef.current.close();
      if (interval) clearInterval(interval);
    };
  }, [lead.id]);

  async function send(body: string) {
    const created = await apiFetch<LeadMessageDto>(
      `/api/v1/leads/${lead.id}/messages/`,
      {
        method: "POST",
        body: JSON.stringify({ body }),
      },
      { auth: true },
    );
    setMessages((curr) => [...curr, created]);
  }

  async function setLeadStatus(next: string) {
    setStatusUpdating(true);
    setStatusError(null);
    try {
      const updated = await apiFetch<LeadDetail>(
        `/api/v1/leads/${lead.id}/status/`,
        {
          method: "PATCH",
          body: JSON.stringify({ status: next }),
        },
        { auth: true },
      );
      setStatus(updated.status);
    } catch (err) {
      setStatusError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setStatusUpdating(false);
    }
  }

  return (
    <div className="max-w-4xl">
      <p className="text-[11px] uppercase tracking-luxe text-gold mb-2">
        <Link href="/dashboard/vendor/leads" className="hover:text-gold-hi">
          ← Back to leads
        </Link>
      </p>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <h1 className="font-serif text-3xl text-ivory">
          {lead.buyer.display_name || lead.buyer.email || "Buyer"}
        </h1>
        <div className="flex items-center gap-3">
          <LeadStatusPill status={status} />
          <select
            value={status}
            disabled={statusUpdating}
            onChange={(e) => setLeadStatus(e.target.value)}
            className="bg-warm border border-gold/22 text-ivory text-xs px-3 py-2 rounded-md focus:outline-none focus:border-gold"
          >
            <option value="pending">Pending</option>
            <option value="contacted">Contacted</option>
            <option value="won">Mark won</option>
            <option value="lost">Mark lost</option>
          </select>
        </div>
      </div>
      {statusError && (
        <p role="alert" className="text-xs text-err mb-3">{statusError}</p>
      )}

      <ul className="flex gap-4 border-b border-gold/14 mb-6">
        {(["conversation", "details", "buyer"] as Tab[]).map((t) => (
          <li key={t}>
            <button
              type="button"
              onClick={() => setTab(t)}
              className={
                "px-1 pb-2 text-[11px] uppercase tracking-luxe border-b-2 transition-colors " +
                (tab === t
                  ? "border-gold text-gold"
                  : "border-transparent text-mist hover:text-gold")
              }
            >
              {t === "buyer" ? "Buyer info" : t}
            </button>
          </li>
        ))}
      </ul>

      {tab === "conversation" && (
        <section>
          <MessageList messages={messages} currentUserId={currentUserId} />
          <ReplyComposer onSend={send} />
        </section>
      )}

      {tab === "details" && (
        <section className="space-y-3 text-sm text-ivory">
          <p>
            <span className="text-mist">Service: </span>
            {lead.service?.title || "—"}
          </p>
          <p>
            <span className="text-mist">Package: </span>
            {lead.package
              ? `${lead.package.tier} — ${lead.package.name}`
              : "—"}
          </p>
          <p>
            <span className="text-mist">Bundle: </span>
            {lead.bundle?.name || "—"}
          </p>
          <p>
            <span className="text-mist">Initial message: </span>
            <span className="block mt-1 whitespace-pre-wrap">
              {lead.message}
            </span>
          </p>
        </section>
      )}

      {tab === "buyer" && (
        <section className="space-y-3 text-sm text-ivory">
          <p>
            <span className="text-mist">Name: </span>
            {lead.buyer.display_name || "—"}
          </p>
          <p>
            <span className="text-mist">Email: </span>
            {lead.buyer.email || "—"}
          </p>
          <p>
            <span className="text-mist">First contacted: </span>
            {new Date(lead.created_at).toLocaleString()}
          </p>
        </section>
      )}

      {status === "won" && (
        <div className="mt-8 border border-emerald-500/30 bg-emerald-900/20 p-4 rounded-md">
          <p className="text-sm text-emerald-200">
            Marked as won. The buyer can now leave a review.
          </p>
          <div className="mt-3">
            <Button
              href={`/marketplace/vendors/${lead.vendor.id}`}
              variant="secondary"
              size="sm"
            >
              View vendor profile
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
