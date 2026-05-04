"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import type { Category } from "@/lib/api/types";
import Button from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface ServicesFiltersProps {
  categories: Category[];
  active: {
    category?: string;
    q?: string;
    min_price?: string;
    max_price?: string;
    has_bundle?: boolean;
  };
}

export default function ServicesFilters({
  categories,
  active,
}: ServicesFiltersProps) {
  const router = useRouter();
  const sp = useSearchParams();
  const [q, setQ] = useState(active.q || "");
  const [minP, setMinP] = useState(active.min_price || "");
  const [maxP, setMaxP] = useState(active.max_price || "");
  const [bundle, setBundle] = useState(active.has_bundle || false);

  useEffect(() => {
    setQ(active.q || "");
    setMinP(active.min_price || "");
    setMaxP(active.max_price || "");
    setBundle(active.has_bundle || false);
  }, [active.q, active.min_price, active.max_price, active.has_bundle]);

  const topLevel = categories.filter((c) => !c.parent_id);

  function apply() {
    const out = new URLSearchParams(sp.toString());
    if (q) out.set("q", q);
    else out.delete("q");
    if (minP) out.set("min_price", minP);
    else out.delete("min_price");
    if (maxP) out.set("max_price", maxP);
    else out.delete("max_price");
    if (bundle) out.set("has_bundle", "1");
    else out.delete("has_bundle");
    out.delete("cursor");
    router.push(`/services?${out.toString()}`);
  }

  function setCategory(slug: string | null) {
    const out = new URLSearchParams(sp.toString());
    if (slug) out.set("category", slug);
    else out.delete("category");
    out.delete("cursor");
    router.push(`/services?${out.toString()}`);
  }

  function clearAll() {
    router.push("/services");
  }

  return (
    <div className="space-y-8">
      <div>
        <label
          htmlFor="svc-search"
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          Search
        </label>
        <div className="flex gap-2">
          <input
            id="svc-search"
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") apply();
            }}
            placeholder="Photo, lender, tour..."
            className="flex-1 bg-warm border border-gold/22 text-ivory placeholder-dim px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          <button
            type="button"
            onClick={apply}
            aria-label="Search services"
            className="px-3 bg-gold text-black hover:bg-gold-hi rounded-md"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle
                cx="7"
                cy="7"
                r="5"
                stroke="currentColor"
                strokeWidth="1.6"
              />
              <path
                d="M11 11l3 3"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>
      </div>

      <div>
        <p className="text-[11px] uppercase tracking-luxe text-mist mb-3">
          Category
        </p>
        <ul className="space-y-1">
          <li>
            <button
              type="button"
              onClick={() => setCategory(null)}
              className={cn(
                "w-full text-left px-3 py-2 text-sm transition-colors",
                !active.category
                  ? "bg-gold/15 text-gold-hi border-l-2 border-gold"
                  : "text-mist hover:text-ivory hover:bg-deep",
              )}
            >
              All categories
            </button>
          </li>
          {topLevel.map((c) => (
            <li key={c.id}>
              <button
                type="button"
                onClick={() => setCategory(c.slug)}
                className={cn(
                  "w-full text-left px-3 py-2 text-sm transition-colors flex items-center justify-between",
                  active.category === c.slug
                    ? "bg-gold/15 text-gold-hi border-l-2 border-gold"
                    : "text-mist hover:text-ivory hover:bg-deep",
                )}
              >
                <span>{c.name}</span>
                {c.service_count != null && (
                  <span className="text-[11px] text-dim">
                    {c.service_count}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-[11px] uppercase tracking-luxe text-mist mb-3">
          Price range
        </p>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            value={minP}
            onChange={(e) => setMinP(e.target.value)}
            placeholder="Min"
            className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
          />
          <span className="text-dim">to</span>
          <input
            type="number"
            min={0}
            value={maxP}
            onChange={(e) => setMaxP(e.target.value)}
            placeholder="Max"
            className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold"
          />
        </div>
      </div>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={bundle}
          onChange={(e) => setBundle(e.target.checked)}
          className="w-4 h-4 accent-gold"
        />
        <span className="text-sm text-mist">Has bundle pricing</span>
      </label>

      <div className="flex flex-col gap-2 pt-3 border-t border-gold/14">
        <Button onClick={apply} variant="solid" size="sm">
          Apply filters
        </Button>
        <button
          type="button"
          onClick={clearAll}
          className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold py-2"
        >
          Clear all
        </button>
      </div>
    </div>
  );
}
