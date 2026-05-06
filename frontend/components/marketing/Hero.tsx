// Pure server component now — no Framer Motion. The hero renders at its final
// state on SSR, no animation gating that can fail under React 19.2 + Next 16.
// (Visual fade-up was nice but having content reliably visible matters more.)
import Link from "next/link";
import Container from "@/components/layout/Container";
import { cn } from "@/lib/utils";

interface HeroProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  bgImage?: string;
  primary?: { label: string; href: string };
  secondary?: { label: string; href: string };
  className?: string;
}

export default function Hero({
  eyebrow,
  title,
  subtitle,
  bgImage,
  primary,
  secondary,
  className,
}: HeroProps) {
  return (
    <section
      className={cn(
        "relative w-full min-h-[480px] sm:min-h-[560px] md:min-h-[640px] lg:min-h-[72vh] bg-deep overflow-hidden",
        className,
      )}
    >
      {bgImage && (
        <div
          className="absolute inset-0 bg-cover bg-center animate-slow-zoom"
          style={{ backgroundImage: `url(${bgImage})` }}
        />
      )}

      {/* Cream-side overlay: warm-tan fade so image is visible at top, copy
          sits on a darker warm wash at the bottom (1301 model). */}
      <div
        className={cn(
          "absolute inset-0",
          bgImage
            ? "bg-gradient-to-t from-warm via-warm/60 to-transparent"
            : "bg-gradient-to-b from-deep via-black to-black",
        )}
        aria-hidden
      />
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(139,115,64,0.10)_0%,_transparent_60%)]"
        aria-hidden
      />

      <Container
        as="div"
        className="relative z-10 flex flex-col justify-center min-h-[480px] sm:min-h-[560px] md:min-h-[640px] lg:min-h-[72vh] py-16 sm:py-24"
      >
        {eyebrow && <div className="ey mb-6">{eyebrow}</div>}
        <h1 className="font-serif text-ivory font-light leading-[1.05] text-[clamp(2.5rem,6vw,4.75rem)] max-w-4xl">
          {title}
        </h1>
        {subtitle && (
          <p className="text-mist text-base md:text-lg max-w-2xl mt-6 leading-relaxed">
            {subtitle}
          </p>
        )}
        {(primary || secondary) && (
          <div className="flex flex-col sm:flex-row gap-4 mt-10">
            {primary && (
              <Link
                href={primary.href}
                data-touch
                className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-dark-bg text-dark-text font-medium hover:bg-dark-deep transition-colors w-full sm:w-auto"
              >
                {primary.label}
              </Link>
            )}
            {secondary && (
              <Link
                href={secondary.href}
                data-touch
                className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-dark-text transition-colors w-full sm:w-auto"
              >
                {secondary.label}
              </Link>
            )}
          </div>
        )}
      </Container>
    </section>
  );
}
