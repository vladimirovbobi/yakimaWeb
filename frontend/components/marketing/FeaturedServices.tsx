import Link from "next/link";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import { safeServerFetch } from "@/lib/api/server";

interface FeaturedService {
  id: number;
  slug: string;
  title: string;
  summary: string;
  category: { slug: string; label: string } | null;
  starting_price_cents: number | null;
  cover_image: { url: string } | null;
  vendor: {
    id: number;
    slug: string;
    business_name: string;
    tagline: string | null;
  };
  rating_avg: number | null;
}

interface FeaturedResponse {
  context: string;
  results: FeaturedService[];
}

interface Props {
  contextKind: string;
  seedKey?: string;
  category?: string;
  limit?: number;
  heading?: string;
  subheading?: string;
  className?: string;
  variant?: "row" | "stack";
}

function formatPrice(cents: number | null): string | null {
  if (cents == null) return null;
  return `$${(cents / 100).toLocaleString()}`;
}

export default async function FeaturedServices({
  contextKind,
  seedKey,
  category,
  limit = 2,
  heading = "Featured services",
  subheading = "Vendors your peers in the Yakima Valley actually use.",
  className = "",
  variant = "row",
}: Props) {
  const params = new URLSearchParams({
    context: contextKind,
    limit: String(Math.max(1, Math.min(limit, 6))),
  });
  if (seedKey) params.set("seed", seedKey);
  if (category) params.set("category", category);

  const data = await safeServerFetch<FeaturedResponse>(
    `/api/public/v1/services/featured/?${params.toString()}`,
    {},
    { next: { revalidate: 600 } },
  );

  const items = data?.results || [];
  if (items.length === 0) return null;

  return (
    <ScrollReveal>
      <aside
        className={`border border-gold/22 bg-panel ${className}`}
        aria-label="Featured services from the marketplace"
      >
        <div className="px-5 md:px-7 py-5 border-b border-gold/14 flex items-baseline justify-between gap-4">
          <div>
            <p className="ey">Featured · From the marketplace</p>
            <h3 className="font-serif text-ivory text-lg md:text-xl leading-tight font-light mt-2">
              {heading}
            </h3>
            {subheading && (
              <p className="text-mist text-sm mt-1.5 leading-relaxed">
                {subheading}
              </p>
            )}
          </div>
          <Link
            href="/services"
            className="hidden sm:inline-flex items-center gap-2 text-[11px] uppercase tracking-cap text-gold hover:text-gold-hi transition-colors whitespace-nowrap"
          >
            See all →
          </Link>
        </div>
        <ul
          className={
            variant === "stack"
              ? "divide-y divide-gold/14"
              : "grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gold/14"
          }
        >
          {items.map((s) => {
            const price = formatPrice(s.starting_price_cents);
            return (
              <li key={s.id} className="px-5 md:px-7 py-5">
                <Link
                  href={`/services/${s.slug}`}
                  className="group flex items-start gap-4"
                >
                  <div className="relative w-20 h-20 md:w-24 md:h-24 flex-shrink-0 bg-warm overflow-hidden">
                    {s.cover_image?.url ? (
                      /* eslint-disable-next-line @next/next/no-img-element */
                      <img
                        src={s.cover_image.url}
                        alt=""
                        loading="lazy"
                        decoding="async"
                        className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 ease-luxe group-hover:scale-[1.04]"
                      />
                    ) : (
                      <div
                        className="absolute inset-0 bg-gradient-to-br from-warm via-deep to-black"
                        aria-hidden
                      />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {s.category?.label && (
                        <span className="text-[10px] uppercase tracking-eyebrow text-gold border border-gold/35 px-1.5 py-0.5">
                          {s.category.label}
                        </span>
                      )}
                      {s.rating_avg != null && (
                        <span className="label-luxe text-gold-hi text-[10px]">
                          ★ {s.rating_avg.toFixed(1)}
                        </span>
                      )}
                    </div>
                    <p className="font-serif text-base md:text-lg text-ivory leading-tight mt-1.5 group-hover:text-gold-hi transition-colors">
                      {s.title}
                    </p>
                    <p className="text-[11px] uppercase tracking-luxe text-dim mt-1">
                      {s.vendor.business_name}
                    </p>
                    <p className="text-mist text-sm mt-2 line-clamp-2">
                      {s.summary}
                    </p>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      {price ? (
                        <span className="font-serif text-gold text-sm">
                          from {price}
                        </span>
                      ) : (
                        <span />
                      )}
                      <span className="inline-flex items-center gap-2 text-[10px] uppercase tracking-cap text-gold group-hover:tracking-luxe transition-[letter-spacing] duration-300">
                        Learn more
                        <svg
                          width="12"
                          height="8"
                          viewBox="0 0 16 10"
                          fill="none"
                          aria-hidden
                        >
                          <path
                            d="M1 5h13m0 0L10 1m4 4l-4 4"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                    </div>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
        <div className="px-5 md:px-7 py-3 border-t border-gold/14 text-[10px] uppercase tracking-luxe text-dim">
          Featured · Vendors verified through ARELLO &amp; brokerage attestation
        </div>
      </aside>
    </ScrollReveal>
  );
}
