import Link from "next/link";
import { Card, CardBody } from "@/components/ui/Card";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import { formatDate } from "@/lib/utils";

export interface FeedPost {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  published_at: string;
  hero_image?: string | null;
  author_name?: string;
  read_minutes?: number;
}

export interface FeedThread {
  id: number;
  slug: string;
  title: string;
  body?: string;
  reply_count: number;
  vote_score: number;
  created_at: string;
  flair?: { label?: string; color?: string } | null;
  author_name?: string;
}

export interface FeedVoice {
  id: number;
  slug?: string;
  name: string;
  brokerage?: string;
  bio?: string;
  verified?: boolean;
  avatar?: string | null;
}

interface Props {
  featured?: FeedPost | null;
  posts: FeedPost[];
  threads: FeedThread[];
  voices: FeedVoice[];
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return "·";
  if (parts.length === 1) return parts[0][0]?.toUpperCase() || "·";
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function readMinutes(excerpt: string | undefined, fallback?: number): number {
  if (fallback) return fallback;
  const words = (excerpt || "").trim().split(/\s+/).length;
  return Math.max(2, Math.round(words / 220) + 4);
}

function FeaturedStory({ post }: { post: FeedPost }) {
  return (
    <ScrollReveal>
      <Link href={`/blog/${post.slug}`} className="block group">
        <Card className="overflow-hidden">
          <div className="grid md:grid-cols-2">
            <div className="relative aspect-[4/3] md:aspect-auto bg-warm overflow-hidden">
              {post.hero_image ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={post.hero_image}
                  alt=""
                  loading="eager"
                  decoding="async"
                  fetchPriority="high"
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 ease-luxe group-hover:scale-[1.03]"
                />
              ) : (
                <div className="absolute inset-0 bg-gradient-to-br from-warm via-deep to-black" aria-hidden />
              )}
              <div className="absolute inset-0 bg-gradient-to-tr from-black/60 via-black/10 to-transparent" aria-hidden />
              <div className="absolute top-5 left-5 ey">Featured</div>
            </div>
            <CardBody className="md:p-10 flex flex-col justify-center">
              <p className="label-luxe mb-4">{formatDate(post.published_at)} · {readMinutes(post.excerpt, post.read_minutes)} min read</p>
              <h2 className="font-serif text-ivory text-[clamp(1.6rem,3vw,2.4rem)] leading-[1.1] font-light group-hover:text-gold-hi transition-colors">
                {post.title}
              </h2>
              <p className="text-mist mt-5 leading-relaxed">{post.excerpt}</p>
              {post.author_name && (
                <div className="mt-7 flex items-center gap-3">
                  <span className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-warm border border-gold/22 text-gold text-xs font-medium">
                    {initials(post.author_name)}
                  </span>
                  <span className="label-luxe">By {post.author_name}</span>
                </div>
              )}
            </CardBody>
          </div>
        </Card>
      </Link>
    </ScrollReveal>
  );
}

function StoryCard({ post, delay }: { post: FeedPost; delay: number }) {
  return (
    <ScrollReveal delay={delay}>
      <Link href={`/blog/${post.slug}`} className="block group h-full">
        <Card className="h-full overflow-hidden">
          <div className="relative aspect-[16/9] bg-warm overflow-hidden">
            {post.hero_image ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={post.hero_image}
                alt=""
                loading="lazy"
                decoding="async"
                className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 ease-luxe group-hover:scale-[1.03]"
              />
            ) : (
              <div className="absolute inset-0 bg-gradient-to-br from-warm via-deep to-black" aria-hidden />
            )}
          </div>
          <CardBody>
            <p className="label-luxe mb-3">
              {formatDate(post.published_at)} · {readMinutes(post.excerpt, post.read_minutes)} min read
            </p>
            <h3 className="font-serif text-xl text-ivory leading-tight font-light mb-3 group-hover:text-gold-hi transition-colors">
              {post.title}
            </h3>
            <p className="text-mist text-sm leading-relaxed line-clamp-3">{post.excerpt}</p>
            {post.author_name && (
              <p className="mt-5 text-[11px] uppercase tracking-luxe text-dim">By {post.author_name}</p>
            )}
          </CardBody>
        </Card>
      </Link>
    </ScrollReveal>
  );
}

