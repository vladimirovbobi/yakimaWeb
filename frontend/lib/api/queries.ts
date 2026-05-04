import { apiFetch } from "./fetch";
import type {
  User,
  Post,
  Comment,
  ForumThread,
  ForumReply,
  Service,
  Category,
  Pagination,
  PostsListParams,
} from "./types";

interface ServicesListParams {
  category?: string;
  q?: string;
  limit?: number;
  cursor?: string;
  has_bundle?: boolean;
  min_price?: number;
  max_price?: number;
}

interface ThreadsListParams {
  flair?: string;
  sort?: "hot" | "new" | "top";
  limit?: number;
  cursor?: string;
}

function qs(params: Record<string, unknown> | undefined) {
  if (!params) return "";
  const usp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v == null || v === "") continue;
    usp.set(k, String(v));
  }
  const s = usp.toString();
  return s ? `?${s}` : "";
}

export const queries = {
  me: () => ({
    queryKey: ["me"],
    queryFn: () => apiFetch<User>("/api/v1/me/", {}, { auth: true }),
  }),
  posts: (params?: PostsListParams) => ({
    queryKey: ["posts", params],
    queryFn: () =>
      apiFetch<Pagination<Post>>(`/api/public/v1/posts/${qs(params)}`),
  }),
  post: (slug: string) => ({
    queryKey: ["post", slug],
    queryFn: () => apiFetch<Post>(`/api/public/v1/posts/${slug}/`),
  }),
  postComments: (slug: string) => ({
    queryKey: ["post", slug, "comments"],
    queryFn: () =>
      apiFetch<Pagination<Comment>>(
        `/api/public/v1/posts/${slug}/comments/`,
      ),
  }),
  services: (params?: ServicesListParams) => ({
    queryKey: ["services", params],
    queryFn: () =>
      apiFetch<Pagination<Service>>(`/api/public/v1/services/${qs(params)}`),
  }),
  service: (slug: string) => ({
    queryKey: ["service", slug],
    queryFn: () => apiFetch<Service>(`/api/public/v1/services/${slug}/`),
  }),
  categories: () => ({
    queryKey: ["categories"],
    queryFn: () =>
      apiFetch<Category[]>("/api/public/v1/services/categories/"),
  }),
  threads: (params?: ThreadsListParams) => ({
    queryKey: ["threads", params],
    queryFn: () =>
      apiFetch<Pagination<ForumThread>>(
        `/api/public/v1/community/threads/${qs(params)}`,
      ),
  }),
  thread: (slug: string) => ({
    queryKey: ["thread", slug],
    queryFn: () =>
      apiFetch<ForumThread>(`/api/public/v1/community/threads/${slug}/`),
  }),
  threadReplies: (slug: string) => ({
    queryKey: ["thread", slug, "replies"],
    queryFn: () =>
      apiFetch<Pagination<ForumReply>>(
        `/api/public/v1/community/threads/${slug}/replies/`,
      ),
  }),
};
