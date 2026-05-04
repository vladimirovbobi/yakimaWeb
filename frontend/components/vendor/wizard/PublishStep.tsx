"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import type { ServiceFormData } from "./ServiceFormCard";
import type { UploadedImage } from "./ImageUploader";

export interface PublishSummary {
  business?: {
    name?: string;
    tagline?: string;
    website?: string;
    contact_phone?: string;
    about?: string;
  };
  categories?: string[];
  services?: ServiceFormData[];
  gallery?: UploadedImage[];
}

interface Props {
  data: PublishSummary;
}

export default function PublishStep({ data }: Props) {
  const router = useRouter();
  const [accept, setAccept] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!accept) {
      setError("You must accept the terms to submit.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await apiFetch(
        "/api/v1/vendors/onboard/publish/",
        {
          method: "POST",
          body: JSON.stringify({ accept_terms: true }),
        },
        { auth: true },
      );
      router.push("/dashboard/vendor?just_submitted=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="max-w-3xl">
      <h1 className="font-serif text-3xl text-gold mb-2">Review & submit</h1>
      <div className="bg-warm/40 border border-gold/30 p-4 rounded-md mb-8">
        <p className="text-xs text-ivory">
          Submission goes to admin review. Most vendors are approved within 24 hours.
        </p>
      </div>

      <div className="space-y-6">
        <Group title="Business">
          <Row label="Name" value={data.business?.name || "—"} />
          <Row label="Tagline" value={data.business?.tagline || "—"} />
          <Row label="Website" value={data.business?.website || "—"} />
          <Row label="Phone" value={data.business?.contact_phone || "—"} />
          <Row
            label="About"
            value={
              data.business?.about ? data.business.about.slice(0, 240) : "—"
            }
          />
        </Group>
        <Group title="Categories">
          <p className="text-sm text-ivory">
            {data.categories && data.categories.length > 0
              ? data.categories.join(", ")
              : "None"}
          </p>
        </Group>
        <Group title="Services">
          <ul className="space-y-1 text-sm text-ivory">
            {(data.services || []).map((s, i) => (
              <li key={i}>
                {s.title || `Service ${i + 1}`} —{" "}
                {s.packages.length} packages
              </li>
            ))}
            {(!data.services || data.services.length === 0) && (
              <li className="text-mist">None added.</li>
            )}
          </ul>
        </Group>
        <Group title="Gallery">
          <p className="text-sm text-ivory">
            {(data.gallery || []).length} image
            {(data.gallery || []).length === 1 ? "" : "s"}
          </p>
        </Group>
      </div>

      <label className="mt-8 flex items-start gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={accept}
          onChange={(e) => setAccept(e.target.checked)}
          className="mt-1 accent-gold"
        />
        <span className="text-xs text-mist">
          I confirm everything is accurate and accept the{" "}
          <a className="underline text-gold" href="/legal/terms" target="_blank">
            terms of service
          </a>
          .
        </span>
      </label>

      {error && (
        <p role="alert" className="mt-4 text-xs text-err">
          {error}
        </p>
      )}

      <div className="pt-8 flex justify-between">
        <Button href="/dashboard/vendor/onboard/gallery" variant="ghost">
          Back
        </Button>
        <Button
          type="button"
          variant="solid"
          loading={submitting}
          onClick={submit}
        >
          Submit for review
        </Button>
      </div>
    </section>
  );
}

function Group({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-luxe text-gold mb-2">
        {title}
      </p>
      <div className="border border-gold/14 p-4 rounded-md bg-panel/40">
        {children}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <p className="text-sm text-ivory">
      <span className="text-mist">{label}: </span>
      {value}
    </p>
  );
}
