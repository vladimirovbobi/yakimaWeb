"use client";

import { motion } from "framer-motion";
import { useCallback, useState } from "react";

import { apiFetch } from "@/lib/api/fetch";

interface RunResponse {
  task_id: number;
  status: string;
}

interface TaskStatus {
  task_id: number;
  status: "queued" | "running" | "success" | "failed" | "blocked";
  progress: number;
  result?: { text?: string } | null;
  error?: string;
}

type Tone = "professional" | "friendly" | "luxury";

interface FormState {
  property_type: string;
  beds: number;
  baths: number;
  sqft: number;
  key_features: string;
  tone: Tone;
}

const DEFAULTS: FormState = {
  property_type: "single-family home",
  beds: 3,
  baths: 2,
  sqft: 1800,
  key_features: "",
  tone: "professional",
};

const TONES: { value: Tone; label: string; hint: string }[] = [
  { value: "professional", label: "Professional", hint: "Clean, factual, MLS-default." },
  { value: "friendly",     label: "Warm",        hint: "Conversational, neighborly tone." },
  { value: "luxury",       label: "Luxury",      hint: "Considered, restrained, refined." },
];

export default function DescriptionWriterApp() {
  const [form, setForm] = useState<FormState>(DEFAULTS);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const update = useCallback(
    <K extends keyof FormState>(k: K, v: FormState[K]) =>
      setForm((s) => ({ ...s, [k]: v })),
    [],
  );

  const pollTask = useCallback(async (taskId: number) => {
    const deadline = Date.now() + 90_000;
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 1500));
      try {
        const status = await apiFetch<TaskStatus>(
          `/api/v1/tools/tasks/${taskId}/`,
          {},
          { auth: true },
        );
        if (status.status === "success") {
          setResult(status.result?.text || "(no text returned)");
          setProgress(100);
          return;
        }
        if (status.status === "failed" || status.status === "blocked") {
          setError(status.error || `Task ${status.status}.`);
          setProgress(100);
          return;
        }
        setProgress(Math.max(progress, status.progress || 30));
      } catch {
        // transient — keep polling
      }
    }
    setError("Timed out — please try again.");
  }, [progress]);

  const onSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setBusy(true);
      setResult(null);
      setError(null);
      setProgress(15);
      try {
        const resp = await apiFetch<RunResponse>(
          "/api/v1/tools/description/",
          {
            method: "POST",
            body: JSON.stringify(form),
            headers: { "Content-Type": "application/json" },
          },
          { auth: true },
        );
        setProgress(40);
        await pollTask(resp.task_id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Submission failed.");
      } finally {
        setBusy(false);
      }
    },
    [form, pollTask],
  );

  const onCopy = useCallback(async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
    } catch {
      // ignore
    }
  }, [result]);

  return (
    <section className="space-y-6">
      <form
        onSubmit={onSubmit}
        className="border border-gold/22 bg-panel p-6 md:p-8 grid gap-5"
      >
        <div className="grid sm:grid-cols-2 gap-5">
          <label className="block">
            <span className="label-luxe">Property type</span>
            <input
              type="text"
              value={form.property_type}
              onChange={(e) => update("property_type", e.target.value)}
              className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
              required
              minLength={2}
              maxLength={64}
            />
          </label>
          <label className="block">
            <span className="label-luxe">Tone</span>
            <select
              value={form.tone}
              onChange={(e) => update("tone", e.target.value as Tone)}
              className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
            >
              {TONES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label} — {t.hint}
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
              value={form.beds}
              onChange={(e) => update("beds", parseInt(e.target.value || "0", 10))}
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
              value={form.baths}
              onChange={(e) => update("baths", parseFloat(e.target.value || "0"))}
              className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
            />
          </label>
          <label className="block">
            <span className="label-luxe">Sq ft</span>
            <input
              type="number"
              min={1}
              max={100000}
              value={form.sqft}
              onChange={(e) => update("sqft", parseInt(e.target.value || "0", 10))}
              className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60"
            />
          </label>
        </div>

        <label className="block">
          <span className="label-luxe">Key features (optional)</span>
          <textarea
            value={form.key_features}
            onChange={(e) => update("key_features", e.target.value)}
            rows={4}
            maxLength={1000}
            placeholder="Quartz kitchen, original hardwoods, fenced backyard, walking distance to downtown Yakima..."
            className="mt-2 w-full bg-deep border border-gold/22 px-3 py-2 text-ivory focus:outline-none focus:border-gold/60 leading-relaxed"
          />
        </label>

        <div className="flex items-center justify-between gap-4 pt-2 border-t border-gold/14">
          <p className="text-mist text-xs leading-relaxed max-w-md">
            Output is moderated for Fair Housing compliance before it reaches
            you. ~30 seconds typical runtime.
          </p>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-7 py-3 bg-gold text-black font-medium hover:bg-gold-hi disabled:opacity-50 transition-colors"
          >
            {busy ? "Generating…" : "Generate description"}
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

      {result && (
        <div className="border border-gold/22 bg-panel p-6 md:p-8">
          <div className="flex items-center justify-between mb-4">
            <p className="ey">Draft</p>
            <button
              type="button"
              onClick={onCopy}
              className="text-[11px] uppercase tracking-cap text-gold hover:text-gold-hi transition-colors"
            >
              Copy
            </button>
          </div>
          <p className="text-ivory leading-[1.85] whitespace-pre-wrap">{result}</p>
          <p className="mt-5 pt-4 border-t border-gold/14 text-[11px] uppercase tracking-luxe text-dim">
            Review before publishing. AI assists, you sign off.
          </p>
        </div>
      )}
    </section>
  );
}
