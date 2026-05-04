export interface User {
  id: number;
  email: string;
  display_name: string;
  is_realtor: boolean;
  is_vendor: boolean;
  is_staff: boolean;
  avatar_url?: string | null;
  bio?: string | null;
  created_at?: string;
}

export interface RealtorProfile {
  id: number;
  user_id: number;
  display_name: string;
  license_number: string;
  license_state: string;
  verified_at: string | null;
  brokerage: string | null;
  bio: string | null;
  avatar_url: string | null;
  is_verified: boolean;
}

export interface VendorProfile {
  id: number;
  user_id: number;
  business_name: string;
  slug: string;
  tagline: string | null;
  about: string | null;
  logo_url: string | null;
  hero_url: string | null;
  category_slug: string | null;
  service_area: string | null;
  rating_avg: number | null;
  rating_count: number;
  is_verified: boolean;
  onboarding_complete: boolean;
}

export interface Author {
  id: number;
  display_name: string;
  avatar_url: string | null;
  is_realtor: boolean;
  is_verified: boolean;
}

export type PostType = "org" | "blog" | "lead-magnet";

export interface Post {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  body_html?: string;
  hero_image_url: string | null;
  post_type: PostType;
  reading_time_minutes: number;
  author: Author;
  published_at: string;
  updated_at: string;
  comment_count: number;
  tags: string[];
}

export interface Comment {
  id: number;
  body_html: string;
  author: Author;
  parent_id: number | null;
  replies?: Comment[];
  created_at: string;
  is_removed: boolean;
}

export type Flair =
  | "buying"
  | "selling"
  | "market"
  | "renting"
  | "ask"
  | "vendors"
  | "neighborhood"
  | "general";

export interface ForumThread {
  id: number;
  slug: string;
  title: string;
  body_html: string;
  flair: Flair;
  author: Author;
  vote_score: number;
  reply_count: number;
  created_at: string;
  last_activity_at: string;
  user_vote?: 1 | -1 | 0;
}

export interface ForumReply {
  id: number;
  body_html: string;
  author: Author;
  parent_id: number | null;
  vote_score: number;
  replies?: ForumReply[];
  created_at: string;
  user_vote?: 1 | -1 | 0;
}

export interface Category {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  parent_id: number | null;
  children?: Category[];
  service_count?: number;
}

export interface Package {
  id: number;
  service_id: number;
  name: string;
  price: number;
  description: string;
  delivery_days: number | null;
  features: string[];
}

export interface Service {
  id: number;
  slug: string;
  title: string;
  tagline: string;
  description_html?: string;
  hero_image_url: string | null;
  gallery: string[];
  vendor: VendorProfile;
  category: Category;
  starting_price: number | null;
  rating_avg: number | null;
  rating_count: number;
  packages?: Package[];
  faq?: Array<{ question: string; answer: string }>;
}

export interface Bundle {
  id: number;
  slug: string;
  name: string;
  vendor: VendorProfile;
  services: Service[];
  total_price: number;
  bundle_price: number;
  savings: number;
}

export interface Lead {
  id: number;
  service_id: number;
  vendor_id: number;
  buyer_id: number;
  package_id: number | null;
  status: "new" | "viewed" | "responded" | "converted" | "closed";
  message: string;
  created_at: string;
}

export interface Review {
  id: number;
  service_id: number;
  reviewer: Author;
  rating: number;
  body: string;
  created_at: string;
  vendor_response?: string;
}

export interface Flag {
  id: number;
  content_type: string;
  object_id: number;
  reason: string;
  reporter_id: number;
  created_at: string;
  status: "pending" | "approved" | "rejected";
}

export interface ModerationDecision {
  id: number;
  content_type: string;
  object_id: number;
  decision: "approve" | "remove" | "shadow" | "edit-required";
  reason: string;
  layer: 1 | 2 | 3;
  ai_confidence: number;
  decided_at: string;
}

export interface SocialEmbed {
  id: number;
  platform: "youtube" | "instagram";
  embed_url: string;
  title: string;
  thumbnail_url: string | null;
  posted_at: string;
}

export interface Pagination<T> {
  next: string | null;
  previous: string | null;
  results: T[];
  count?: number;
}

export interface ProblemDetail {
  type?: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: Record<string, string[]>;
  code?: string;
}

export interface PostsListParams {
  type?: PostType;
  limit?: number;
  cursor?: string;
}

export type ModTargetType =
  | "post"
  | "comment"
  | "forum_thread"
  | "forum_reply"
  | "service"
  | "lead_message"
  | "review"
  | "vendor_tagline";

export interface QueueItem {
  id: number;
  target_type: ModTargetType | string;
  target_id: number;
  target_excerpt: string;
  target_full_url: string;
  reason_flag: string | null;
  classifier_output: {
    allowed: boolean | null;
    categories: string[];
    severity: number | null;
  };
  severity: number | null;
  created_at: string;
}

export interface ActionTemplate {
  slug: string;
  label: string;
  action: "approve" | "remove";
  default_reason: string;
  notify_template_id?: string;
  is_active?: boolean;
  sort_order?: number;
}

export interface ModeratorStats {
  items_reviewed_30d: number;
  items_reviewed_7d: number;
  agreement_rate: number;
  reversal_rate: number;
  avg_response_minutes: number;
  current_streak: number;
  queue_position: number;
  timeseries_30d: Array<{ day: string; count: number }>;
}

export interface InvestigateUserResult {
  user: User;
  recent_posts: Array<{
    id: number;
    kind: string;
    excerpt: string;
    created_at?: string;
    moderation_status?: string;
  }>;
  recent_comments: Array<{
    id: number;
    kind: string;
    excerpt: string;
    created_at?: string;
    moderation_status?: string;
  }>;
  recent_threads: Array<{ id: number; excerpt: string; moderation_status?: string }>;
  recent_replies: Array<{ id: number; excerpt: string; moderation_status?: string }>;
  recent_flags_against: Array<{
    id: number;
    reporter: Author;
    reason_category: string;
    reason_text: string;
    status: string;
    created_at: string;
  }>;
  recent_decisions: Array<{
    id: number;
    target_type: string;
    target_id: number;
    target_excerpt: string;
    action: string;
    severity: number | null;
    moderated_at: string;
  }>;
  total_warnings: number;
  last_seen: string | null;
  account_age_days: number;
  pattern_signals: string[];
  post_count_24h: number;
  recent_decision_count_30d: number;
}

export interface Escalation {
  id: number;
  target_type: string;
  target_id: number;
  target_excerpt: string;
  severity: number | null;
  notes: string;
  escalated_by: Author;
  created_at: string;
}

export interface Tag {
  id: number;
  slug: string;
  name: string;
  post_count: number;
}
