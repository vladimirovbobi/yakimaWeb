import Link from "next/link";
import { safeServerFetch } from "@/lib/api/server";
import type { Pagination, Post, Tag } from "@/lib/api/types";

interface TagDetailResponse extends Pagination<Post> {
  tag: Tag;
}

export default async function TagPage(props: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await props.params;
  const data = await safeServerFetch<TagDetailResponse>(
    `/api/public/v1/posts/tags/${encodeURIComponent(slug)}/`,
    { method: "GET" },
  );

  if (!data) {
    return (
      <main className="px-6 py-16 max-w-4xl mx-auto">
        <h1 className="font-serif font-light text-ivory text-4xl">
          Tag not found
        </h1>
        <Link
          href="/blog"
          className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi mt-6 inline-block"
        >
          ← Back to blog
        </Link>
      </main>
    );
  }

  const posts = data.results ?? [];

  return (
    <main className="px-6 py-16 max-w-5xl mx-auto">
      <Link
        href="/blog"
        className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
      >
        ← All posts
      </Link>

      <header className="mt-8 mb-12">
        <div className="ey mb-3">Tag</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2.5rem,5vw,3.5rem)] leading-tight">
          {data.tag.name}
        </h1>
        <p className="text-mist mt-3">
          {data.tag.post_count}{" "}
          {data.tag.post_count === 1 ? "post" : "posts"} tagged{" "}
          <span className="text-gold-hi">#{data.tag.slug}</span>
        </p>
      </header>

      <ul className="space-y-6">
        {posts.length === 0 && (
          <li className="text-mist">No posts under this tag yet.</li>
        )}
        {posts.map((p) => (
          <li
            key={p.id}
            className="border border-gold/22 bg-deep p-6 hover:border-gold/40 transition"
          >
            <Link href={`/blog/${p.slug}`}>
              <h2 className="font-serif font-light text-ivory text-2xl mb-2">
                {p.title}
              </h2>
              <p className="text-mist text-sm mb-3">{p.excerpt}</p>
              <div className="text-[10px] uppercase tracking-luxe text-dim">
                {p.author.display_name} •{" "}
                {p.published_at
                  ? new Date(p.published_at).toLocaleDateString()
                  : ""}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
