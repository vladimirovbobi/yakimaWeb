import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function VendorDashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/vendor");

  return (
    <ComingSoon
      eyebrow="Vendor"
      title="Manage your services."
      sprint="Sprint 4"
      body="The full vendor surface - services, packages, bundles, leads, reviews - lands in Sprint 4."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
