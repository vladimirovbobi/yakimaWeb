import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function ModQueuePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/mod/queue");
  if (!user.is_staff) redirect("/dashboard");

  return (
    <ComingSoon
      eyebrow="Moderation"
      title="Review queue."
      sprint="Sprint 5"
      body="Items the AI flagged for human review. Side-by-side view of original content, classifier reasoning, and one-click approve / remove / shadow."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
