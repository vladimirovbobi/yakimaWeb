import Link from "next/link";
import Image from "next/image";
import type { Service } from "@/lib/api/types";
import { Card, CardBody } from "@/components/ui/Card";
import { pluralize } from "@/lib/utils";

interface ServiceCardProps {
  service: Service;
  priority?: boolean;
}

function Stars({ value, count }: { value: number | null; count: number }) {
  const v = value ?? 0;
  return (
    <div className="flex items-center gap-1.5" aria-label={`${v} of 5 stars`}>
      <div className="flex gap-0.5">
        {[0, 1, 2, 3, 4].map((i) => (
          <svg
            key={i}
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill={i < Math.round(v) ? "currentColor" : "none"}
            stroke="currentColor"
            className="text-gold"
            aria-hidden
          >
            <path
              d="M6 1l1.545 3.13L11 4.635 8.5 7.07l.59 3.43L6 8.885 2.91 10.5l.59-3.43L1 4.635l3.455-.505L6 1z"
              strokeWidth="0.8"
              strokeLinejoin="round"
            />
          </svg>
        ))}
      </div>
      <span className="text-[11px] text-mist">
        {v.toFixed(1)} ({count} {pluralize(count, "review")})
      </span>
    </div>
  );
}

export default function ServiceCard({ service, priority }: ServiceCardProps) {
  return (
    <Link
      href={`/services/${service.slug}`}
      className="group block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
    >
      <Card className="h-full overflow-hidden">
        <div className="relative aspect-[4/3] overflow-hidden bg-warm">
          {service.hero_image_url ? (
            <Image
              src={service.hero_image_url}
              alt={service.title}
              fill
              priority={priority}
              sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 420px"
              className="object-cover transition-transform duration-700 ease-luxe group-hover:scale-[1.04]"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-dim text-xs uppercase tracking-luxe">
              No image
            </div>
          )}
        </div>
        <CardBody className="flex flex-col">
          <div className="flex items-center justify-between gap-3 mb-3">
            <span className="text-[11px] uppercase tracking-luxe text-gold truncate">
              {service.vendor.business_name}
            </span>
            <Stars
              value={service.rating_avg}
              count={service.rating_count}
            />
          </div>
          <h3 className="font-serif text-xl text-ivory font-light leading-tight mb-2 group-hover:text-gold-hi transition-colors">
            {service.title}
          </h3>
          <p className="text-mist text-sm leading-relaxed line-clamp-2 mb-5">
            {service.tagline}
          </p>
          <div className="mt-auto flex items-end justify-between gap-4 pt-5 border-t border-gold/14">
            {service.starting_price != null ? (
              <div>
                <p className="text-[10px] uppercase tracking-luxe text-mist">
                  Starting at
                </p>
                <p className="font-serif text-gold text-2xl leading-none mt-1">
                  ${service.starting_price.toLocaleString()}
                </p>
              </div>
            ) : (
              <span className="text-mist text-sm">Custom quote</span>
            )}
            <span className="inline-flex items-center gap-2 text-[11px] uppercase tracking-luxe text-gold transition-transform duration-300 group-hover:translate-x-1">
              View service
              <svg
                width="14"
                height="10"
                viewBox="0 0 14 10"
                fill="none"
                aria-hidden
              >
                <path
                  d="M1 5h12m0 0L9 1m4 4l-4 4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
          </div>
        </CardBody>
      </Card>
    </Link>
  );
}
