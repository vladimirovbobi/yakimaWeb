import Image from "next/image";
import Script from "next/script";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Container from "@/components/layout/Container";
import ScrollReveal from "@/components/reveal/ScrollReveal";
import PostCard from "@/components/content/PostCard";
import CommentThread from "@/components/content/CommentThread";
import CommentForm from "@/components/content/CommentForm";
import SignInPrompt from "@/components/auth/SignInPrompt";
import { safeServerFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/auth/server";
import { formatDate, pluralize } from "@/lib/utils";
import type { Comment, Pagination, Post } from "@/lib/api/types";

interface PostDetailPageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({
  params,
}: PostDetailPageProps): Promise<Metadata> {
  const { slug } = await params;
  const post = await safeServerFetch<Post>(
    `/api/public/v1/posts/${slug}/`,
    {},
    { cache: "no-store" },
  );
  if (!post) return { title: "Post" };

  const url = `/blog/${post.slug}`;
  return {
    title: post.title,
    description: post.excerpt,
    alternates: { canonical: url },
    openGraph: {
      type: "article",
      title: post.title,
      description: post.excerpt,
      url,
      images: post.hero_image_url ? [post.hero_image_url] : undefined,
      publishedTime: post.published_at,
      modifiedTime: post.updated_at,
      authors: [post.author.display_name],
    },
    twitter: {
      card: "summary_large_image",
      title: post.title,
      description: post.excerpt,
      images: post.hero_image_url ? [post.hero_image_url] : undefined,
    },
  };
}

export default async function PostDetailPage({ params }: PostDetailPageProps) {
  const { slug } = await params;

  const [post, commentsPage, user] = await Promise.all([
    safeServerFetch<Post>(
      `/api/public/v1/posts/${slug}/`,
      {},
      { cache: "no-store" },
    ),
    safeServerFetch<Pagination<Comment>>(
      `/api/public/v1/posts/${slug}/comments/`,
      {},
      { cache: "no-store" },
    ),
    getCurrentUser(),
  ]);

  if (!post) notFound();

  const related = await safeServerFetch<Pagination<Post>>(
    `/api/public/v1/posts/?limit=3&exclude_slug=${slug}`,
    {},
    { cache: "no-store" },
  );

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.excerpt,
    image: post.hero_image_url || undefined,
    author: { "@type": "Person", name: post.author.display_name },
    datePublished: post.published_at,
    dateModified: post.updated_at,
  };

  return (
    <>
      <Script
        id={`ld-post-${post.id}`}
        type="application/ld+json"
        strategy="beforeInteractive"
      >
        {JSON.stringify(jsonLd)}
      </Script>

      {post.hero_image_url && (
        <div className="relative w-full aspect-[21/9] md:aspect-[21/8] bg-black overflow-hidden">
          <Image
            src={post.hero_image_url}
            alt={post.title}
            fill
            priority
            sizes="100vw"
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-black/30" />
        </div>
      )}

      <article className="section-y">
        <Container>
          <header className="max-w-3xl">
            <div className="ey mb-5">
              {post.post_type === "org"
                ? "Yakima Web"
                : post.post_type === "blog"
                  ? "Realtor blog"
                  : "Tool"}
              {" · "}
              {post.reading_time_minutes}{" "}
              {pluralize(post.reading_time_minutes, "min", "min")} read
            </div>
            <h1 className="font-serif font-light text-ivory text-[clamp(2rem,5vw,3.75rem)] leading-[1.05]">
              {post.title}
            </h1>
            <div className="mt-8 flex flex-wrap items-center gap-4 pb-8 border-b border-gold/14">
              {post.author.avatar_url ? (
                <Image
                  src={post.author.avatar_url}
                  alt=""
                  width={40}
                  height={40}
                  className="rounded-full border border-gold/22"
                />
              ) : (
                <div
                  aria-hidden
                  className="w-10 h-10 rounded-full bg-warm border border-gold/22 flex items-center justify-center text-gold"
                >
                  {post.author.display_name.charAt(0).toUpperCase()}
                </div>
              )}
              <div>
                <p className="text-ivory text-sm flex items-center gap-2">
                  {post.author.display_name}
                  {post.author.is_realtor && post.author.is_verified && (
                    <span
                      title="Verified realtor"
                      aria-label="Verified realtor"
                      className="w-2 h-2 rounded-full bg-gold"
                    />
                  )}
                </p>
                <p className="text-[11px] uppercase tracking-luxe text-mist">
                  {formatDate(post.published_at)}
                </p>
              </div>
            </div>
          </header>

          <div
            className="post-body mt-10 max-w-3xl text-ivory text-base md:text-lg leading-[1.85] space-y-6"
            dangerouslySetInnerHTML={{ __html: post.body_html || "" }}
          />

          {post.tags.length > 0 && (
            <div className="mt-12 max-w-3xl flex flex-wrap gap-2">
              {post.tags.map((t) => (
                <span
                  key={t}
                  className="text-[11px] uppercase tracking-luxe text-mist border border-gold/22 px-3 py-1.5"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </Container>
      </article>

      {related && related.results.length > 0 && (
        <section className="section-y bg-deep border-y border-gold/14">
          <Container>
            <ScrollReveal>
              <h2 className="font-serif font-light text-ivory text-3xl mb-10">
                Keep reading
              </h2>
            </ScrollReveal>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {related.results.slice(0, 3).map((r, i) => (
                <ScrollReveal key={r.id} delay={0.05 + i * 0.06}>
                  <PostCard post={r} />
                </ScrollReveal>
              ))}
            </div>
          </Container>
        </section>
      )}

      <section className="section-y">
        <Container>
          <div className="max-w-3xl">
            <h2 className="font-serif font-light text-ivory text-3xl mb-3">
              Comments
            </h2>
            <p className="text-mist text-sm mb-10">
              {post.comment_count}{" "}
              {pluralize(post.comment_count, "comment", "comments")}. AI-moderated
              before publishing.
            </p>

            <div className="mb-12">
              {user ? (
                <CommentForm postSlug={post.slug} />
              ) : (
                <SignInPrompt
                  verb="comment"
                  next={`/blog/${post.slug}`}
                />
              )}
            </div>

            {commentsPage && commentsPage.results.length > 0 ? (
              <CommentThread
                comments={commentsPage.results}
                postSlug={post.slug}
                authed={!!user}
              />
            ) : (
              <p className="text-mist text-sm">
                No comments yet. Be the first to write one.
              </p>
            )}
          </div>
        </Container>
      </section>
    </>
  );
}
