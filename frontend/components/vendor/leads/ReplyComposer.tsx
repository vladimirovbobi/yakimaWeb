"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";

interface Props {
  onSend: (body: string) => Promise<void>;
}

export default function ReplyComposer({ onSend }: Props) {
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const text = body.trim();
    if (!text) return;
    setSending(true);
    setError(null);
    try {
      await onSend(text);
      setBody("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="border-t border-gold/14 pt-4">
      <textarea
        rows={3}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        onKeyDown={(e) => {
          if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            void send();
          }
        }}
        placeholder="Type your reply…"
        className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
      />
      <div className="flex justify-between items-center mt-2">
        <p className="text-[10px] uppercase tracking-luxe text-dim">
          Ctrl/Cmd + Enter to send
        </p>
        <Button
          type="button"
          variant="solid"
          size="sm"
          loading={sending}
          onClick={send}
        >
          Send
        </Button>
      </div>
      {error && <p role="alert" className="mt-2 text-xs text-err">{error}</p>}
    </div>
  );
}
