import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { Post, ForumThread } from "@/lib/api/types";
import { Card, CardBody } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils";

interface MeActivity {
  recent_posts: Post[];
  recent_threads: ForumThread[];
}

export default async function DashboardHome() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard");

  const activity = await safeServerFetch<MeActivity>(
    "/api/v1/me/activity/",
    {},
    { auth: true },
  );

  const quickLinks: Array<{ label: string; href: string; tone?: string }> = [
    { label: "Try furniture remover", href: "/dashboard/tools/furniture-remover" },
    { label: "Write a description", href: "/dashboard/tools/description-writer" },
    { label: "Browse community", href: "/community" },
    { label: "See marketplace", href: "/services" },
  ];

  if (user.is_realtor) {
    quickLinks.unshift({
      label: "Write a blog post",
      href: "/dashboard/realtor/posts/new",
    });
  }
  if (user.is_vendor) {
    quickLinks.unshift({
      label: "Add a service",
      href: "/dashboard/vendor",
    });
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-10">
        <div className="ey mb-3">Dashboard</div>
        <h1 className="font-serif font-light text-ivory text-[clamp(2rem,4vw,2.75rem)] leading-tight">
          Welcome back, {firstName(user.display_name) || "stranger"}.
        </h1>
        <p className="text-mist mt-3 leading-relaxed">
          Pick up where you left off, or jump into a tool.
        </p>
      </div>

      <section className="mb-12">
        <h2 className="text-[11px] uppercase tracking-luxe text-mist mb-4">
          Quick links
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {quickLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="block px-5 py-4 bg-deep border border-gold/14 hover:border-gold/52 hover:bg-warm/30 transition-colors text-sm text-ivory hover:text-gold-hi"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card hover={false}>
          <CardBody>
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-serif text-2xl text-ivory">Your posts</h3>
              {user.is_realtor && (
                <Link
                  href="/dashboard/realtor/posts"
                  className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
                >
                  All
                </Link>
              )}
            </div>
            {activity?.recent_posts && activity.recent_posts.length > 0 ? (
              <ul className="space-y-3">
                {activity.recent_posts.slice(0, 5).map((p) => (
                  <li
                    key={p.id}
                    className="border-b border-gold/14 pb-3 last:border-b-0 last:pb-0"
                  >
                    <Link
                      href={`/blog/${p.slug}`}
                      className="text-ivory hover:text-gold-hi transition-colors text-sm font-serif"
                    >
                      {p.title}
                    </Link>
                    <p className="text-[11px] uppercase tracking-luxe text-dim mt-1">
                      {formatDate(p.published_at)}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-mist text-sm">No posts yet.</p>
            )}
          </CardBody>
        </Card>

        <Card hover={false}>
          <CardBody>
            <h3 className="font-serif text-2xl text-ivory mb-5">
              Forum activity
            </h3>
            {activity?.recent_threads && activity.recent_threads.length > 0 ? (
              <ul className="space-y-3">
                {activity.recent_threads.slice(0, 5).map((t) => (
                  <li
                    key={t.id}
                    className="border-b border-gold/14 pb-3 last:border-b-0 last:pb-0"
                  >
                    <Link
                      href={`/community/threads/${t.slug}`}
                      className="text-ivory hover:text-gold-hi transition-colors text-sm font-serif"
                    >
                      {t.title}
                    </Link>
                    <p className="text-[11px] uppercase tracking-luxe text-dim mt-1">
                      {t.flair} - {t.reply_count} replies
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-mist text-sm">
                No threads yet. Start one in{" "}
                <Link
                  href="/community"
                  className="text-gold hover:text-gold-hi underline underline-offset-4"
                >
                  the community
                </Link>
                .
              </p>
            )}
          </CardBody>
        </Card>
      </section>
    </div>
  );
}

function firstName(displayName: string): string {
  if (!displayName) return "";
  return displayName.split(/\s+/)[0];
}
