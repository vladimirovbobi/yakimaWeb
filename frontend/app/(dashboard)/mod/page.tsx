import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { ModeratorStats, Pagination, QueueItem } from "@/lib/api/types";

export default async function ModDashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/mod");
  if (!user.is_staff) redirect("/dashboard");

  const [stats, queueDepthResp] = await Promise.all([
    safeServerFetch<ModeratorStats>(
      "/api/v1/mod/stats/",
      { method: "GET" },
      { auth: true },
    ),
    safeServerFetch<Pagination<QueueItem>>(
      "/api/v1/mod/queue/?limit=1",
      { method: "GET" },
      { auth: true },
    ),
  ]);

  const depth = queueDepthResp?.count ?? queueDepthResp?.results?.length ?? 0;

  return (
    <div className="max-w-5xl">
      <div className="ey mb-3">Moderation</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-2">
        Investigate, decide, ship.
      </h1>
      <p className="text-mist mt-2">
        Three-layer pipeline status, your stats, and quick links.
      </p>

      <div className="mt-10 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Today"
          value={stats?.items_reviewed_7d ?? 0}
          subtitle="reviewed (7d)"
        />
        <StatCard
          label="30 days"
          value={stats?.items_reviewed_30d ?? 0}
          subtitle="reviewed"
        />
        <StatCard
          label="Agreement"
          value={`${Math.round((stats?.agreement_rate ?? 0) * 100)}%`}
          subtitle="with AI"
        />
        <StatCard
          label="Avg pace"
          value={`${stats?.avg_response_minutes?.toFixed?.(1) ?? "0.0"}m`}
          subtitle="per item"
        />
      </div>

      <div className="mt-10 border border-gold/22 bg-deep p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="ey mb-1">Queue depth</div>
            <div className="text-3xl font-serif text-ivory">{depth}</div>
          </div>
          <Link
            href="/dashboard/mod/queue"
            className="px-5 py-3 border border-gold/40 text-gold uppercase tracking-luxe text-[11px] hover:bg-gold/10"
          >
            Open queue →
          </Link>
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <QuickLink
          title="My stats"
          body="Sparklines, reversal rate, current streak."
          href="/dashboard/mod/stats"
        />
        <QuickLink
          title="Investigate user"
          body="Composite dossier — posts, flags, mod history."
          href="/dashboard/mod/investigate"
        />
        <QuickLink
          title="Escalations"
          body="Operator-only inbox of escalated items."
          href="/dashboard/mod/escalations"
        />
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  subtitle,
}: {
  label: string;
  value: string | number;
  subtitle: string;
}) {
  return (
    <div className="border border-gold/22 bg-panel p-5">
      <div className="text-[10px] uppercase tracking-luxe text-dim">{label}</div>
      <div className="font-serif text-ivory text-3xl mt-1">{value}</div>
      <div className="text-[11px] text-mist uppercase tracking-luxe mt-1">
        {subtitle}
      </div>
    </div>
  );
}

function QuickLink({
  title,
  body,
  href,
}: {
  title: string;
  body: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="block border border-gold/22 bg-panel p-6 hover:border-gold/40 transition"
    >
      <div className="font-serif text-ivory text-lg mb-2">{title}</div>
      <p className="text-mist text-sm">{body}</p>
    </Link>
  );
}
