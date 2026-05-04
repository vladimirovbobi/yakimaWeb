import { notFound, redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth/server";
import { safeServerFetch } from "@/lib/api/server";
import LeadConversation, {
  type LeadDetail,
  type LeadMessageDto,
} from "./LeadConversation";

export default async function VendorLeadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=/dashboard/vendor/leads/${id}`);

  const lead = await safeServerFetch<LeadDetail>(
    `/api/v1/leads/${id}/`,
    {},
    { auth: true },
  );
  if (!lead) notFound();

  const messagesData = await safeServerFetch<
    { results?: LeadMessageDto[] } | LeadMessageDto[]
  >(`/api/v1/leads/${id}/messages/`, {}, { auth: true });
  const messages: LeadMessageDto[] = Array.isArray(messagesData)
    ? messagesData
    : messagesData?.results || [];

  return (
    <LeadConversation
      currentUserId={user.id}
      lead={lead}
      initialMessages={messages}
    />
  );
}
