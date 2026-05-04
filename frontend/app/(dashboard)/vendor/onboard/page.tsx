import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function VendorOnboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/vendor/onboard");

  return (
    <ComingSoon
      eyebrow="Vendor onboarding"
      title="Get listed in the marketplace."
      sprint="Sprint 4"
      body="A 5-step wizard: business info, service area, primary category, sample work, and your first service. Lands in Sprint 4."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
