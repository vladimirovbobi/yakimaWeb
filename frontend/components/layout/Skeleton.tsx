/**
 * Tiny presentational skeleton primitives. Used by route-level loading.tsx
 * fallbacks. Honors prefers-reduced-motion via Tailwind's `motion-safe:`
 * variant so the shimmer stops for users who asked for less motion.
 */

import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function SkeletonBar({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden
      className={cn(
        "bg-warm/50 motion-safe:animate-pulse rounded-sm",
        className,
      )}
    />
  );
}

export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div
      aria-hidden
      className={cn(
        "border border-gold/14 bg-deep p-6 space-y-4",
        className,
      )}
    >
      <SkeletonBar className="h-3 w-24" />
      <SkeletonBar className="h-6 w-full" />
      <SkeletonBar className="h-4 w-5/6" />
      <SkeletonBar className="h-4 w-3/5" />
    </div>
  );
}

export function PageSkeleton({
  label = "Loading",
  cards = 6,
}: {
  label?: string;
  cards?: number;
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label}
      className="container mx-auto px-4 py-16 max-w-7xl"
    >
      <span className="sr-only">{label}</span>
      <div className="space-y-4 mb-12">
        <SkeletonBar className="h-3 w-32" />
        <SkeletonBar className="h-12 w-3/4 max-w-3xl" />
        <SkeletonBar className="h-4 w-1/2 max-w-xl" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: cards }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  );
}
