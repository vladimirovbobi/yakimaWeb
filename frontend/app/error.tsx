"use client";

import { useEffect } from "react";
import Link from "next/link";
import Container from "@/components/layout/Container";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface to client logging so user-facing errors aren't silent.
    if (typeof window !== "undefined" && error) {
      console.warn("[error.tsx]", error.message, error.digest);
    }
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center py-32">
      <Container className="text-center">
        <div className="ey mb-6 text-err">Something broke</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2.5rem,6vw,4rem)] leading-[1.05]">
          We hit a snag.
        </h1>
        <p className="text-mist mt-6 max-w-md mx-auto leading-relaxed">
          The page failed to load. The error has been logged. You can try again
          or head home.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-10">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
          >
            Try again
          </button>
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
          >
            Home
          </Link>
        </div>
      </Container>
    </main>
  );
}
