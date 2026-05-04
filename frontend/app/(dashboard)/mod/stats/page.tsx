import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { ModeratorStats } from "@/lib/api/types";

export default async function ModStatsPage(props: {
  searchParams: Promise<{ user_id?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/mod/stats");
  if (!user.is_staff) redirect("/dashboard");

  const { user_id } = await props.searchParams;
  const path = user_id
    ? `/api/v1/mod/stats/?user_id=${encodeURIComponent(user_id)}`
    : "/api/v1/mod/stats/";

  const stats = await safeServerFetch<ModeratorStats>(
    path,
    { method: "GET" },
    { auth: true },
  );

  if (!stats) {
    return (
      <div className="max-w-5xl">
        <h1 className="font-serif font-light text-ivory text-3xl mb-3">
          Stats unavailable
        </h1>
        <p className="text-mist">Try again or check API health.</p>
      </div>
    );
  }

  const max = Math.max(1, ...stats.timeseries_30d.map((p) => p.count));

  return (
    <div className="max-w-5xl">
      <div className="ey mb-3">Moderator stats</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-2">
        How am I doing?
      </h1>

      <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Big label="Reviewed (30d)" value={stats.items_reviewed_30d} />
        <Big label="Reviewed (7d)" value={stats.items_reviewed_7d} />
        <Big
          label="Agreement"
          value={`${Math.round(stats.agreement_rate * 100)}%`}
        />
        <Big
          label="Reversal"
          value={`${Math.round(stats.reversal_rate * 100)}%`}
        />
        <Big
          label="Avg response"
          value={`${stats.avg_response_minutes.toFixed(1)}m`}
        />
        <Big label="Streak" value={stats.current_streak} />
        <Big label="Rank" value={`#${stats.queue_position}`} />
      </div>

      <div className="mt-10 border border-gold/22 bg-deep p-6">
        <div className="ey mb-4">30-day decisions</div>
        <div className="flex items-end gap-1 h-32">
          {stats.timeseries_30d.length === 0 && (
            <p className="text-mist text-sm">No data yet.</p>
          )}
          {stats.timeseries_30d.map((p) => (
            <div
              key={p.day}
              title={`${p.day}: ${p.count}`}
              className="flex-1 bg-gold/40 hover:bg-gold transition"
              style={{ height: `${(p.count / max) * 100}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Big({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border border-gold/22 bg-panel p-5">
      <div className="text-[10px] uppercase tracking-luxe text-dim">{label}</div>
      <div className="font-serif text-ivory text-2xl mt-1">{value}</div>
    </div>
  );
}
