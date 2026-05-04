import { redirect } from "next/navigation";

import ImageCompressorApp from "@/components/tools/ImageCompressorApp";
import FeaturedServices from "@/components/marketing/FeaturedServices";
import { getCurrentUser } from "@/lib/auth/server";

export const metadata = {
  title: "Lossless image compressor",
  description:
    "Shrink listing photos without losing a pixel of quality. JPG, PNG, WebP, HEIC, TIFF, GIF, BMP supported. Up to 50 MB per file.",
};

const STEPS = [
  {
    n: "01",
    title: "Drag in your photos",
    body:
      "JPG, PNG, WebP, HEIC, TIFF, GIF, BMP — up to 50 MB each, batch of any size.",
  },
  {
    n: "02",
    title: "We re-encode losslessly",
    body:
      "JPEG keeps its original quantization tables; PNG/WebP/GIF run optimized; HEIC converts to lossless WebP. Pixel-identical to your input.",
  },
  {
    n: "03",
    title: "Download — or send via delivery",
    body:
      "Per-file download links or grab the whole batch. Vendors can attach the compressed set directly to a buyer delivery package.",
  },
];

const FACTS = [
  { label: "Max per file", value: "50 MB" },
  { label: "Daily limit (member)", value: "30 runs" },
  { label: "Daily limit (verified realtor)", value: "300 runs" },
  { label: "Cost", value: "Free" },
  { label: "Avg runtime", value: "2-5s" },
  { label: "Pixel quality loss", value: "0% — fully lossless" },
];

export default async function ImageCompressorPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/tools/image-compressor");

  return (
    <div className="max-w-5xl space-y-12">
      <header className="space-y-3">
        <div className="ey text-gold">Lead magnet</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4.5vw,3rem)] leading-[1.05]">
          Lossless image compressor.
        </h1>
        <p className="text-mist max-w-2xl leading-relaxed text-base md:text-lg">
          Smaller files. Same pixels. Your listing photos load faster on every
          MLS, every social post, every email. JPG, PNG, WebP, HEIC, TIFF, GIF,
          and BMP — drop a batch and pull them back compressed.
        </p>
      </header>

      <ImageCompressorApp />

      <section className="space-y-4" aria-labelledby="how-it-works">
        <div className="ey text-gold">How it works</div>
        <h2
          id="how-it-works"
          className="font-serif text-ivory text-2xl md:text-3xl"
        >
          Three steps. No quality loss. Ever.
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
          Facts
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

      <FeaturedServices
        contextKind="tool/image-compressor"
        seedKey="image-compressor"
        limit={2}
        heading="Need it shot before you compress it?"
        subheading="Local photographers + stagers your colleagues already trust."
      />
    </div>
  );
}
