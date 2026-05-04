import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function DescriptionWriterPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/tools/description-writer");

  return (
    <ComingSoon
      eyebrow="AI tool"
      title="Description writer."
      sprint="Sprint 3"
      body="Paste listing details, pick a voice (factual / warm / punchy), get a Fair-Housing-checked draft in seconds. Lands in Sprint 3."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
