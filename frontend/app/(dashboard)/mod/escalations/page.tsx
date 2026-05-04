import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { Escalation, Pagination } from "@/lib/api/types";

export default async function EscalationsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (!user.is_staff) redirect("/dashboard");

  const data = await safeServerFetch<Pagination<Escalation>>(
    "/api/v1/mod/escalations/",
    { method: "GET" },
    { auth: true },
  );

  const items = data?.results ?? [];

  return (
    <div className="max-w-5xl">
      <div className="ey mb-3">Operator inbox</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-2">
        Escalations
      </h1>
      <p className="text-mist mt-2">
        Items moderators sent up. Operator role required.
      </p>

      <div className="mt-10 space-y-3">
        {items.length === 0 && (
          <p className="text-mist text-sm border border-gold/22 bg-deep p-6">
            No open escalations.
          </p>
        )}
        {items.map((e) => (
          <article
            key={e.id}
            className="border border-gold/22 bg-deep p-5"
          >
            <div className="flex items-center gap-3 mb-2">
              <span className="px-2 py-1 border border-gold/40 text-gold uppercase tracking-luxe text-[10px]">
                {e.target_type}
              </span>
              <span className="px-2 py-1 border border-gold/22 text-mist uppercase tracking-luxe text-[10px]">
                Severity {e.severity ?? "—"}
              </span>
              <span className="text-[10px] uppercase tracking-luxe text-dim">
                by {e.escalated_by.display_name} •{" "}
                {new Date(e.created_at).toLocaleString()}
              </span>
            </div>
            <p className="text-mist text-sm mb-2 truncate">
              {e.target_excerpt}
            </p>
            <p className="text-ivory text-sm whitespace-pre-wrap">{e.notes}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
