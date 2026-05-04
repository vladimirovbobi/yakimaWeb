import type { Metadata } from "next";

const SITE_NAME = "Yakima Real Estate Hub";
const SITE_BASE = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
const DEFAULT_OG = `${SITE_BASE}/og/default.jpg`;
const TWITTER_HANDLE = "@yakimaweb";

export interface PageMetaInput {
  title: string;
  description: string;
  path: string;
  image?: string;
  type?: "website" | "article" | "profile";
  publishedAt?: string;
  modifiedAt?: string;
  authorName?: string;
  noindex?: boolean;
  keywords?: string[];
}

export function pageMeta(input: PageMetaInput): Metadata {
  const url = `${SITE_BASE}${input.path}`;
  const image = input.image || DEFAULT_OG;
  return {
    title: input.title,
    description: input.description,
    keywords: input.keywords,
    alternates: { canonical: url },
    robots: input.noindex
      ? { index: false, follow: false }
      : { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 },
    openGraph: {
      title: input.title,
      description: input.description,
      url,
      siteName: SITE_NAME,
      type: input.type || "website",
      locale: "en_US",
      images: [{ url: image, width: 1200, height: 630, alt: input.title }],
      ...(input.type === "article" && {
        publishedTime: input.publishedAt,
        modifiedTime: input.modifiedAt,
        authors: input.authorName ? [input.authorName] : undefined,
      }),
    },
    twitter: {
      card: "summary_large_image",
      title: input.title,
      description: input.description,
      images: [image],
      site: TWITTER_HANDLE,
    },
  };
}

export function organizationLD() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": `${SITE_BASE}/#organization`,
    name: SITE_NAME,
    url: SITE_BASE,
    logo: `${SITE_BASE}/icon-512.png`,
    description: "Central Washington's grounded hub for verified realtors, real conversations, and local market truth — Yakima Valley and the wider region.",
    areaServed: { "@type": "Place", name: "Yakima Valley, Washington" },
    sameAs: [],
  };
}

export function websiteLD() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": `${SITE_BASE}/#website`,
    url: SITE_BASE,
    name: SITE_NAME,
    publisher: { "@id": `${SITE_BASE}/#organization` },
    potentialAction: {
      "@type": "SearchAction",
      target: { "@type": "EntryPoint", urlTemplate: `${SITE_BASE}/search?q={query}` },
      "query-input": "required name=query",
    },
  };
}

export function breadcrumbLD(items: Array<{ name: string; path: string }>) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((it, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: it.name,
      item: `${SITE_BASE}${it.path}`,
    })),
  };
}

export function articleLD(input: {
  title: string;
  description: string;
  path: string;
  image?: string;
  publishedAt: string;
  modifiedAt?: string;
  authorName: string;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    "@id": `${SITE_BASE}${input.path}#article`,
    headline: input.title,
    description: input.description,
    image: input.image || DEFAULT_OG,
    datePublished: input.publishedAt,
    dateModified: input.modifiedAt || input.publishedAt,
    author: { "@type": "Person", name: input.authorName },
    publisher: { "@id": `${SITE_BASE}/#organization` },
    mainEntityOfPage: `${SITE_BASE}${input.path}`,
  };
}

export function discussionLD(input: {
  title: string;
  body: string;
  path: string;
  authorName: string;
  createdAt: string;
  replyCount: number;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "DiscussionForumPosting",
    "@id": `${SITE_BASE}${input.path}#discussion`,
    headline: input.title,
    text: input.body.slice(0, 500),
    url: `${SITE_BASE}${input.path}`,
    datePublished: input.createdAt,
    author: { "@type": "Person", name: input.authorName },
    interactionStatistic: {
      "@type": "InteractionCounter",
      interactionType: "https://schema.org/CommentAction",
      userInteractionCount: input.replyCount,
    },
  };
}

export function jsonLDScript(data: object | object[]) {
  return {
    __html: JSON.stringify(data),
  };
}
