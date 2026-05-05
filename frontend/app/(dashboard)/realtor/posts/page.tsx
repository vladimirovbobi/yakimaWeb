import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import EmptyState from "@/components/layout/EmptyState";
import type { Post } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

interface MeActivity {
  recent_posts?: Post[];
}

export default async function MyPostsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/realtor/posts");
  if (!user.is_realtor && !user.is_staff) redirect("/dashboard");

  const activity = await safeServerFetch<MeActivity>(
    "/api/v1/me/activity/?limit=50",
    {},
    { auth: true },
  );
  const posts = activity?.recent_posts ?? [];

  return (
    <div className="max-w-4xl">
      <div className="ey mb-3">Realtor</div>
      <div className="flex items-center justify-between mb-8 gap-4 flex-wrap">
        <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight">
          Your posts
        </h1>
        <Link
          href="/dashboard/realtor/posts/new"
          className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors"
        >
          New post
        </Link>
      </div>

      {posts.length === 0 ? (
        <EmptyState
          kind="posts"
          title="No posts yet"
          body="Write your first post and we'll publish it once it clears the moderation pipeline."
          action={{ label: "Write a post", href: "/dashboard/realtor/posts/new" }}
        />
      ) : (
        <ul className="border border-gold/14 divide-y divide-gold/14">
          {posts.map((p) => (
            <li
              key={p.id}
              className="px-6 py-4 flex items-center justify-between gap-4 hover:bg-warm/30 transition-colors"
            >
              <div className="min-w-0">
                <Link
                  href={`/blog/${p.slug}`}
                  className="block font-serif text-lg text-ivory hover:text-gold-hi truncate"
                >
                  {p.title}
                </Link>
                <p className="text-[11px] uppercase tracking-luxe text-dim mt-1">
                  {p.published_at ? formatDate(p.published_at) : "Draft"}
                </p>
              </div>
              <Link
                href={`/dashboard/realtor/posts/${p.slug}/edit`}
                className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi flex-shrink-0"
              >
                Edit
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
