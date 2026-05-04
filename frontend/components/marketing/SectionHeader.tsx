import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  description?: string;
  align?: "left" | "center";
  className?: string;
}

export default function SectionHeader({
  eyebrow,
  title,
  description,
  align = "left",
  className,
}: SectionHeaderProps) {
  return (
    <div
      className={cn(
        "max-w-3xl",
        align === "center" && "mx-auto text-center",
        className,
      )}
    >
      {eyebrow && <div className="ey mb-4">{eyebrow}</div>}
      <h2 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,3rem)] leading-[1.1]">
        {title}
      </h2>
      {description && (
        <p className="text-mist mt-5 leading-relaxed text-base md:text-lg">
          {description}
        </p>
      )}
    </div>
  );
}
