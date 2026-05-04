"use client";

import { useState } from "react";
import Image from "next/image";
import type { Review, Service } from "@/lib/api/types";
import { cn, formatDate, pluralize } from "@/lib/utils";

type Tab = "overview" | "packages" | "reviews" | "faq";

interface ServiceTabsProps {
  service: Service;
  reviews: Review[];
}

const tabs: Array<{ key: Tab; label: string }> = [
  { key: "overview", label: "Overview" },
  { key: "packages", label: "Packages" },
  { key: "reviews", label: "Reviews" },
  { key: "faq", label: "FAQ" },
];

export default function ServiceTabs({ service, reviews }: ServiceTabsProps) {
  const [active, setActive] = useState<Tab>("overview");
  const packages = service.packages || [];
  const faq = service.faq || [];

  return (
    <div>
      <div role="tablist" className="flex gap-1 border-b border-gold/14">
        {tabs.map((t) => {
          const isActive = active === t.key;
          return (
            <button
              key={t.key}
              role="tab"
              type="button"
              aria-selected={isActive}
              onClick={() => setActive(t.key)}
              className={cn(
                "px-5 py-4 text-[11px] uppercase tracking-luxe transition-colors -mb-px border-b-2",
                isActive
                  ? "text-gold border-gold"
                  : "text-mist border-transparent hover:text-ivory",
              )}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      <div className="py-8">
        {active === "overview" && (
          <div
            className="post-body max-w-3xl"
            dangerouslySetInnerHTML={{ __html: service.description_html || "" }}
          />
        )}

        {active === "packages" &&
          (packages.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {packages.map((p) => (
                <div
                  key={p.id}
                  className="bg-deep border border-gold/22 p-6 flex flex-col"
                >
                  <h3 className="font-serif text-xl text-ivory mb-2">{p.name}</h3>
                  <p className="font-serif text-gold text-3xl mb-3">
                    ${p.price.toLocaleString()}
                  </p>
                  {p.delivery_days != null && (
                    <p className="text-[11px] uppercase tracking-luxe text-mist mb-5">
                      {p.delivery_days}{" "}
                      {pluralize(p.delivery_days, "day", "days")} delivery
                    </p>
                  )}
                  <p className="text-mist text-sm leading-relaxed mb-5">
                    {p.description}
                  </p>
                  {p.features.length > 0 && (
                    <ul className="space-y-2 mt-auto">
                      {p.features.map((f, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm text-ivory"
                        >
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 14 14"
                            className="text-gold flex-shrink-0 mt-1"
                            aria-hidden
                          >
                            <path
                              d="M2 7l3 3 7-7"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              fill="none"
                            />
                          </svg>
                          {f}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">
              No packages published. Use the inquiry form for a custom quote.
            </p>
          ))}

        {active === "reviews" &&
          (reviews.length > 0 ? (
            <div className="space-y-6">
              {reviews.map((r) => (
                <div
                  key={r.id}
                  className="border-b border-gold/14 pb-6 last:border-b-0"
                >
                  <div className="flex items-center gap-3 mb-2">
                    {r.reviewer.avatar_url ? (
                      <Image
                        src={r.reviewer.avatar_url}
                        alt=""
                        width={28}
                        height={28}
                        className="rounded-full border border-gold/22"
                      />
                    ) : (
                      <div
                        aria-hidden
                        className="w-7 h-7 rounded-full bg-warm border border-gold/22 flex items-center justify-center text-[10px] text-gold"
                      >
                        {r.reviewer.display_name.charAt(0).toUpperCase()}
                      </div>
                    )}
                    <span className="text-sm text-ivory">
                      {r.reviewer.display_name}
                    </span>
                    <div
                      className="flex gap-0.5"
                      aria-label={`${r.rating} of 5 stars`}
                    >
                      {[0, 1, 2, 3, 4].map((i) => (
                        <svg
                          key={i}
                          width="12"
                          height="12"
                          viewBox="0 0 12 12"
                          fill={i < r.rating ? "currentColor" : "none"}
                          stroke="currentColor"
                          className="text-gold"
                          aria-hidden
                        >
                          <path
                            d="M6 1l1.545 3.13L11 4.635 8.5 7.07l.59 3.43L6 8.885 2.91 10.5l.59-3.43L1 4.635l3.455-.505L6 1z"
                            strokeWidth="0.8"
                          />
                        </svg>
                      ))}
                    </div>
                    <span className="text-[11px] uppercase tracking-luxe text-dim ml-auto">
                      {formatDate(r.created_at)}
                    </span>
                  </div>
                  <p className="text-mist text-sm leading-relaxed">{r.body}</p>
                  {r.vendor_response && (
                    <div className="mt-4 ml-8 pl-4 border-l border-gold/22">
                      <p className="text-[11px] uppercase tracking-luxe text-gold mb-2">
                        Vendor response
                      </p>
                      <p className="text-mist text-sm leading-relaxed">
                        {r.vendor_response}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">
              No reviews yet. Be the first to leave one.
            </p>
          ))}

        {active === "faq" &&
          (faq.length > 0 ? (
            <div className="max-w-3xl space-y-6">
              {faq.map((f, i) => (
                <details
                  key={i}
                  className="border border-gold/14 group bg-deep"
                >
                  <summary className="flex items-center justify-between gap-4 p-5 cursor-pointer list-none text-ivory">
                    <span className="font-serif text-lg leading-tight">
                      {f.question}
                    </span>
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 14 14"
                      className="text-gold flex-shrink-0 transition-transform group-open:rotate-180"
                      aria-hidden
                    >
                      <path
                        d="M3 5l4 4 4-4"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        fill="none"
                      />
                    </svg>
                  </summary>
                  <div className="px-5 pb-5 text-mist leading-relaxed">
                    {f.answer}
                  </div>
                </details>
              ))}
            </div>
          ) : (
            <p className="text-mist text-sm">No FAQ posted yet.</p>
          ))}
      </div>
    </div>
  );
}
