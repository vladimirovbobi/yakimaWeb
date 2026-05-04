import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import NotificationsClient from "./NotificationsClient";

export interface NotificationDto {
  id: number;
  kind: string;
  title: string;
  body: string;
  link: string;
  is_read: boolean;
  created_at: string;
}

const KINDS = [
  "all",
  "lead_received",
  "lead_message",
  "lead_won",
  "review_received",
  "comment_reply",
  "forum_reply",
  "mod_decision",
  "vendor_approved",
  "license_expiring_soon",
] as const;

export default async function NotificationsPage({
  searchParams,
}: {
  searchParams: Promise<{ filter?: string; kind?: string; cursor?: string }>;
}) {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/notifications");

  const params = await searchParams;
  const filter = params.filter === "unread" ? "unread" : "all";
  const kind = (params.kind && KINDS.includes(params.kind as (typeof KINDS)[number]))
    ? params.kind
    : "all";

  const qs = new URLSearchParams();
  if (filter === "unread") qs.set("unread", "1");
  if (kind !== "all") qs.set("kind", kind);
  if (params.cursor) qs.set("cursor", params.cursor);

  const data = await safeServerFetch<
    { results?: NotificationDto[]; next?: string; previous?: string }
    | NotificationDto[]
  >(`/api/v1/me/notifications/?${qs.toString()}`, {}, { auth: true });

  const results: NotificationDto[] = Array.isArray(data)
    ? data
    : data?.results || [];
  const next = !Array.isArray(data) ? data?.next || null : null;
  const previous = !Array.isArray(data) ? data?.previous || null : null;

  return (
    <NotificationsClient
      filter={filter}
      kind={kind}
      kinds={KINDS as unknown as string[]}
      items={results}
      nextUrl={next}
      previousUrl={previous}
    />
  );
}
