import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import ComingSoon from "@/components/dashboard/ComingSoon";

export default async function FurnitureRemoverPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/tools/furniture-remover");

  return (
    <ComingSoon
      eyebrow="AI tool"
      title="Furniture remover."
      sprint="Sprint 3"
      body="Drop a photo of a furnished room. Get back a clean shell, ready for staging or a vacant tour. Full upload + Celery job + result viewer lands in Sprint 3."
      back={{ label: "Back to dashboard", href: "/dashboard" }}
    />
  );
}
