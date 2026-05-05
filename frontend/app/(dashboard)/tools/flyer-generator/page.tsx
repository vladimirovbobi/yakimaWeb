import { redirect } from "next/navigation";

import FlyerGeneratorApp from "@/components/tools/FlyerGeneratorApp";
import { getCurrentUser } from "@/lib/auth/server";

export const metadata = {
  title: "Flyer generator",
  description:
    "Pick a design preset, drop in property details and creative copy, get a print-ready PDF flyer in about a minute.",
};

const STEPS = [
  {
    n: "01",
    title: "Pick a style",
    body: "Six curated presets — editorial, minimal, bold, geometric, Swiss, Italian. Each carries its own palette and typography.",
  },
  {
    n: "02",
    title: "Drop the facts + copy",
    body: "Property details, your headline, the callouts that actually matter. We treat your text as data — moderation runs before any LLM call.",
  },
  {
    n: "03",
    title: "Print or share",
    body: "Output is US Letter, print-ready. Output is moderated, no script tags, no surprises.",
  },
];

const FACTS = [
  { label: "Daily limit (member)", value: "3 runs" },
  { label: "Daily limit (verified realtor)", value: "20 runs" },
  { label: "Per-run cost", value: "$0 (prototype)" },
  { label: "Avg runtime", value: "60-180s" },
];

export default async function FlyerGeneratorPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/tools/flyer-generator");

  return (
    <div className="max-w-6xl space-y-12">
      <header className="space-y-3">
        <div className="ey text-gold">AI tool</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3rem)] leading-[1.05]">
          Flyer generator.
        </h1>
        <p className="text-mist max-w-2xl leading-relaxed text-base md:text-lg">
          A printable flyer in about a minute. Six design philosophies — pick
          one, drop in the property, ship the PDF to print or social.
        </p>
      </header>

      <FlyerGeneratorApp />

      <section className="space-y-4" aria-labelledby="how-it-works">
        <div className="ey text-gold">How it works</div>
        <h2
          id="how-it-works"
          className="font-serif text-ivory text-2xl md:text-3xl"
        >
          Three steps. Print-ready.
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="border border-gold/22 bg-panel p-6 space-y-2"
            >
              <div className="ey text-gold-dim">{s.n}</div>
              <div className="font-serif text-ivory text-lg">{s.title}</div>
              <p className="text-mist text-sm leading-relaxed">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="facts">
        <h2 id="facts" className="font-serif text-ivory text-xl md:text-2xl">
          Limits + cost
        </h2>
        <div className="border border-gold/22 bg-panel p-6 grid gap-3 sm:grid-cols-2 text-sm">
          {FACTS.map((f) => (
            <div
              key={f.label}
              className="flex items-center justify-between gap-4"
            >
              <span className="text-dim">{f.label}</span>
              <span className="text-ivory">{f.value}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
