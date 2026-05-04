import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import type { ActionTemplate, Pagination, QueueItem } from "@/lib/api/types";
import QueueWorkstation from "@/components/mod/QueueWorkstation";

export default async function ModQueuePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/dashboard/mod/queue");
  if (!user.is_staff) redirect("/dashboard");

  const [nextItem, templates, queueList] = await Promise.all([
    safeServerFetch<QueueItem | { detail: string }>(
      "/api/v1/mod/queue/next/",
      { method: "GET" },
      { auth: true },
    ),
    safeServerFetch<ActionTemplate[]>(
      "/api/v1/mod/templates/",
      { method: "GET" },
      { auth: true },
    ),
    safeServerFetch<Pagination<QueueItem>>(
      "/api/v1/mod/queue/?limit=1",
      { method: "GET" },
      { auth: true },
    ),
  ]);

  const initialItem =
    nextItem && typeof nextItem === "object" && "id" in nextItem
      ? (nextItem as QueueItem)
      : null;
  const queueDepth = queueList?.count ?? queueList?.results?.length ?? 0;

  return (
    <div className="max-w-6xl">
      <div className="ey mb-3">Moderation</div>
      <h1 className="font-serif font-light text-ivory text-[clamp(1.75rem,3.5vw,2.25rem)] leading-tight mb-8">
        Review queue
      </h1>

      <QueueWorkstation
        initialItem={initialItem}
        initialTemplates={templates ?? []}
        totalQueueDepth={queueDepth}
      />
    </div>
  );
}
