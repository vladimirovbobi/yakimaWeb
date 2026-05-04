import type { Metadata } from "next";
import Container from "@/components/layout/Container";

export const metadata: Metadata = {
  title: "Coming May 2026",
  description:
    "Yakima Web — verified-realtor blogs, a vendor marketplace, AI listing tools, and a Yakima Valley community. Launching soon.",
  robots: { index: false, follow: false },
};

export default function ComingSoonPage() {
  return (
    <main className="min-h-screen bg-black text-ivory">
      <section className="section-y flex min-h-screen items-center">
        <Container>
          <div className="mx-auto max-w-2xl text-center">
            <div className="ey mb-6">Yakima Web</div>
            <h1 className="font-serif font-light text-[clamp(2.5rem,6vw,4.5rem)] leading-[1.05] text-ivory">
              Coming May 2026.
            </h1>
            <p className="mt-8 text-mist text-lg leading-relaxed">
              A real-estate hub for Central Washington. License-verified
              realtors. Local vendors. AI tools that earn their place. Built
              for the Valley.
            </p>

            <NewsletterForm />

            <p className="mt-8 text-dim text-sm">
              We will only email you about the launch. No marketing churn.
            </p>
          </div>
        </Container>
      </section>
    </main>
  );
}

function NewsletterForm() {
  return (
    <form
      action="/api/public/v1/posts/newsletter/?source=coming-soon"
      method="post"
      className="mt-12 flex flex-col items-stretch gap-4 sm:flex-row sm:items-center"
      data-testid="coming-soon-form"
    >
      <label htmlFor="cs-email" className="sr-only">
        Email address
      </label>
      <input
        id="cs-email"
        name="email"
        type="email"
        required
        autoComplete="email"
        placeholder="you@yakimavalley.com"
        className="flex-1 rounded-md border border-warm bg-panel px-5 py-4 text-ivory placeholder:text-dim focus:border-gold focus:outline-none"
      />
      <button
        type="submit"
        className="rounded-md bg-gold px-6 py-4 font-medium text-black transition-colors hover:bg-gold-hi focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-hi"
      >
        Notify me
      </button>
    </form>
  );
}
