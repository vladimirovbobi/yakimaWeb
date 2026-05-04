import { cn } from "@/lib/utils";

const tones = {
  pending:   "border-mist/40 text-mist",
  contacted: "border-blue-400/40 text-blue-200",
  won:       "border-emerald-500/40 text-emerald-300",
  lost:      "border-rose-500/40 text-rose-300",
} as const;

export type LeadStatus = keyof typeof tones;

export default function LeadStatusPill({
  status,
  className,
}: {
  status: LeadStatus | string;
  className?: string;
}) {
  const tone = (status in tones ? tones[status as LeadStatus] : tones.pending);
  return (
    <span
      className={cn(
        "px-3 py-1 text-[10px] uppercase tracking-luxe border rounded-full",
        tone,
        className,
      )}
    >
      {status}
    </span>
  );
}
