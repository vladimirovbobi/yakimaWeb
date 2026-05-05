import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import EmptyState from "@/components/layout/EmptyState";
import LeadCard, {
  type LeadCardData,
} from "@/components/vendor/leads/LeadCard";

const STATUSES = ["all", "pending", "contacted", "won", "lost"] as const;

export default async function VendorLeadsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/vendor/leads");

  const params = await searchParams;
  const status = params.status && STATUSES.includes(params.status as typeof STATUSES[number])
    ? params.status
    : "all";

  const qs = new URLSearchParams({ as: "vendor" });
  if (status !== "all") qs.set("status", status);

  const data = await safeServerFetch<{ results?: LeadCardData[] } | LeadCardData[]>(
    `/api/v1/leads/me/?${qs.toString()}`,
    {},
    { auth: true },
  );
  const results: LeadCardData[] = Array.isArray(data)
    ? data
    : data?.results || [];

  return (
    <div className="max-w-4xl">
      <p className="text-[11px] uppercase tracking-luxe text-gold mb-3">
        Vendor leads
      </p>
      <h1 className="font-serif text-3xl text-ivory mb-6">Buyer inquiries</h1>

      <ul className="flex flex-wrap gap-2 mb-8">
        {STATUSES.map((s) => (
          <li key={s}>
            <Link
              href={`/dashboard/vendor/leads${s === "all" ? "" : `?status=${s}`}`}
              className={
                "px-3 py-1.5 text-[11px] uppercase tracking-luxe rounded-full border " +
                (status === s
                  ? "bg-gold text-black border-gold"
                  : "border-gold/30 text-mist hover:border-gold hover:text-gold")
              }
            >
              {s}
            </Link>
          </li>
        ))}
      </ul>

      {results.length === 0 ? (
        <EmptyState
          kind="leads"
          title={status === "all" ? "No leads yet" : `No "${status}" leads`}
          body={status === "all"
            ? "When buyers reach out about your services, their inquiries will land here."
            : "Try a different status filter to see leads in another stage."}
          action={status === "all"
            ? undefined
            : { label: "Show all leads", href: "/dashboard/vendor/leads" }}
        />
      ) : (
        <ul className="grid gap-4">
          {results.map((lead) => (
            <li key={lead.id}>
              <LeadCard lead={lead} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
