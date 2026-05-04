import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";

interface MyVendor {
  current_step?: string;
  wizard_state?: { current_step?: string };
}

export default async function VendorOnboardEntryPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/vendor/onboard");

  const me = await safeServerFetch<MyVendor>(
    "/api/v1/me/vendor/",
    {},
    { auth: true },
  );

  const step =
    me?.wizard_state?.current_step || me?.current_step || "business";
  redirect(`/dashboard/vendor/onboard/${step}`);
}
