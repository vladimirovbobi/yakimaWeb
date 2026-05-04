import Link from "next/link";
import { safeServerFetch } from "@/lib/api/server";
import type { Tag } from "@/lib/api/types";

export default async function TagsIndexPage() {
  const tags = await safeServerFetch<Tag[]>(
    "/api/public/v1/posts/tags/",
    { method: "GET" },
  );

  return (
    <main className="px-6 py-16 max-w-4xl mx-auto">
      <Link
        href="/blog"
        className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
      >
        ← All posts
      </Link>

      <header className="mt-8 mb-12">
        <div className="ey mb-3">Tags</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2.5rem,5vw,3.5rem)] leading-tight">
          Browse by topic
        </h1>
      </header>

      <ul className="flex flex-wrap gap-3">
        {(tags ?? []).map((t) => (
          <li key={t.slug}>
            <Link
              href={`/blog/tags/${t.slug}`}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gold/22 text-mist hover:text-gold-hi hover:border-gold/40"
            >
              <span>#{t.slug}</span>
              <span className="text-[10px] uppercase tracking-luxe text-dim">
                {t.post_count}
              </span>
            </Link>
          </li>
        ))}
        {(!tags || tags.length === 0) && (
          <li className="text-mist">No tags yet.</li>
        )}
      </ul>
    </main>
  );
}
