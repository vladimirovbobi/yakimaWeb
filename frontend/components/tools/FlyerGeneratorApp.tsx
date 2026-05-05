"use client";

import { motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/api/fetch";
import PresetCard, { type FlyerPresetSummary } from "./PresetCard";

interface RunResponse {
  task_id: number;
  status: string;
}

interface TaskStatus {
  task_id: number;
  status: "queued" | "running" | "success" | "failed" | "blocked";
  progress: number;
  result?: {
    flyer?: {
      preset_slug: string;
      pdf_url: string | null;
      pdf_path: string | null;
      pdf_bytes: number;
      pdf_format: string | null;
    };
  } | null;
  error?: string;
}

interface PropertyInfo {
  address: string;
  price: number;
  beds: number;
  baths: number;
  sqft: number;
  agent_name: string;
  agent_phone: string;
  mls: string;
  property_type: string;
}

interface CreativeText {
  headline: string;
  callouts: string[];
  value_props: string[];
}

const DEFAULT_PROPERTY: PropertyInfo = {
  address: "",
  price: 0,
  beds: 3,
  baths: 2,
  sqft: 1800,
  agent_name: "",
  agent_phone: "",
  mls: "",
  property_type: "single-family home",
};

const DEFAULT_CREATIVE: CreativeText = {
  headline: "",
  callouts: ["", "", ""],
  value_props: ["", "", ""],
};

const PROPERTY_TYPES = [
  "single-family home",
  "townhouse",
  "condo",
  "land",
  "multi-family",
  "luxury estate",
];

const MAX_PHOTOS = 5;
const MIN_PHOTOS = 1;
const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 240_000;

export default function FlyerGeneratorApp() {
  const [presets, setPresets] = useState<FlyerPresetSummary[]>([]);
  const [presetSlug, setPresetSlug] = useState<string>("");
  const [property, setProperty] = useState<PropertyInfo>(DEFAULT_PROPERTY);
  const [creative, setCreative] = useState<CreativeText>(DEFAULT_CREATIVE);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [presetsError, setPresetsError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiFetch<FlyerPresetSummary[]>(
      "/api/public/v1/tools/flyer-generator/presets/",
    )
      .then((data) => {
        if (cancelled) return;
        setPresets(data);
        if (data.length && !presetSlug) setPresetSlug(data[0].slug);
      })
      .catch((err) => {
        if (cancelled) return;
        setPresetsError(
          err instanceof Error ? err.message : "Failed to load presets.",
        );
      });
    return () => {
      cancelled = true;
    };
  }, [presetSlug]);

  const updateProp = useCallback(
    <K extends keyof PropertyInfo>(k: K, v: PropertyInfo[K]) =>
      setProperty((s) => ({ ...s, [k]: v })),
    [],
  );

  const setCallout = (i: number, value: string) =>
    setCreative((s) => {
      const next = s.callouts.slice();
      next[i] = value;
      return { ...s, callouts: next };
    });

  const setValueProp = (i: number, value: string) =>
    setCreative((s) => {
      const next = s.value_props.slice();
      next[i] = value;
      return { ...s, value_props: next };
    });

  async function handleFiles(files: FileList) {
    if (!files.length) return;
    if (photoUrls.length >= MAX_PHOTOS) return;
    setUploading(true);
    setError(null);
    try {
      const fresh: string[] = [];
      for (const file of Array.from(files)) {
        if (photoUrls.length + fresh.length >= MAX_PHOTOS) break;
        const fd = new FormData();
        fd.append("file", file);
        const res = await fetch(
          `${
            process.env.NEXT_PUBLIC_API_BASE_URL || ""
          }/api/v1/uploads/?type=flyer-photo`,
          { method: "POST", body: fd, credentials: "include" },
        );
        if (!res.ok) {
          throw new Error(`Upload failed (${res.status}).`);
        }
        const json: { url?: string } = await res.json();
        if (json.url) fresh.push(json.url);
      }
      setPhotoUrls((prev) => [...prev, ...fresh].slice(0, MAX_PHOTOS));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function removePhoto(i: number) {
    setPhotoUrls((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function poll(taskId: number) {
    const deadline = Date.now() + POLL_TIMEOUT_MS;
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
      try {
        const status = await apiFetch<TaskStatus>(
          `/api/v1/tools/tasks/${taskId}/`,
          {},
          { auth: true },
        );
        if (status.status === "success") {
          setPdfUrl(status.result?.flyer?.pdf_url || null);
          setProgress(100);
          return;
        }
        if (status.status === "failed" || status.status === "blocked") {
          setError(status.error || `Task ${status.status}.`);
          setProgress(100);
          return;
        }
        setProgress((p) => Math.max(p, status.progress || 30));
      } catch {
        // Transient — keep polling.
      }
    }
    setError("Timed out — please try again.");
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!presetSlug) {
      setError("Pick a design style first.");
      return;
    }
    if (photoUrls.length < MIN_PHOTOS) {
      setError("Upload at least one photo.");
      return;
    }
    if (!property.address.trim()) {
      setError("Address is required.");
      return;
    }
    if (property.price <= 0) {
      setError("Price must be greater than zero.");
      return;
    }
    setError(null);
    setPdfUrl(null);
    setBusy(true);
    setProgress(15);
    try {
      const body = {
        preset_slug: presetSlug,
        property_info: property,
        creative_text: {
          headline: creative.headline.trim(),
          callouts: creative.callouts.map((c) => c.trim()).filter(Boolean),
          value_props: creative.value_props.map((v) => v.trim()).filter(Boolean),
        },
        photo_urls: photoUrls,
      };
      const resp = await apiFetch<RunResponse>(
        "/api/v1/tools/flyer-generator/",
        {
          method: "POST",
          body: JSON.stringify(body),
          headers: { "Content-Type": "application/json" },
        },
        { auth: true },
      );
      setProgress(35);
      await poll(resp.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-10">
      {/* Section 1 — Preset gallery */}
      <fieldset className="space-y-5">
        <div className="flex items-baseline justify-between">
          <legend className="ey">Style</legend>
          {presetSlug && (
            <span className="text-mist text-xs">
              Selected:{" "}
              <span className="text-ivory">
                {presets.find((p) => p.slug === presetSlug)?.name}
              </span>
            </span>
          )}
        </div>
        {presetsError ? (
          <div className="border border-err/35 bg-err/10 text-err px-4 py-3 text-sm">
            {presetsError}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {presets.map((preset) => (
              <PresetCard
                key={preset.slug}
                preset={preset}
                selected={presetSlug === preset.slug}
                onSelect={setPresetSlug}
              />
            ))}
          </div>
        )}
      </fieldset>

      <form onSubmit={onSubmit} className="space-y-10">
        {/* Section 2 — Property info */}
        <fieldset className="border border-gold/22 bg-panel p-6 md:p-8 space-y-5">
          <legend className="px-2 ey">Property</legend>
          <div className="grid sm:grid-cols-2 gap-5">
            <label className="block sm:col-span-2">
              <span className="label-luxe">Address</span>
              <input
                type="text"
                value={property.address}
                onChange={(e) => updateProp("address", e.target.value)}
                placeholder="142 Sample St, Yakima WA 98901"
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
                required
                maxLength={200}
              />
            </label>
            <label className="block">
              <span className="label-luxe">Price (USD)</span>
              <input
                type="number"
                min={1}
                value={property.price}
                onChange={(e) =>
                  updateProp("price", parseInt(e.target.value || "0", 10))
                }
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
                required
              />
            </label>
            <label className="block">
              <span className="label-luxe">Property type</span>
              <select
                value={property.property_type}
                onChange={(e) => updateProp("property_type", e.target.value)}
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
              >
                {PROPERTY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="grid sm:grid-cols-3 gap-5">
            <label className="block">
              <span className="label-luxe">Beds</span>
              <input
                type="number"
                min={0}
                max={20}
                value={property.beds}
                onChange={(e) =>
                  updateProp("beds", parseInt(e.target.value || "0", 10))
                }
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
              />
            </label>
            <label className="block">
              <span className="label-luxe">Baths</span>
              <input
                type="number"
                min={0}
                max={20}
                step={0.5}
                value={property.baths}
                onChange={(e) =>
                  updateProp("baths", parseFloat(e.target.value || "0"))
                }
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
              />
            </label>
            <label className="block">
              <span className="label-luxe">Sq ft</span>
              <input
                type="number"
                min={1}
                value={property.sqft}
                onChange={(e) =>
                  updateProp("sqft", parseInt(e.target.value || "0", 10))
                }
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
              />
            </label>
          </div>
          <div className="grid sm:grid-cols-2 gap-5">
            <label className="block">
              <span className="label-luxe">Agent name</span>
              <input
                type="text"
                value={property.agent_name}
                onChange={(e) => updateProp("agent_name", e.target.value)}
                placeholder="Jane Realtor"
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
                maxLength={120}
              />
            </label>
            <label className="block">
              <span className="label-luxe">Agent phone</span>
              <input
                type="tel"
                value={property.agent_phone}
                onChange={(e) => updateProp("agent_phone", e.target.value)}
                placeholder="(509) 555-0142"
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
                maxLength={32}
              />
            </label>
            <label className="block sm:col-span-2">
              <span className="label-luxe">MLS # (optional)</span>
              <input
                type="text"
                value={property.mls}
                onChange={(e) => updateProp("mls", e.target.value)}
                className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
                maxLength={32}
              />
            </label>
          </div>
        </fieldset>

        {/* Section 3 — Creative text */}
        <fieldset className="border border-gold/22 bg-panel p-6 md:p-8 space-y-5">
          <legend className="px-2 ey">Creative copy</legend>
          <label className="block">
            <span className="label-luxe">Headline (≤80 chars)</span>
            <input
              type="text"
              value={creative.headline}
              onChange={(e) =>
                setCreative((s) => ({ ...s, headline: e.target.value }))
              }
              placeholder="Quiet light. North exposure."
              maxLength={80}
              className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
            />
          </label>
          <div className="grid sm:grid-cols-3 gap-5">
            {creative.callouts.map((c, i) => (
              <label key={`callout-${i}`} className="block">
                <span className="label-luxe">Callout {i + 1}</span>
                <input
                  type="text"
                  value={c}
                  onChange={(e) => setCallout(i, e.target.value)}
                  maxLength={60}
                  placeholder={i === 0 ? "Quartz kitchen" : ""}
                  className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
                />
              </label>
            ))}
          </div>
          <div className="grid sm:grid-cols-3 gap-5">
            {creative.value_props.map((v, i) => (
              <label key={`vp-${i}`} className="block">
                <span className="label-luxe">Value prop {i + 1}</span>
                <textarea
                  value={v}
                  onChange={(e) => setValueProp(i, e.target.value)}
                  maxLength={140}
                  rows={2}
                  placeholder={
                    i === 0 ? "Walking distance to downtown Yakima." : ""
                  }
                  className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60 leading-relaxed"
                />
              </label>
            ))}
          </div>
        </fieldset>

        {/* Section 4 — Photos */}
        <fieldset className="border border-gold/22 bg-panel p-6 md:p-8 space-y-5">
          <legend className="px-2 ey">
            Photos ({photoUrls.length}/{MAX_PHOTOS})
          </legend>
          <p className="text-mist text-sm leading-relaxed">
            Upload 1–5 photos. JPG, PNG, or WebP. 10 MB cap each.
          </p>
          {photoUrls.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {photoUrls.map((u, i) => (
                <div
                  key={u}
                  className="relative border border-gold/22 bg-deep aspect-square overflow-hidden"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={u}
                    alt={`Property photo ${i + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => removePhoto(i)}
                    className="absolute top-2 right-2 bg-deep/90 text-ivory text-[10px] uppercase tracking-cap px-2 py-1 hover:bg-err/40"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
          <input
            ref={fileRef}
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => {
              if (e.target.files) handleFiles(e.target.files);
            }}
            disabled={uploading || photoUrls.length >= MAX_PHOTOS}
            className="block text-mist text-sm file:mr-3 file:px-4 file:py-2 file:bg-gold/10 file:border file:border-gold/40 file:text-gold file:uppercase file:tracking-cap file:text-xs file:cursor-pointer"
          />
          {uploading && <p className="text-mist text-xs">Uploading…</p>}
        </fieldset>

        {/* Section 5 — Submit */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
          <p className="text-mist text-xs leading-relaxed max-w-md">
            ~60–180s typical runtime. Output is moderated before it reaches you.
            You can print or share the PDF.
          </p>
          <button
            type="submit"
            disabled={busy || uploading || !presetSlug}
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-7 py-3 bg-gold text-black font-medium hover:bg-gold-hi disabled:opacity-50 transition-colors"
          >
            {busy ? "Designing…" : "Generate flyer"}
          </button>
        </div>
      </form>

      {(busy || progress > 0) && (
        <div className="h-1 bg-warm">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="h-full bg-gold/70"
          />
        </div>
      )}

      {error && (
        <div className="border border-err/35 bg-err/10 text-err px-5 py-4 text-sm">
          {error}
        </div>
      )}

      {pdfUrl && (
        <div className="border border-gold/22 bg-panel p-6 md:p-8 space-y-4">
          <p className="ey">Ready</p>
          <h3 className="font-serif text-3xl text-ivory leading-tight">
            Your flyer is rendered.
          </h3>
          <p className="text-mist text-sm leading-relaxed max-w-2xl">
            The PDF is print-ready at US Letter portrait. Open or download
            below; both options preserve full quality.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 uppercase tracking-cap text-xs px-7 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
            >
              Download PDF
            </a>
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 uppercase tracking-cap text-xs px-7 py-3 border border-gold/40 text-gold hover:border-gold transition-colors"
            >
              Open in new tab
            </a>
          </div>
        </div>
      )}
    </section>
  );
}