function ConversationCard({ thread, delay }: { thread: FeedThread; delay: number }) {
  const flairLabel = thread.flair?.label;
  return (
    <ScrollReveal delay={delay}>
      <Link href={`/community/threads/${thread.slug}`} className="block group h-full">
        <Card className="h-full">
          <CardBody>
            <div className="flex items-center justify-between mb-4">
              {flairLabel ? (
                <span className="text-[10px] uppercase tracking-eyebrow text-gold border border-gold/35 px-2 py-1">
                  {flairLabel}
                </span>
              ) : <span />}
              <span className="label-luxe">{formatDate(thread.created_at)}</span>
            </div>
            <h3 className="font-serif text-lg text-ivory leading-snug font-light mb-3 group-hover:text-gold-hi transition-colors">
              {thread.title}
            </h3>
            {thread.body && (
              <p className="text-mist text-sm leading-relaxed line-clamp-3">{thread.body}</p>
            )}
            <div className="mt-6 flex items-center gap-5 text-[11px] uppercase tracking-luxe text-mist">
              <span>
                <span className="text-ivory">{thread.vote_score}</span> votes
              </span>
              <span>
                <span className="text-ivory">{thread.reply_count}</span> replies
              </span>
              {thread.author_name && (
                <span className="ml-auto text-dim">{thread.author_name}</span>
              )}
            </div>
          </CardBody>
        </Card>
      </Link>
    </ScrollReveal>
  );
}

function VoiceStrip({ voices }: { voices: FeedVoice[] }) {
  if (voices.length === 0) return null;
  return (
    <ScrollReveal>
      <div className="border border-gold/14 bg-deep">
        <div className="px-6 md:px-10 py-7 border-b border-gold/14">
          <p className="ey">Verified voices</p>
          <h3 className="font-serif text-2xl text-ivory leading-tight font-light mt-3">
            Realtors who actually live and work here.
          </h3>
        </div>
        <ul className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-gold/14">
          {voices.slice(0, 3).map((v) => (
            <li key={v.id} className="px-6 md:px-8 py-7">
              <div className="flex items-start gap-4">
                <span className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-warm border border-gold/22 text-gold font-serif text-base flex-shrink-0">
                  {initials(v.name)}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-serif text-lg text-ivory leading-tight font-light">{v.name}</p>
                    {v.verified && (
                      <span className="inline-flex items-center gap-1 text-[9px] uppercase tracking-eyebrow text-gold border border-gold/35 px-1.5 py-0.5">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" aria-hidden>
                          <path d="M5 12l4 4 10-10" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        Verified
                      </span>
                    )}
                  </div>
                  {v.brokerage && (
                    <p className="text-[11px] uppercase tracking-luxe text-dim mt-1">{v.brokerage}</p>
                  )}
                  {v.bio && (
                    <p className="text-mist text-sm mt-3 leading-relaxed line-clamp-3">{v.bio}</p>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
        <div className="px-6 md:px-10 py-5 border-t border-gold/14 flex items-center justify-end">
          <Link href="/realtors" className="inline-flex items-center gap-3 text-xs uppercase tracking-cap text-gold hover:text-gold-hi transition-colors">
            Meet the realtors
            <svg width="14" height="10" viewBox="0 0 16 10" fill="none" aria-hidden>
              <path d="M1 5h13m0 0L10 1m4 4l-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </Link>
        </div>
      </div>
    </ScrollReveal>
  );
}

function NewsletterCard() {
  return (
    <ScrollReveal>
      <div className="border border-gold/22 bg-warm/40 px-6 md:px-10 py-10 md:py-12">
        <div className="grid md:grid-cols-[1fr_auto] gap-8 items-center">
          <div>
            <p className="ey mb-3">Quietly weekly</p>
            <h3 className="font-serif text-2xl md:text-3xl text-ivory leading-tight font-light">
              One thoughtful note about the Yakima Valley each Friday.
            </h3>
            <p className="text-mist mt-4 leading-relaxed text-sm md:text-base max-w-xl">
              No daily blast. No franchise spam. Just one careful read on the local market, the neighborhoods, and the conversations that matter.
            </p>
          </div>
          <Link
            href="/signup"
            className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-7 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors whitespace-nowrap"
          >
            Subscribe free
          </Link>
        </div>
      </div>
    </ScrollReveal>
  );
}

export default function CuratedFeed({ featured, posts, threads, voices }: Props) {
  const lateralPosts = posts.slice(0, 4);
  const lateralThreads = threads.slice(0, 3);

  return (
    <div className="space-y-10 md:space-y-14">
      {featured && <FeaturedStory post={featured} />}

      {(lateralPosts.length > 0 || lateralThreads.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
          {lateralPosts.slice(0, 3).map((post, i) => (
            <StoryCard key={`p-${post.id}`} post={post} delay={0.05 + i * 0.05} />
          ))}
          {lateralThreads.slice(0, 3).map((thread, i) => (
            <ConversationCard key={`t-${thread.id}`} thread={thread} delay={0.05 + i * 0.05} />
          ))}
        </div>
      )}

      <VoiceStrip voices={voices} />

      {lateralPosts.length > 3 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
          {lateralPosts.slice(3).map((post, i) => (
            <StoryCard key={`p2-${post.id}`} post={post} delay={0.05 + i * 0.05} />
          ))}
        </div>
      )}

      <NewsletterCard />
    </div>
  );
}
