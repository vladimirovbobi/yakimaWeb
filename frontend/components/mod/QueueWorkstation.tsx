"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import type { ActionTemplate, QueueItem } from "@/lib/api/types";
import InvestigateDrawer from "./InvestigateDrawer";

interface QueueWorkstationProps {
  initialItem: QueueItem | null;
  initialTemplates: ActionTemplate[];
  totalQueueDepth: number;
}

type DecisionAction = "approve" | "remove" | "escalate";

export default function QueueWorkstation({
  initialItem,
  initialTemplates,
  totalQueueDepth,
}: QueueWorkstationProps) {
  const [item, setItem] = useState<QueueItem | null>(initialItem);
  const [templates] = useState<ActionTemplate[]>(initialTemplates);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [escalateOpen, setEscalateOpen] = useState(false);
  const [escalateNotes, setEscalateNotes] = useState("");
  const [investigateOpen, setInvestigateOpen] = useState(false);
  const [completed, setCompleted] = useState(0);
  const [queueDepth, setQueueDepth] = useState(totalQueueDepth);
  const [pace, setPace] = useState<number[]>([]);
  const lastDecisionAt = useRef<number>(Date.now());

  const reasonRef = useRef<HTMLTextAreaElement>(null);
  const templateRef = useRef<HTMLSelectElement>(null);

  const fetchNext = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const next = await apiFetch<QueueItem | { detail: string }>(
        "/api/v1/mod/queue/next/",
        { method: "GET" },
        { auth: true },
      );
      if (next && typeof next === "object" && "id" in next) {
        setItem(next as QueueItem);
      } else {
        setItem(null);
      }
      setSelectedTemplate("");
      setReason("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 204) {
        setItem(null);
      } else {
        setError("Failed to load next item.");
      }
    } finally {
      setBusy(false);
    }
  }, []);

  const submitDecision = useCallback(
    async (action: DecisionAction, customReason?: string, notes?: string) => {
      if (!item || busy) return;
      setBusy(true);
      setError(null);
      try {
        if (action === "escalate") {
          await apiFetch(
            `/api/v1/mod/items/${item.id}/escalate/`,
            {
              method: "POST",
              body: JSON.stringify({ notes: notes ?? "" }),
            },
            { auth: true },
          );
        } else {
          const tmpl = templates.find((t) => t.slug === selectedTemplate);
          const finalReason =
            customReason ?? reason ?? tmpl?.default_reason ?? "";
          await apiFetch(
            `/api/v1/mod/items/${item.id}/decision/`,
            {
              method: "POST",
              body: JSON.stringify({
                action,
                reason: finalReason,
                action_template: selectedTemplate || "",
              }),
            },
            { auth: true },
          );
        }

        const now = Date.now();
        const elapsedSec = Math.max(1, (now - lastDecisionAt.current) / 1000);
        lastDecisionAt.current = now;
        setPace((prev) => [...prev.slice(-9), elapsedSec]);
        setCompleted((c) => c + 1);
        setQueueDepth((d) => Math.max(0, d - 1));
        setEscalateOpen(false);
        setEscalateNotes("");
        await fetchNext();
      } catch {
        setError("Decision failed. Try again.");
      } finally {
        setBusy(false);
      }
    },
    [item, busy, selectedTemplate, reason, templates, fetchNext],
  );

  // Keyboard shortcuts.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const inEditable =
        target?.tagName === "INPUT" ||
        target?.tagName === "TEXTAREA" ||
        target?.tagName === "SELECT" ||
        target?.isContentEditable;

      if (escalateOpen && e.key === "Escape") {
        setEscalateOpen(false);
        return;
      }
      if (inEditable) return;

      switch (e.key.toLowerCase()) {
        case "a":
          e.preventDefault();
          submitDecision("approve");
          break;
        case "r":
          e.preventDefault();
          submitDecision("remove");
          break;
        case "e":
          e.preventDefault();
          setEscalateOpen(true);
          break;
        case "t":
          e.preventDefault();
          templateRef.current?.focus();
          break;
        case "n":
          e.preventDefault();
          fetchNext();
          break;
        case "i":
          e.preventDefault();
          setInvestigateOpen(true);
          break;
        default:
          break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [submitDecision, fetchNext, escalateOpen]);

  // SSE — Sprint 6 wires real stream; soft-fail on 404.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/v1/streams/mod-queue/`;
    let es: EventSource | null = null;
    try {
      es = new EventSource(url, { withCredentials: true });
      es.onmessage = (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          if (typeof payload?.queue_depth === "number") {
            setQueueDepth(payload.queue_depth);
          }
        } catch {
          // ignore malformed
        }
      };
      es.onerror = () => {
        es?.close();
      };
    } catch {
      // SSE not yet wired — Sprint 6 lands the stream endpoint.
    }
    return () => {
      es?.close();
    };
  }, []);

  const avgPace = useMemo(() => {
    if (pace.length === 0) return null;
    const mean = pace.reduce((acc, n) => acc + n, 0) / pace.length;
    return Math.round(mean);
  }, [pace]);

  if (!item) {
    return (
      <div className="border border-gold/22 bg-deep p-12 text-center">
        <div className="ey mb-3">Queue empty</div>
        <h2 className="font-serif font-light text-ivory text-2xl mb-3">
          Nothing pending review.
        </h2>
        <p className="text-mist text-sm">
          New items will land here automatically. Press N to refresh manually.
        </p>
        <button
          type="button"
          onClick={fetchNext}
          className="mt-6 px-4 py-2 border border-gold/40 text-gold uppercase tracking-luxe text-[11px] hover:bg-gold/10"
        >
          Refresh (N)
        </button>
      </div>
    );
  }

  const cls = item.classifier_output;

  return (
    <div className="space-y-6">
      {/* Top stats bar */}
      <div className="flex items-center justify-between text-[11px] uppercase tracking-luxe text-mist border-b border-gold/14 pb-3">
        <div>
          Item <span className="text-gold-hi">{completed + 1}</span> of{" "}
          <span className="text-gold-hi">{queueDepth}</span> total
        </div>
        <div className="flex items-center gap-6">
          {avgPace !== null && (
            <div>
              avg pace <span className="text-gold-hi">{avgPace}s</span>
            </div>
          )}
          <div>completed today {completed}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_22rem] gap-6">
        {/* Main item card */}
        <article className="border border-gold/22 bg-panel p-4 sm:p-6 lg:p-8 order-2 lg:order-1">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 border border-gold/40 text-gold uppercase tracking-luxe text-[10px]">
                {item.target_type}
              </span>
              <span className="px-3 py-1 border border-gold/22 text-mist uppercase tracking-luxe text-[10px]">
                Severity {item.severity ?? "—"}
              </span>
              {item.reason_flag && (
                <span className="px-3 py-1 border border-rose-400/40 text-rose-300 uppercase tracking-luxe text-[10px]">
                  Flag: {item.reason_flag}
                </span>
              )}
            </div>
            <span className="text-[11px] uppercase tracking-luxe text-dim flex-shrink-0">
              ID #{item.id}
            </span>
          </div>

          <h3 className="font-serif font-light text-ivory text-2xl mb-4">
            Item under review
          </h3>
          <div
            className="prose prose-invert max-w-none text-mist mb-8 whitespace-pre-wrap"
            dangerouslySetInnerHTML={{ __html: item.target_excerpt }}
          />

          {item.target_full_url && (
            <a
              href={item.target_full_url}
              target="_blank"
              rel="noreferrer"
              className="inline-block text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
            >
              View original surface →
            </a>
          )}

          {/* Classifier output (redacted — no rationale) */}
          <div className="mt-8 pt-6 border-t border-gold/14">
            <div className="ey mb-3">Classifier signals</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  Allowed
                </div>
                <div className="text-ivory">
                  {cls.allowed === null ? "—" : cls.allowed ? "Yes" : "No"}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  Categories
                </div>
                <div className="text-ivory">
                  {cls.categories?.join(", ") || "—"}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  Severity
                </div>
                <div className="text-ivory">{cls.severity ?? "—"}</div>
              </div>
            </div>
            <p className="text-[10px] uppercase tracking-luxe text-dim mt-3">
              Free-text rationale is hidden from moderators per safety contract.
            </p>
          </div>
        </article>

        {/* Action panel */}
        <aside className="border border-gold/22 bg-deep p-5 sm:p-6 space-y-5 h-fit lg:sticky lg:top-24 order-1 lg:order-2">
          <div>
            <div className="ey mb-3">Decide</div>
            <div className="space-y-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => submitDecision("approve")}
                className="w-full px-4 py-3 border border-emerald-400/40 text-emerald-300 hover:bg-emerald-400/10 uppercase tracking-luxe text-[11px] flex items-center justify-between"
              >
                <span>Approve</span>
                <kbd className="text-dim">A</kbd>
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => submitDecision("remove")}
                className="w-full px-4 py-3 border border-rose-400/40 text-rose-300 hover:bg-rose-400/10 uppercase tracking-luxe text-[11px] flex items-center justify-between"
              >
                <span>Remove</span>
                <kbd className="text-dim">R</kbd>
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => setEscalateOpen(true)}
                className="w-full px-4 py-3 border border-gold/40 text-gold hover:bg-gold/10 uppercase tracking-luxe text-[11px] flex items-center justify-between"
              >
                <span>Escalate</span>
                <kbd className="text-dim">E</kbd>
              </button>
            </div>
          </div>

          <div>
            <label className="ey mb-2 block">Template (T)</label>
            <select
              ref={templateRef}
              value={selectedTemplate}
              onChange={(e) => {
                setSelectedTemplate(e.target.value);
                const t = templates.find((tt) => tt.slug === e.target.value);
                if (t) setReason(t.default_reason);
              }}
              className="w-full bg-warm/40 border border-gold/22 text-ivory px-3 py-2 text-sm"
            >
              <option value="">— Custom reason —</option>
              {templates.map((t) => (
                <option key={t.slug} value={t.slug}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="ey mb-2 block">Reason (optional)</label>
            <textarea
              ref={reasonRef}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              maxLength={300}
              placeholder="Add context for the audit log..."
              className="w-full bg-warm/40 border border-gold/22 text-ivory px-3 py-2 text-sm font-mono"
            />
          </div>

          <div className="pt-4 border-t border-gold/14 space-y-2">
            <button
              type="button"
              onClick={fetchNext}
              disabled={busy}
              className="w-full px-3 py-2 text-[11px] uppercase tracking-luxe text-mist hover:text-gold-hi"
            >
              Skip without action (N)
            </button>
            <button
              type="button"
              onClick={() => setInvestigateOpen(true)}
              className="w-full px-3 py-2 text-[11px] uppercase tracking-luxe text-mist hover:text-gold-hi"
            >
              Investigate author (I)
            </button>
          </div>

          {error && (
            <div className="text-rose-300 text-xs border border-rose-400/40 bg-rose-400/10 p-3">
              {error}
            </div>
          )}
        </aside>
      </div>

      {/* Keyboard hints — hidden on touch where keyboard shortcuts don't apply */}
      <div className="hidden sm:flex text-[10px] uppercase tracking-luxe text-dim border-t border-gold/14 pt-3 flex-wrap gap-x-6 gap-y-1">
        <span>A approve</span>
        <span>R remove</span>
        <span>E escalate</span>
        <span>T template</span>
        <span>N skip</span>
        <span>I investigate</span>
      </div>

      {/* Escalation modal */}
      {escalateOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-end sm:items-center justify-center p-0 sm:p-6">
          <div className="bg-deep border border-gold/40 sm:max-w-lg w-full p-6 sm:p-8 sheet-mobile sm:!max-w-lg max-h-[90vh] overflow-y-auto safe-bottom sm:!pb-8">
            <div className="ey mb-3">Escalate to operators</div>
            <h3 className="font-serif font-light text-ivory text-xl mb-4">
              Why does this need ops attention?
            </h3>
            <textarea
              value={escalateNotes}
              onChange={(e) => setEscalateNotes(e.target.value)}
              rows={5}
              maxLength={2000}
              autoFocus
              className="w-full bg-warm/40 border border-gold/22 text-ivory px-3 py-2 text-sm mb-4"
              placeholder="Pattern of abuse, edge case, policy ambiguity..."
            />
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3">
              <button
                type="button"
                onClick={() => setEscalateOpen(false)}
                className="px-4 py-3 sm:py-2 border border-gold/22 text-mist uppercase tracking-luxe text-[11px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() =>
                  submitDecision("escalate", undefined, escalateNotes)
                }
                disabled={busy || escalateNotes.length === 0}
                className="px-4 py-3 sm:py-2 border border-gold/40 text-gold uppercase tracking-luxe text-[11px] hover:bg-gold/10 disabled:opacity-50"
              >
                Send to ops
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Investigate drawer */}
      {investigateOpen && (
        <InvestigateDrawer
          authorIdHint={null}
          targetType={item.target_type}
          targetId={item.target_id}
          onClose={() => setInvestigateOpen(false)}
        />
      )}
    </div>
  );
}
