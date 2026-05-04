"use client";

import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

export interface ApiMessage {
  id: number;
  sender: { id: number; display_name?: string; email?: string };
  body: string;
  created_at: string;
}

interface Props {
  messages: ApiMessage[];
  currentUserId: number;
}

export default function MessageList({ messages, currentUserId }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [messages.length]);

  return (
    <div
      ref={ref}
      className="flex flex-col gap-3 overflow-y-auto max-h-[60vh] py-4"
      role="log"
      aria-live="polite"
    >
      {messages.length === 0 ? (
        <p className="text-sm text-mist text-center py-12">
          No messages yet. Start the conversation below.
        </p>
      ) : (
        messages.map((m) => (
          <MessageBubble
            key={m.id}
            body={m.body}
            senderName={m.sender.display_name || m.sender.email || "User"}
            isMine={m.sender.id === currentUserId}
            createdAt={m.created_at}
          />
        ))
      )}
    </div>
  );
}
