import Link from "next/link";
import LeadStatusPill, { type LeadStatus } from "./LeadStatusPill";

export interface LeadCardData {
  id: number;
  buyer: { display_name?: string; email?: string };
  service?: { title?: string } | null;
  bundle?: { name?: string } | null;
  status: LeadStatus | string;
  message_excerpt: string;
  created_at: string;
}

export default function LeadCard({ lead }: { lead: LeadCardData }) {
  const buyer = lead.buyer.display_name || lead.buyer.email || "Buyer";
  const headline = lead.service?.title || lead.bundle?.name || "Inquiry";
  return (
    <Link
      href={`/dashboard/vendor/leads/${lead.id}`}
      className="block border border-gold/14 hover:border-gold/40 bg-panel/50 p-5 rounded-md transition-colors"
    >
      <div className="flex items-center justify-between gap-3 mb-2">
        <p className="font-serif text-lg text-ivory truncate">{buyer}</p>
        <LeadStatusPill status={lead.status} />
      </div>
      <p className="text-[11px] uppercase tracking-luxe text-gold mb-2">
        {headline}
      </p>
      <p className="text-sm text-mist line-clamp-2">{lead.message_excerpt}</p>
      <p className="mt-3 text-[10px] uppercase tracking-luxe text-dim">
        {new Date(lead.created_at).toLocaleString()}
      </p>
    </Link>
  );
}
