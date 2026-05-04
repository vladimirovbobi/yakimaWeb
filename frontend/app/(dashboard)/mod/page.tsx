import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function ModDashboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/mod");
  if (!user.is_staff) redirect("/dashboard");

  return (
    <ComingSoon
      eyebrow="Moderation"
      title="Investigate and decide."
      sprint="Sprint 5"
      body="Pipeline decisions, prompt-injection rejections, ban / shadowban controls, audit trail. Lands in Sprint 5."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
