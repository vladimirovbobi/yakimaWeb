/**
 * Deterministic placeholder picker — same input always produces the same image.
 *
 * Used by every card and avatar in the platform so a missing API hero_image
 * doesn't leave a hollow rectangle. Drop a real photo into /public/img/<dir>/
 * and update the API to return a real URL — the fallback never fires.
 *
 * Each placeholder JPEG carries a tiny `[demo]` corner pip so production
 * placeholders are visible.
 */

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function pick(seed: string | number, modulo: number): number {
  return (hash(String(seed)) % modulo) + 1;
}

export function postPlaceholder(seed: string | number): string {
  return `/img/posts/post-${pick(seed, 10)}.jpg`;
}

export function servicePlaceholder(seed: string | number): string {
  return `/img/services/service-${pick(seed, 12)}.jpg`;
}

export function avatarPlaceholder(seed: string | number): string {
  return `/img/avatars/avatar-${pick(seed, 8)}.jpg`;
}

export function vendorLogoPlaceholder(seed: string | number): string {
  return `/img/vendors/vendor-logo-${pick(seed, 8)}.jpg`;
}

export function threadPlaceholder(seed: string | number): string {
  return `/img/threads/thread-${pick(seed, 6)}.jpg`;
}

const HERO_BY_SECTION: Record<string, string> = {
  home: "/img/hero/hero-home.jpg",
  blog: "/img/hero/hero-blog.jpg",
  services: "/img/hero/hero-services.jpg",
  community: "/img/hero/hero-community.jpg",
  tools: "/img/hero/hero-tools.jpg",
};

export function heroForSection(section: keyof typeof HERO_BY_SECTION | string): string {
  return HERO_BY_SECTION[section] || HERO_BY_SECTION.home;
}

const EMPTY_BY_KIND: Record<string, string> = {
  leads: "/img/empty/empty-leads.svg",
  posts: "/img/empty/empty-posts.svg",
  services: "/img/empty/empty-services.svg",
  notifications: "/img/empty/empty-notifications.svg",
  search: "/img/empty/empty-search.svg",
};

export function emptyStateImage(kind: keyof typeof EMPTY_BY_KIND | string): string {
  return EMPTY_BY_KIND[kind] || EMPTY_BY_KIND.posts;
}
