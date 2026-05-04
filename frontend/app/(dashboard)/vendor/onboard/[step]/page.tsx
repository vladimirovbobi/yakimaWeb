import { notFound, redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import StepClient from "./StepClient";
import { STEPS } from "@/components/vendor/wizard/WizardChrome";

interface MyVendorResponse {
  business_name?: string;
  tagline?: string;
  website?: string;
  contact_phone?: string;
  about?: string;
  current_step?: string;
  completed_steps?: string[];
  wizard_state?: {
    current_step?: string;
    completed_steps?: string[];
    data?: Record<string, unknown>;
  };
}

const VALID = STEPS.map((s) => s.key);

export default async function StepPage({
  params,
}: {
  params: Promise<{ step: string }>;
}) {
  const { step } = await params;
  if (!VALID.includes(step as (typeof VALID)[number])) {
    notFound();
  }

  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=/dashboard/vendor/onboard/${step}`);

  const me = await safeServerFetch<MyVendorResponse>(
    "/api/v1/me/vendor/",
    {},
    { auth: true },
  );

  // If trying to access a later step before completing earlier ones, send back.
  const completed = me?.wizard_state?.completed_steps || me?.completed_steps || [];
  const currentIdx = VALID.indexOf(step as (typeof VALID)[number]);
  if (currentIdx > 0 && !completed.includes("business")) {
    redirect("/dashboard/vendor/onboard/business");
  }

  const wizardData = (me?.wizard_state?.data || {}) as Record<string, unknown>;

  return (
    <StepClient
      step={step as (typeof VALID)[number]}
      completed={completed as string[]}
      data={wizardData}
      profile={{
        name: me?.business_name || "",
        tagline: me?.tagline || "",
        website: me?.website || "",
        contact_phone: me?.contact_phone || "",
        about: me?.about || "",
      }}
    />
  );
}
