import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { RealtorProfile } from "@/lib/api/types";
import Badge from "@/components/ui/Badge";
import { Card, CardBody } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils";

export default async function RealtorPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/realtor");

  const profile = await safeServerFetch<RealtorProfile>(
    "/api/v1/me/realtor/",
    {},
    { auth: true },
  );

  return (
    <div className="max-w-4xl">
      <div className="ey mb-3">Realtor</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight mb-8">
        Your license and profile
      </h1>

      {profile ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card hover={false}>
            <CardBody>
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-serif text-xl text-ivory">License</h2>
                {profile.is_verified ? (
                  <Badge tone="verified">Verified</Badge>
                ) : (
                  <Badge tone="pending">Pending</Badge>
                )}
              </div>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-mist">Number</dt>
                  <dd className="text-ivory font-mono">
                    {profile.license_number}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-mist">State</dt>
                  <dd className="text-ivory">{profile.license_state}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-mist">Verified at</dt>
                  <dd className="text-ivory">
                    {profile.verified_at
                      ? formatDate(profile.verified_at)
                      : "Not yet"}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-mist">Brokerage</dt>
                  <dd className="text-ivory">{profile.brokerage || "-"}</dd>
                </div>
              </dl>
            </CardBody>
          </Card>

          <Card hover={false}>
            <CardBody>
              <h2 className="font-serif text-xl text-ivory mb-4">Profile</h2>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-mist text-[11px] uppercase tracking-luxe mb-1">
                    Display name
                  </dt>
                  <dd className="text-ivory">{profile.display_name}</dd>
                </div>
                <div>
                  <dt className="text-mist text-[11px] uppercase tracking-luxe mb-1">
                    Bio
                  </dt>
                  <dd className="text-ivory text-sm leading-relaxed">
                    {profile.bio || (
                      <span className="text-dim italic">No bio yet.</span>
                    )}
                  </dd>
                </div>
              </dl>
              <Link
                href="/dashboard/realtor/edit"
                className="inline-flex items-center gap-2 text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi mt-6"
              >
                Edit profile
              </Link>
            </CardBody>
          </Card>
        </div>
      ) : (
        <div className="border border-gold/22 bg-deep p-8 max-w-2xl">
          <h2 className="font-serif text-2xl text-ivory mb-3">
            Verify your license
          </h2>
          <p className="text-mist text-sm leading-relaxed mb-5">
            We verify your license through ARELLO before showing the verified
            pip on your profile. It takes a minute.
          </p>
          <Link
            href="/dashboard/realtor/verify"
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
          >
            Start verification
          </Link>
        </div>
      )}
    </div>
  );
}
