import { cn } from "@/lib/utils";

type Tone = "gold" | "verified" | "pending" | "active" | "removed" | "neutral";

const tones: Record<Tone, string> = {
  gold: "bg-gold/15 text-gold-hi border-gold/30",
  verified: "bg-ok/15 text-ok border-ok/30",
  pending: "bg-warn/15 text-warn border-warn/30",
  active: "bg-gold/15 text-gold border-gold/40",
  removed: "bg-err/15 text-err border-err/30",
  neutral: "bg-mist/10 text-mist border-mist/30",
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export default function Badge({
  tone = "neutral",
  className,
  children,
  ...rest
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 text-[10px] uppercase tracking-luxe border",
        tones[tone],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
