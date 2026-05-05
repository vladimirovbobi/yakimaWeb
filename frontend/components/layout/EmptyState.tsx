/**
 * Branded empty-state block. Pairs an SVG illustration with copy + optional
 * action. Used wherever an authenticated list returns zero items so the
 * surface still feels alive instead of a plain sentence.
 */

import Link from "next/link";
import { emptyStateImage } from "@/lib/placeholders";

interface EmptyStateProps {
  kind?: "posts" | "services" | "leads" | "notifications" | "search" | string;
  title: string;
  body?: string;
  action?: { label: string; href: string };
  className?: string;
}

export default function EmptyState({
  kind = "posts",
  title,
  body,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      role="status"
      className={
        "border border-gold/14 bg-deep p-8 md:p-12 text-center max-w-xl mx-auto " +
        (className ?? "")
      }
    >
      <img
        src={emptyStateImage(kind)}
        alt=""
        aria-hidden
        className="mx-auto h-24 w-24 md:h-32 md:w-32 mb-6 opacity-80"
      />
      <h3 className="font-serif text-ivory text-xl md:text-2xl mb-3">
        {title}
      </h3>
      {body && (
        <p className="text-mist text-sm md:text-base leading-relaxed mb-6">
          {body}
        </p>
      )}
      {action && (
        <Link
          href={action.href}
          className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
