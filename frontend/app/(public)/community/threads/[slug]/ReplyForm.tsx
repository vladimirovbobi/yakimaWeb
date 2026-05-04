"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

interface ReplyFormProps {
  threadSlug: string;
  parentId?: number;
  onDone?: () => void;
}

export default function ReplyForm({
  threadSlug,
  parentId,
  onDone,
}: ReplyFormProps) {
  const [body, setBody] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const toast = useToast();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim() || pending) return;
    setPending(true);
    setError(null);
    try {
      await apiFetch(
        `/api/v1/community/threads/${threadSlug}/replies/`,
        {
          method: "POST",
          body: JSON.stringify({ body, parent_id: parentId ?? null }),
        },
        { auth: true },
      );
      setBody("");
      toast.push("Reply submitted for review", "success");
      onDone?.();
      router.refresh();
    } catch (err) {
      const e = err as ApiError;
      setError(e.problem.detail || e.problem.title || "Could not post reply");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={parentId ? 3 : 5}
        required
        placeholder="Stay on topic. No personal attacks."
        className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold transition-colors resize-y"
      />
      {error && <p className="text-err text-xs">{error}</p>}
      <div className="flex items-center gap-3">
        <Button type="submit" variant="solid" size="sm" loading={pending}>
          {parentId ? "Post reply" : "Post"}
        </Button>
        {onDone && (
          <button
            type="button"
            onClick={onDone}
            className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
