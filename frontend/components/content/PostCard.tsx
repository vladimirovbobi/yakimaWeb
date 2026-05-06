import Link from "next/link";
import Image from "next/image";
import type { Post } from "@/lib/api/types";
import { Card, CardBody } from "@/components/ui/Card";
import { formatDate, pluralize } from "@/lib/utils";
import { avatarPlaceholder, postPlaceholder } from "@/lib/placeholders";

const TYPE_LABEL: Record<string, string> = {
  org: "Yakima Web",
  blog: "Realtor blog",
  "lead-magnet": "Tool",
};

interface PostCardProps {
  post: Post;
  priority?: boolean;
}

export default function PostCard({ post, priority }: PostCardProps) {
  const typeLabel = TYPE_LABEL[post.post_type] || post.post_type;
  const heroSrc = post.hero_image_url || postPlaceholder(post.slug || post.id);
  return (
    <Link
      href={`/blog/${post.slug}`}
      className="group block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
    >
      <Card className="h-full overflow-hidden">
        <div className="relative aspect-[16/10] overflow-hidden bg-warm">
          <Image
            src={heroSrc}
            alt={post.title}
            fill
            priority={priority}
            sizes="(max-width: 768px) 100vw, (max-width: 1280px) 33vw, 420px"
            className="object-cover transition-transform duration-700 ease-luxe group-hover:scale-[1.04]"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-dark-bg/60 via-dark-bg/10 to-transparent" />
        </div>
        <CardBody className="flex flex-col">
          <div className="flex items-center gap-3 mb-4 text-[10px] uppercase tracking-luxe">
            <span className="text-gold">{typeLabel}</span>
            <span className="text-dim">|</span>
            <span className="text-mist">
              {post.reading_time_minutes}{" "}
              {pluralize(post.reading_time_minutes, "min", "min")} read
            </span>
          </div>
          <h3 className="font-serif text-2xl text-ivory font-light leading-tight mb-3 group-hover:text-gold-hi transition-colors">
            {post.title}
          </h3>
          <p className="text-mist text-sm leading-relaxed line-clamp-3 mb-5">
            {post.excerpt}
          </p>
          <div className="mt-auto flex items-center justify-between gap-4 pt-5 border-t border-gold/14">
            <div className="flex items-center gap-3 min-w-0">
              {(() => {
                const author = post.author || ({} as Partial<typeof post.author>);
                const name = author.display_name || "Author";
                const avatar =
                  author.avatar_url ||
                  avatarPlaceholder(author.id || name);
                const verified = !!(author.is_realtor && author.is_verified);
                return (
                  <>
                    <Image
                      src={avatar}
                      alt=""
                      width={28}
                      height={28}
                      className="rounded-full border border-gold/22"
                    />
                    <span className="text-xs text-mist truncate">{name}</span>
                    {verified && (
                      <span
                        title="Verified realtor"
                        aria-label="Verified realtor"
                        className="w-2 h-2 rounded-full bg-gold flex-shrink-0"
                      />
                    )}
                  </>
                );
              })()}
            </div>
            <span className="text-[11px] uppercase tracking-luxe text-dim flex-shrink-0">
              {formatDate(post.published_at)}
            </span>
          </div>
        </CardBody>
      </Card>
    </Link>
  );
}
