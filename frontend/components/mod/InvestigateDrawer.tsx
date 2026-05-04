"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api/fetch";
import type { InvestigateUserResult } from "@/lib/api/types";

interface InvestigateDrawerProps {
  /**
   * If provided, fetch dossier directly. If null and (targetType,targetId)
   * given, the backend resolves the author via the target.
   */
  authorIdHint: number | null;
  targetType?: string;
  targetId?: number;
  onClose: () => void;
}

export default function InvestigateDrawer({
  authorIdHint,
  onClose,
}: InvestigateDrawerProps) {
  const [data, setData] = useState<InvestigateUserResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (authorIdHint == null) {
        setError("Author lookup not yet wired for target-based investigation.");
        setLoading(false);
        return;
      }
      try {
        const result = await apiFetch<InvestigateUserResult>(
          `/api/v1/mod/investigate/${authorIdHint}/`,
          { method: "GET" },
          { auth: true },
        );
        if (!cancelled) setData(result);
      } catch {
        if (!cancelled) setError("Failed to load dossier.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [authorIdHint]);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Author investigation"
    >
      <aside
        className="absolute inset-x-0 bottom-0 top-[10vh] sm:top-0 sm:right-0 sm:left-auto sm:bottom-auto sm:h-full w-full sm:max-w-xl bg-deep border-t sm:border-t-0 sm:border-l border-gold/40 overflow-y-auto safe-bottom sm:!pb-0"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4 sm:p-6 border-b border-gold/14 flex items-center justify-between sticky top-0 bg-deep z-10">
          <div className="ey">Investigation</div>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex items-center justify-center min-h-11 px-3 text-mist hover:text-gold-hi text-[11px] uppercase tracking-luxe"
            aria-label="Close investigation"
          >
            Close
          </button>
        </div>

        <div className="p-6 space-y-6">
          {loading && (
            <p className="text-mist text-sm">Loading dossier…</p>
          )}
          {error && (
            <p className="text-rose-300 text-sm border border-rose-400/40 bg-rose-400/10 p-3">
              {error}
            </p>
          )}

          {data && <DossierBody data={data} />}
        </div>
      </aside>
    </div>
  );
}

function DossierBody({ data }: { data: InvestigateUserResult }) {
  return (
    <>
      <section>
        <div className="ey mb-2">User</div>
        <h2 className="font-serif font-light text-ivory text-xl">
          {data.user.display_name}
        </h2>
        <p className="text-mist text-sm">{data.user.email}</p>
        <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-mist">
          <div>
            <span className="text-dim">Account age:</span> {data.account_age_days}d
          </div>
          <div>
            <span className="text-dim">Warnings:</span> {data.total_warnings}
          </div>
          <div>
            <span className="text-dim">Posts/24h:</span> {data.post_count_24h}
          </div>
          <div>
            <span className="text-dim">Decisions/30d:</span>{" "}
            {data.recent_decision_count_30d}
          </div>
        </div>
      </section>

      {data.pattern_signals.length > 0 && (
        <section>
          <div className="ey mb-2">Pattern signals</div>
          <ul className="space-y-1">
            {data.pattern_signals.map((s) => (
              <li
                key={s}
                className="px-3 py-2 border border-rose-400/40 bg-rose-400/10 text-rose-300 text-xs uppercase tracking-luxe"
              >
                {s.replaceAll("_", " ")}
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.recent_posts.length > 0 && (
        <Section title="Recent posts" items={data.recent_posts} />
      )}
      {data.recent_comments.length > 0 && (
        <Section title="Recent comments" items={data.recent_comments} />
      )}
      {data.recent_threads.length > 0 && (
        <Section title="Forum threads" items={data.recent_threads} />
      )}
      {data.recent_replies.length > 0 && (
        <Section title="Forum replies" items={data.recent_replies} />
      )}

      {data.recent_flags_against.length > 0 && (
        <section>
          <div className="ey mb-2">Flags against</div>
          <ul className="space-y-2">
            {data.recent_flags_against.map((f) => (
              <li
                key={f.id}
                className="border border-gold/22 p-3 text-sm text-mist"
              >
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  {f.reason_category} • by {f.reporter.display_name}
                </div>
                <div className="text-mist text-xs">{f.reason_text}</div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.recent_decisions.length > 0 && (
        <section>
          <div className="ey mb-2">Mod decisions</div>
          <ul className="space-y-2">
            {data.recent_decisions.map((d) => (
              <li
                key={d.id}
                className="border border-gold/22 p-3 text-sm text-mist"
              >
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  {d.action} • severity {d.severity ?? "—"}
                </div>
                <div className="text-mist text-xs truncate">
                  {d.target_excerpt}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}

function Section({
  title,
  items,
}: {
  title: string;
  items: Array<{
    id: number;
    excerpt?: string;
    moderation_status?: string;
  }>;
}) {
  return (
    <section>
      <div className="ey mb-2">
        {title} ({items.length})
      </div>
      <ul className="space-y-2">
        {items.slice(0, 5).map((it) => (
          <li
            key={it.id}
            className="border border-gold/22 p-3 text-sm text-mist"
          >
            <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
              {it.moderation_status || "—"}
            </div>
            <div className="text-mist text-xs truncate">
              {it.excerpt || "(no excerpt)"}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
