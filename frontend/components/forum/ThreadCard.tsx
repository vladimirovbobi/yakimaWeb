import Link from "next/link";
import type { ForumThread } from "@/lib/api/types";
import { formatDate, pluralize } from "@/lib/utils";

const FLAIR_LABEL: Record<string, string> = {
  buying: "Buying",
  selling: "Selling",
  market: "Market",
  renting: "Renting",
  ask: "Ask Yakima",
  vendors: "Vendors",
  neighborhood: "Neighborhoods",
  general: "General",
};

interface ThreadCardProps {
  thread: ForumThread;
  showFlair?: boolean;
}

export default function ThreadCard({
  thread,
  showFlair = true,
}: ThreadCardProps) {
  const flairLabel = FLAIR_LABEL[thread.flair] || thread.flair;
  return (
    <Link
      href={`/community/threads/${thread.slug}`}
      className="block group border border-gold/14 hover:border-gold/35 transition-colors bg-deep"
    >
      <div className="p-5 md:p-6 flex gap-5">
        <div className="flex flex-col items-center gap-1 flex-shrink-0 w-12">
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
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            {showFlair && (
              <span className="text-[10px] uppercase tracking-luxe text-gold border border-gold/30 px-2 py-1">
                {flairLabel}
              </span>
            )}
            <span className="text-[11px] uppercase tracking-luxe text-mist truncate">
              by {thread.author.display_name}
            </span>
            {thread.author.is_realtor && thread.author.is_verified && (
              <span
                title="Verified realtor"
                aria-label="Verified realtor"
                className="w-2 h-2 rounded-full bg-gold"
              />
            )}
          </div>
          <h3 className="font-serif text-xl text-ivory font-light leading-tight group-hover:text-gold-hi transition-colors mb-3">
            {thread.title}
          </h3>
          <div className="flex items-center gap-5 text-[11px] uppercase tracking-luxe text-mist">
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
