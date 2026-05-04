"use client";

import { useState } from "react";
import WizardChrome, {
  type StepKey,
} from "@/components/vendor/wizard/WizardChrome";
import BusinessInfoStep, {
  type BusinessData,
} from "@/components/vendor/wizard/BusinessInfoStep";
import CategoriesStep from "@/components/vendor/wizard/CategoriesStep";
import ServicesStep from "@/components/vendor/wizard/ServicesStep";
import GalleryStep from "@/components/vendor/wizard/GalleryStep";
import PublishStep from "@/components/vendor/wizard/PublishStep";
import type { ServiceFormData } from "@/components/vendor/wizard/ServiceFormCard";
import type { UploadedImage } from "@/components/vendor/wizard/ImageUploader";
import type { AutosaveState } from "@/components/vendor/wizard/useAutosave";

interface Props {
  step: StepKey;
  completed: string[];
  data: Record<string, unknown>;
  profile: BusinessData;
}

export default function StepClient({ step, completed, data, profile }: Props) {
  const [saveState, setSaveState] = useState<AutosaveState>("idle");

  const businessInitial: BusinessData = {
    name: (data.business as { name?: string })?.name || profile.name || "",
    tagline:
      (data.business as { tagline?: string })?.tagline || profile.tagline || "",
    website:
      (data.business as { website?: string })?.website || profile.website || "",
    contact_phone:
      (data.business as { contact_phone?: string })?.contact_phone ||
      profile.contact_phone ||
      "",
    about: (data.business as { about?: string })?.about || profile.about || "",
  };

  return (
    <div className="max-w-5xl mx-auto">
      <WizardChrome
        currentStep={step}
        completedSteps={completed}
        saveState={saveState}
      />

      {step === "business" && (
        <BusinessInfoStep
          initial={businessInitial}
          onSaveStateChange={setSaveState}
        />
      )}

      {step === "categories" && (
        <CategoriesStep
          initial={(data.categories as string[]) || []}
          onSaveStateChange={setSaveState}
        />
      )}

      {step === "services" && (
        <ServicesStep
          initial={(data.services as ServiceFormData[]) || []}
          onSaveStateChange={setSaveState}
        />
      )}

      {step === "gallery" && (
        <GalleryStep
          initial={(data.gallery as UploadedImage[]) || []}
          onSaveStateChange={setSaveState}
        />
      )}

      {step === "publish" && (
        <PublishStep
          data={{
            business: businessInitial as unknown as PublishBusiness,
            categories: (data.categories as string[]) || [],
            services: (data.services as ServiceFormData[]) || [],
            gallery: (data.gallery as UploadedImage[]) || [],
          }}
        />
      )}
    </div>
  );
}

type PublishBusiness = {
  name?: string;
  tagline?: string;
  website?: string;
  contact_phone?: string;
  about?: string;
};
