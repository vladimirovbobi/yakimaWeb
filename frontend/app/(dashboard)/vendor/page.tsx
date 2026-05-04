import { redirect } from "next/navigation";
import Link from "next/link";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import Button from "@/components/ui/Button";

interface MyVendor {
  business_name?: string;
  status?: "draft" | "active" | "suspended";
  submitted_at?: string;
  current_step?: string;
  wizard_state?: {
    current_step?: string;
    completed_steps?: string[];
  };
}

export default async function VendorDashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ just_submitted?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/vendor");

  const params = await searchParams;
  const me = await safeServerFetch<MyVendor>(
    "/api/v1/me/vendor/",
    {},
    { auth: true },
  );
  const justSubmitted = params.just_submitted === "1";

  // No vendor profile at all → guide to onboarding.
  if (!me?.business_name) {
    return (
      <div className="max-w-2xl">
        <p className="text-[11px] uppercase tracking-luxe text-gold mb-3">
          Vendor
        </p>
        <h1 className="font-serif text-3xl text-ivory mb-4">
          Get listed in the marketplace.
        </h1>
        <p className="text-mist mb-8">
          A 5-step wizard takes about 10 minutes. Buyers can find and message
          you within 24 hours of approval.
        </p>
        <Button href="/dashboard/vendor/onboard" variant="solid">
          Start onboarding
        </Button>
      </div>
    );
  }

  const isPending = me.status === "draft" || justSubmitted;
  const isActive = me.status === "active";

  return (
    <div className="max-w-3xl">
      <p className="text-[11px] uppercase tracking-luxe text-gold mb-3">
        Vendor
      </p>
      <div className="flex items-center justify-between gap-4 mb-2">
        <h1 className="font-serif text-3xl text-ivory">
          {me.business_name}
        </h1>
        <StatusPill
          label={
            isActive
              ? "Active"
              : isPending
                ? "Under review"
                : (me.status || "Unknown")
          }
          tone={isActive ? "ok" : isPending ? "warn" : "off"}
        />
      </div>

      {isPending && (
        <div className="border border-gold/30 bg-warm/40 rounded-md p-4 mb-8">
          <p className="text-sm text-ivory">
            Your application is under review. Most vendors are approved within 24 hours.
          </p>
        </div>
      )}

      <ul className="grid sm:grid-cols-2 gap-4">
        <DashTile
          href="/dashboard/vendor/leads"
          title="Leads"
          subtitle="Manage buyer inquiries"
        />
        <DashTile
          href="/dashboard/vendor/onboard"
          title="Edit profile"
          subtitle="Update services + gallery"
        />
      </ul>

      <p className="mt-10 text-xs text-mist">
        <Link href="/dashboard" className="underline">
          Back to dashboard
        </Link>
      </p>
    </div>
  );
}

function StatusPill({
  label,
  tone,
}: {
  label: string;
  tone: "ok" | "warn" | "off";
}) {
  const map = {
    ok: "border-emerald-500/40 text-emerald-300",
    warn: "border-gold/40 text-gold",
    off: "border-mist/30 text-mist",
  } as const;
  return (
    <span
      className={`px-3 py-1 text-[10px] uppercase tracking-luxe border rounded-full ${map[tone]}`}
    >
      {label}
    </span>
  );
}

function DashTile({
  href,
  title,
  subtitle,
}: {
  href: string;
  title: string;
  subtitle: string;
}) {
  return (
    <li>
      <Link
        href={href}
        className="block border border-gold/14 hover:border-gold/40 bg-panel/40 p-5 rounded-md transition-colors"
      >
        <p className="font-serif text-xl text-ivory mb-1">{title}</p>
        <p className="text-xs text-mist">{subtitle}</p>
      </Link>
    </li>
  );
}
