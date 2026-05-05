import Link from "next/link";
import Image from "next/image";
import type { ForumThread } from "@/lib/api/types";
import { formatDate, pluralize } from "@/lib/utils";
import { threadPlaceholder } from "@/lib/placeholders";

interface ThreadCardProps {
  thread: ForumThread;
  showFlair?: boolean;
}

export default function ThreadCard({
  thread,
  showFlair = true,
}: ThreadCardProps) {
  const flairLabel = thread.flair?.label || thread.flair?.slug || "Forum";
  const thumbSrc = threadPlaceholder(thread.slug || thread.id);
  return (
    <Link
      href={`/community/threads/${thread.slug}`}
      className="block group border border-gold/14 hover:border-gold/35 transition-colors bg-deep"
    >
      <div className="p-4 sm:p-5 md:p-6 flex flex-col sm:flex-row gap-3 sm:gap-5">
        <div className="hidden sm:flex flex-col items-center gap-1 flex-shrink-0 w-12">
          <svg
            width="14"
            height="10"
            viewBox="0 0 14 10"
            fill="none"
            className="text-dim"
            aria-hidden
          >
            <path
              d="M1 8l6-6 6 6"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="font-serif text-2xl text-ivory leading-none">
            {thread.vote_score}
          </span>
          <span className="text-[10px] uppercase tracking-luxe text-dim">
            votes
          </span>
        </div>
        <div className="hidden md:block flex-shrink-0 relative w-[240px] aspect-[16/9] overflow-hidden bg-warm border border-gold/14">
          <Image
            src={thumbSrc}
            alt=""
            fill
            sizes="240px"
            className="object-cover transition-transform duration-700 ease-luxe group-hover:scale-[1.03]"
          />
        </div>
        <div className="flex sm:hidden items-center gap-2 text-[11px] uppercase tracking-luxe text-dim">
          <svg
            width="12"
            height="8"
            viewBox="0 0 14 10"
            fill="none"
            aria-hidden
          >
            <path
              d="M1 8l6-6 6 6"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="font-serif text-base text-ivory">
            {thread.vote_score}
          </span>
          <span>votes</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
            {showFlair && (
              <span className="text-[10px] uppercase tracking-luxe text-gold border border-gold/30 px-2 py-1">
                {flairLabel}
              </span>
            )}
            <span className="text-[11px] uppercase tracking-luxe text-mist truncate max-w-full">
              by {thread.author.display_name}
            </span>
            {thread.author.is_realtor && thread.author.is_verified && (
              <span
                title="Verified realtor"
                aria-label="Verified realtor"
                className="w-2 h-2 rounded-full bg-gold flex-shrink-0"
              />
            )}
          </div>
          <h3 className="font-serif text-lg sm:text-xl text-ivory font-light leading-tight group-hover:text-gold-hi transition-colors mb-3">
            {thread.title}
          </h3>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] uppercase tracking-luxe text-mist">
            <span>
              <span className="text-ivory">{thread.reply_count}</span>{" "}
              {pluralize(thread.reply_count, "reply", "replies")}
            </span>
            <span>{formatDate(thread.last_activity_at)}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
