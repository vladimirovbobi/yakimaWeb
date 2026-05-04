import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import VoteButton from "@/components/forum/VoteButton";
import SignInPrompt from "@/components/auth/SignInPrompt";
import FeaturedServices from "@/components/marketing/FeaturedServices";
import { safeServerFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth/server";
import type { ForumReply, ForumThread, Pagination } from "@/lib/api/types";
import { formatDate, pluralize } from "@/lib/utils";
import ReplyForm from "./ReplyForm";
import ReplyTree from "./ReplyTree";

interface ThreadPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({
  params,
}: ThreadPageProps): Promise<Metadata> {
  const { slug } = await params;
  const thread = await safeServerFetch<ForumThread>(
    `/api/public/v1/community/threads/${slug}/`,
    {},
    { cache: "no-store" },
  );
  if (!thread) return { title: "Thread" };
  return {
    title: thread.title,
    description: thread.body_html
      .replace(/<[^>]*>/g, "")
      .slice(0, 160),
  };
}

export default async function ThreadPage({ params }: ThreadPageProps) {
  const { slug } = await params;

  const [thread, repliesPage, user] = await Promise.all([
    safeServerFetch<ForumThread>(
      `/api/public/v1/community/threads/${slug}/`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<ForumReply>>(
      `/api/public/v1/community/threads/${slug}/replies/?limit=200`,
      {},
      { cache: "no-store" },
    ),
    getCurrentUser(),
  ]);

  if (!thread) notFound();

  const path = `/community/threads/${thread.slug}`;

  return (
    <section className="section-y">
      <Container>
        <Link
          href={`/community/${thread.flair}`}
          className="inline-flex items-center gap-2 text-[11px] uppercase tracking-luxe text-mist hover:text-gold mb-8"
        >
          <svg
            width="12"
            height="10"
            viewBox="0 0 12 10"
            fill="none"
            aria-hidden
          >
            <path
              d="M11 5H1m0 0l4-4M1 5l4 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Back to {thread.flair}
        </Link>

        <article className="grid grid-cols-[60px_1fr] gap-6 max-w-4xl">
          <div className="pt-1">
            <VoteButton
              itemType="thread"
              itemId={thread.id}
              score={thread.vote_score}
              userVote={thread.user_vote}
              authed={!!user}
              currentPath={path}
            />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-3">
              <Link
                href={`/community/${thread.flair}`}
                className="text-[10px] uppercase tracking-luxe text-gold border border-gold/30 px-2 py-1 hover:bg-gold/10"
              >
                {thread.flair}
              </Link>
              <span className="text-[11px] uppercase tracking-luxe text-mist flex items-center gap-2">
                {thread.author.avatar_url ? (
                  <Image
                    src={thread.author.avatar_url}
                    alt=""
                    width={20}
                    height={20}
                    className="rounded-full border border-gold/22"
                  />
                ) : null}
                {thread.author.display_name}
                {thread.author.is_realtor && thread.author.is_verified && (
                  <span
                    title="Verified realtor"
                    className="w-2 h-2 rounded-full bg-gold"
                  />
                )}
                {" · "}
                {formatDate(thread.created_at)}
              </span>
            </div>
            <h1 className="font-serif font-light text-ivory text-[clamp(1.75rem,3.5vw,2.75rem)] leading-[1.15] mb-6">
              {thread.title}
            </h1>
            <div
              className="prose-page text-ivory leading-[1.85]"
              dangerouslySetInnerHTML={{ __html: thread.body_html }}
            />
            <p className="mt-8 text-[11px] uppercase tracking-luxe text-mist border-t border-gold/14 pt-4">
              {thread.reply_count}{" "}
              {pluralize(thread.reply_count, "reply", "replies")}
            </p>
          </div>
        </article>

        <div className="mt-12 max-w-4xl">
          <FeaturedServices
            contextKind={`forum/${thread.flair || "general"}`}
            seedKey={thread.slug}
            limit={2}
            heading="Vendors who handle this kind of work"
            subheading="Pulled from the marketplace based on this thread."
          />
        </div>

        <div className="mt-12 max-w-4xl">
          <h2 className="font-serif font-light text-ivory text-2xl mb-6">
            Add a reply
          </h2>
          {user ? (
            <ReplyForm threadSlug={thread.slug} />
          ) : (
            <SignInPrompt verb="reply" next={path} />
          )}
        </div>

        <div className="mt-12 max-w-4xl">
          <h2 className="font-serif font-light text-ivory text-2xl mb-6">
            Replies
          </h2>
          {repliesPage && repliesPage.results.length > 0 ? (
            <ReplyTree
              replies={repliesPage.results}
              threadSlug={thread.slug}
              authed={!!user}
              currentPath={path}
            />
          ) : (
            <p className="text-mist text-sm">No replies yet.</p>
          )}
        </div>
      </Container>
    </section>
  );
}
