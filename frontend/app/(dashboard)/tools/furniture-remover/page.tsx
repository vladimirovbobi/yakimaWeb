import { redirect } from "next/navigation";

import FurnitureRemoverApp from "@/components/tools/FurnitureRemoverApp";
import FeaturedServices from "@/components/marketing/FeaturedServices";
import { getCurrentUser } from "@/lib/auth/server";

export const metadata = {
  title: "Furniture Remover · Yakima Real Estate Hub",
  description:
    "Drop a photo of a furnished room. Get an empty-room version back in 30 seconds — perfect for staging mockups and clean buyer renders.",
};

const STEPS = [
  {
    n: "01",
    title: "Upload a room photo",
    body:
      "JPG or PNG, up to 10 MB. Wide angles work best. Skip photos with faces or signage.",
  },
  {
    n: "02",
    title: "Wait ~30 seconds",
    body:
      "Our pipeline runs Gemini 2.5 Pro to map the furniture, then Gemini 2.5 Flash Image to inpaint a clean shell.",
  },
  {
    n: "03",
    title: "Download or re-stage",
    body:
      "You get an empty room you can hand to your stager, your buyer, or your render artist.",
  },
];

const SAMPLES = [
  {
    label: "Living room",
    before: "/img/samples/furniture-remover/living-before.jpg",
    after: "/img/samples/furniture-remover/living-after.jpg",
  },
  {
    label: "Bedroom",
    before: "/img/samples/furniture-remover/bedroom-before.jpg",
    after: "/img/samples/furniture-remover/bedroom-after.jpg",
  },
  {
    label: "Dining",
    before: "/img/samples/furniture-remover/dining-before.jpg",
    after: "/img/samples/furniture-remover/dining-after.jpg",
  },
];

export default async function FurnitureRemoverPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/tools/furniture-remover");

  return (
    <div className="max-w-5xl space-y-12">
      <header className="space-y-3">
        <div className="ey text-gold">AI tool</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3rem)] leading-[1.05]">
          Furniture remover.
        </h1>
        <p className="text-mist max-w-2xl leading-relaxed text-base md:text-lg">
          Drop a photo of a furnished room. We empty it — same lighting, same
          architecture, no people, no decor — so buyers can imagine their own
          life inside.
        </p>
      </header>

      <FurnitureRemoverApp />

      <section className="space-y-4" aria-labelledby="how-it-works">
        <div className="ey text-gold">How it works</div>
        <h2
          id="how-it-works"
          className="font-serif text-ivory text-2xl md:text-3xl"
        >
          From cluttered to clean in three moves.
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

      <section className="space-y-4" aria-labelledby="rate-limits">
        <h2
          id="rate-limits"
          className="font-serif text-ivory text-xl md:text-2xl"
        >
          Limits + cost
        </h2>
        <div className="border border-gold/22 bg-panel p-6 grid gap-3 sm:grid-cols-2 text-sm">
          <div className="flex items-center justify-between gap-4">
            <span className="text-dim">Daily limit (member)</span>
            <span className="text-ivory">10 runs</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-dim">Daily limit (verified realtor)</span>
            <span className="text-ivory">100 runs</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-dim">Per-run cost</span>
            <span className="text-ivory">~$0.04</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-dim">Avg runtime</span>
            <span className="text-ivory">25-40s</span>
          </div>
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="samples">
        <div className="ey text-gold">Sample runs</div>
        <h2 id="samples" className="font-serif text-ivory text-xl md:text-2xl">
          Before and after.
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          {SAMPLES.map((s) => (
            <figure
              key={s.label}
              className="space-y-2 border border-gold/22 bg-panel p-3"
            >
              <div className="grid grid-cols-2 gap-1 bg-black">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={s.before}
                  alt={`${s.label} before`}
                  className="aspect-[4/3] object-cover w-full"
                  loading="lazy"
                />
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={s.after}
                  alt={`${s.label} after`}
                  className="aspect-[4/3] object-cover w-full"
                  loading="lazy"
                />
              </div>
              <figcaption className="ey text-mist">{s.label}</figcaption>
            </figure>
          ))}
        </div>
      </section>

      <FeaturedServices
        contextKind="tool/furniture-remover"
        seedKey="furniture-remover"
        limit={2}
        heading="Want a stager to take it the rest of the way?"
        subheading="Local stagers who pair well with our virtual prep tools."
      />
    </div>
  );
}
