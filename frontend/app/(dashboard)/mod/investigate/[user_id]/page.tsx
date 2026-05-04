import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { InvestigateUserResult } from "@/lib/api/types";

export default async function InvestigateUserPage(props: {
  params: Promise<{ user_id: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (!user.is_staff) redirect("/dashboard");

  const { user_id } = await props.params;
  const data = await safeServerFetch<InvestigateUserResult>(
    `/api/v1/mod/investigate/${encodeURIComponent(user_id)}/`,
    { method: "GET" },
    { auth: true },
  );

  if (!data) {
    return (
      <div className="max-w-4xl">
        <h1 className="font-serif font-light text-ivory text-3xl">
          User not found
        </h1>
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      <div className="ey mb-3">Investigation</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-2">
        {data.user.display_name}
      </h1>
      <p className="text-mist">{data.user.email}</p>

      <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Account age" value={`${data.account_age_days}d`} />
        <Stat label="Warnings" value={data.total_warnings} />
        <Stat label="Posts (24h)" value={data.post_count_24h} />
        <Stat label="Decisions (30d)" value={data.recent_decision_count_30d} />
      </div>

      {data.pattern_signals.length > 0 && (
        <section className="mt-10">
          <div className="ey mb-3">Pattern signals</div>
          <div className="flex flex-wrap gap-2">
            {data.pattern_signals.map((s) => (
              <span
                key={s}
                className="px-3 py-2 border border-rose-400/40 bg-rose-400/10 text-rose-300 text-[11px] uppercase tracking-luxe"
              >
                {s.replaceAll("_", " ")}
              </span>
            ))}
          </div>
        </section>
      )}

      <div className="mt-10 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title="Recent posts" items={data.recent_posts} />
        <Section title="Recent comments" items={data.recent_comments} />
        <Section title="Forum threads" items={data.recent_threads} />
        <Section title="Forum replies" items={data.recent_replies} />
      </div>

      {data.recent_flags_against.length > 0 && (
        <section className="mt-10">
          <div className="ey mb-3">Flags against</div>
          <ul className="space-y-2">
            {data.recent_flags_against.map((f) => (
              <li
                key={f.id}
                className="border border-gold/22 p-3 text-sm text-mist"
              >
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  {f.reason_category} • by {f.reporter.display_name} •{" "}
                  {new Date(f.created_at).toLocaleString()}
                </div>
                <div>{f.reason_text}</div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {data.recent_decisions.length > 0 && (
        <section className="mt-10">
          <div className="ey mb-3">Mod decisions</div>
          <ul className="space-y-2">
            {data.recent_decisions.map((d) => (
              <li
                key={d.id}
                className="border border-gold/22 p-3 text-sm text-mist"
              >
                <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
                  {d.action} • severity {d.severity ?? "—"} •{" "}
                  {d.target_type} #{d.target_id}
                </div>
                <div className="truncate">{d.target_excerpt}</div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border border-gold/22 bg-panel p-5">
      <div className="text-[10px] uppercase tracking-luxe text-dim">{label}</div>
      <div className="font-serif text-ivory text-2xl mt-1">{value}</div>
    </div>
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
  if (items.length === 0) return null;
  return (
    <section>
      <div className="ey mb-2">
        {title} ({items.length})
      </div>
      <ul className="space-y-2">
        {items.map((it) => (
          <li
            key={it.id}
            className="border border-gold/22 p-3 text-sm text-mist"
          >
            <div className="text-[10px] uppercase tracking-luxe text-dim mb-1">
              {it.moderation_status || "—"}
            </div>
            <div className="truncate">{it.excerpt || "(no excerpt)"}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
