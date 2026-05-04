"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { useAutosave } from "./useAutosave";
import type { AutosaveState } from "./useAutosave";

export interface BusinessData {
  name: string;
  tagline: string;
  website: string;
  contact_phone: string;
  about: string;
}

interface Props {
  initial?: Partial<BusinessData>;
  onSaveStateChange?: (s: AutosaveState) => void;
}

const TAGLINE_LIMIT = 160;
const ABOUT_MIN = 500;
const ABOUT_MAX = 2000;

export default function BusinessInfoStep({
  initial = {},
  onSaveStateChange,
}: Props) {
  const router = useRouter();
  const [data, setData] = useState<BusinessData>({
    name: initial.name || "",
    tagline: initial.tagline || "",
    website: initial.website || "",
    contact_phone: initial.contact_phone || "",
    about: initial.about || "",
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { state, schedule, flush } = useAutosave<BusinessData>({
    onSave: async (value) => {
      await apiFetch(
        "/api/v1/vendors/onboard/business/",
        {
          method: "PATCH",
          body: JSON.stringify({
            business_name: value.name,
            tagline: value.tagline,
            website: value.website,
            contact_phone: value.contact_phone,
            about: value.about,
          }),
        },
        { auth: true },
      );
    },
  });

  useEffect(() => {
    onSaveStateChange?.(state);
  }, [state, onSaveStateChange]);

  function update<K extends keyof BusinessData>(k: K, v: BusinessData[K]) {
    setData((d) => {
      const next = { ...d, [k]: v };
      schedule(next);
      return next;
    });
  }

  async function continueNext() {
    setError(null);
    if (!data.name.trim()) {
      setError("Business name is required.");
      return;
    }
    if (data.about.length > 0 && data.about.length < ABOUT_MIN) {
      setError(`Tell us a bit more — at least ${ABOUT_MIN} characters.`);
      return;
    }
    setSubmitting(true);
    try {
      await flush(data);
      router.push("/dashboard/vendor/onboard/categories");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSubmitting(false);
    }
  }

  const taglineWarn = data.tagline.length > TAGLINE_LIMIT;

  return (
    <section className="max-w-2xl">
      <h1 className="font-serif text-3xl text-gold mb-2">Your business</h1>
      <p className="text-sm text-mist mb-8">
        The basics buyers see first — make it count.
      </p>
      <div className="space-y-6">
        <Input
          label="Business name"
          required
          value={data.name}
          onChange={(e) => update("name", e.target.value)}
          onBlur={() => flush(data)}
          placeholder="Cascade Photography"
          maxLength={200}
        />
        <Input
          label="Tagline"
          helper={`${data.tagline.length}/${TAGLINE_LIMIT}${taglineWarn ? " — over limit" : ""}`}
          error={taglineWarn ? "Tagline is too long." : undefined}
          value={data.tagline}
          onChange={(e) => update("tagline", e.target.value)}
          onBlur={() => flush(data)}
          placeholder="Sharp listings. Faster sales."
        />
        <Input
          label="Website"
          type="url"
          inputMode="url"
          autoComplete="url"
          autoCapitalize="none"
          spellCheck={false}
          value={data.website}
          onChange={(e) => update("website", e.target.value)}
          onBlur={() => flush(data)}
          placeholder="https://yourwebsite.com"
        />
        <Input
          label="Contact phone"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          value={data.contact_phone}
          onChange={(e) => update("contact_phone", e.target.value)}
          onBlur={() => flush(data)}
          placeholder="(509) 555-0123"
        />
        <div>
          <label
            htmlFor="about"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            What do you do?
          </label>
          <textarea
            id="about"
            value={data.about}
            onChange={(e) => update("about", e.target.value)}
            onBlur={() => flush(data)}
            rows={6}
            maxLength={ABOUT_MAX}
            placeholder="Tell buyers what you do best, your style, and what makes you different."
            className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          <p className="mt-1.5 text-xs text-mist">
            {data.about.length}/{ABOUT_MAX} (markdown supported)
          </p>
        </div>
        {error && (
          <p role="alert" className="text-xs text-err">
            {error}
          </p>
        )}
        <div className="pt-4 flex justify-end">
          <Button
            type="button"
            variant="solid"
            loading={submitting}
            onClick={continueNext}
            className="w-full sm:w-auto"
          >
            Continue
          </Button>
        </div>
      </div>
    </section>
  );
}
