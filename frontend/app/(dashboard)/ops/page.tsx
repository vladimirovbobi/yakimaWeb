import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function OperationsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/ops");
  if (!user.is_staff) redirect("/dashboard");

  return (
    <ComingSoon
      eyebrow="Operations"
      title="Platform health and audit log."
      sprint="Sprint 6"
      body="DAU/MAU, ARELLO check rates, moderation pipeline metrics, audit log search, license expiry alerts. Lands in Sprint 6."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
