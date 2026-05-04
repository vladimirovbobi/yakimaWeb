import Link from "next/link";

interface ComingSoonProps {
  eyebrow: string;
  title: string;
  sprint: string;
  body?: string;
  back?: { label: string; href: string };
}

export default function ComingSoon({
  eyebrow,
  title,
  sprint,
  body,
  back,
}: ComingSoonProps) {
  return (
    <div className="max-w-3xl">
      <div className="ey mb-3">{eyebrow}</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight">
        {title}
      </h1>
      {body && (
        <p className="text-mist mt-4 leading-relaxed text-base md:text-lg">
          {body}
        </p>
      )}
      <div className="mt-10 border border-gold/22 bg-deep p-8">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-[11px] uppercase tracking-luxe text-gold border border-gold/40 px-2 py-1">
            {sprint}
          </span>
          <span className="text-[11px] uppercase tracking-luxe text-mist">
            Building
          </span>
        </div>
        <p className="text-mist text-sm leading-relaxed">
          This surface is scaffolded. The full interactions land in {sprint}.
        </p>
      </div>
      {back && (
        <Link
          href={back.href}
          className="inline-flex items-center gap-2 text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi mt-8"
        >
          <svg
            width="12"
            height="10"
            viewBox="0 0 12 10"
            fill="none"
            aria-hidden
          >
            <path
              d="M11 5H1m0 0l4-4M1 5l4 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {back.label}
        </Link>
      )}
    </div>
  );
}
