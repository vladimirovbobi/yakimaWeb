"use client";

import { motion, useReducedMotion } from "framer-motion";
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
  const reduced = useReducedMotion();

  return (
    <section
      className={cn(
        "relative w-full min-h-[560px] md:min-h-[640px] lg:min-h-[72vh] bg-black overflow-hidden",
        className,
      )}
    >
      {bgImage && (
        <motion.div
          className="absolute inset-0"
          initial={reduced ? false : { opacity: 0, scale: 1.05 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
        >
          <div
            className="absolute inset-0 bg-cover bg-center animate-slow-zoom"
            style={{ backgroundImage: `url(${bgImage})` }}
          />
        </motion.div>
      )}

      <div
        className="absolute inset-0 bg-gradient-to-t from-black via-black/70 to-black/40"
        aria-hidden
      />
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(191,160,106,0.08)_0%,_transparent_60%)]"
        aria-hidden
      />

      <Container
        as="div"
        className="relative z-10 flex flex-col justify-center min-h-[560px] md:min-h-[640px] lg:min-h-[72vh] py-24"
      >
        {eyebrow && (
          <motion.div
            initial={reduced ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="ey mb-6"
          >
            {eyebrow}
          </motion.div>
        )}
        <motion.h1
          initial={reduced ? false : { opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="font-serif text-ivory font-light leading-[1.05] text-[clamp(2.5rem,6vw,4.75rem)] max-w-4xl"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            initial={reduced ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="text-mist text-base md:text-lg max-w-2xl mt-6 leading-relaxed"
          >
            {subtitle}
          </motion.p>
        )}
        {(primary || secondary) && (
          <motion.div
            initial={reduced ? false : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.7 }}
            className="flex flex-col sm:flex-row gap-4 mt-10"
          >
            {primary && (
              <Link
                href={primary.href}
                className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
              >
                {primary.label}
              </Link>
            )}
            {secondary && (
              <Link
                href={secondary.href}
                className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
              >
                {secondary.label}
              </Link>
            )}
          </motion.div>
        )}
      </Container>
    </section>
  );
}
