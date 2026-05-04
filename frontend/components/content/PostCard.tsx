import Link from "next/link";
import Image from "next/image";
import type { Post } from "@/lib/api/types";
import { Card, CardBody } from "@/components/ui/Card";
import { formatDate, pluralize } from "@/lib/utils";

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
  return (
    <Link
      href={`/blog/${post.slug}`}
      className="group block h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
    >
      <Card className="h-full overflow-hidden">
        {post.hero_image_url && (
          <div className="relative aspect-[16/10] overflow-hidden">
            <Image
              src={post.hero_image_url}
              alt={post.title}
              fill
              priority={priority}
              sizes="(max-width: 768px) 100vw, (max-width: 1280px) 33vw, 420px"
              className="object-cover transition-transform duration-700 ease-luxe group-hover:scale-[1.04]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
          </div>
        )}
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
              {post.author.avatar_url ? (
                <Image
                  src={post.author.avatar_url}
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
                  {post.author.display_name.charAt(0).toUpperCase()}
                </div>
              )}
              <span className="text-xs text-mist truncate">
                {post.author.display_name}
              </span>
              {post.author.is_realtor && post.author.is_verified && (
                <span
                  title="Verified realtor"
                  aria-label="Verified realtor"
                  className="w-2 h-2 rounded-full bg-gold flex-shrink-0"
                />
              )}
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
