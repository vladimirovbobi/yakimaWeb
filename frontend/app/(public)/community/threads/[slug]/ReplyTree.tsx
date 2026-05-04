"use client";

import { useState } from "react";
import Image from "next/image";
import type { ForumReply } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";
import VoteButton from "@/components/forum/VoteButton";
import ReplyForm from "./ReplyForm";

interface ReplyTreeProps {
  replies: ForumReply[];
  threadSlug: string;
  authed: boolean;
  currentPath: string;
  depth?: number;
}

export default function ReplyTree({
  replies,
  threadSlug,
  authed,
  currentPath,
  depth = 0,
}: ReplyTreeProps) {
  return (
    <div className="space-y-5">
      {replies.map((r) => (
        <ReplyNode
          key={r.id}
          reply={r}
          threadSlug={threadSlug}
          authed={authed}
          currentPath={currentPath}
          depth={depth}
        />
      ))}
    </div>
  );
}

function ReplyNode({
  reply,
  threadSlug,
  authed,
  currentPath,
  depth,
}: {
  reply: ForumReply;
  threadSlug: string;
  authed: boolean;
  currentPath: string;
  depth: number;
}) {
  const [open, setOpen] = useState(false);
  const indent = Math.min(depth, 5);

  return (
    <div style={{ marginLeft: indent * 24 }}>
      <div className="grid grid-cols-[40px_1fr] gap-4 border-l border-gold/14 pl-4 py-3">
        <div className="pt-1">
          <VoteButton
            itemType="reply"
            itemId={reply.id}
            score={reply.vote_score}
            userVote={reply.user_vote}
            authed={authed}
            currentPath={currentPath}
          />
        </div>
        <div>
          <div className="flex items-center gap-3 mb-2 flex-wrap">
            {reply.author.avatar_url ? (
              <Image
                src={reply.author.avatar_url}
                alt=""
                width={24}
                height={24}
                className="rounded-full border border-gold/22"
              />
            ) : (
              <div
                aria-hidden
                className="w-6 h-6 rounded-full bg-warm border border-gold/22 flex items-center justify-center text-[10px] text-gold"
              >
                {reply.author.display_name.charAt(0).toUpperCase()}
              </div>
            )}
            <span className="text-sm text-ivory">
              {reply.author.display_name}
            </span>
            {reply.author.is_realtor && reply.author.is_verified && (
              <span
                title="Verified realtor"
                className="w-2 h-2 rounded-full bg-gold"
              />
            )}
            <span className="text-[11px] uppercase tracking-luxe text-dim">
              {formatDate(reply.created_at)}
            </span>
          </div>
          <div
            className="text-mist text-sm leading-relaxed prose-comment"
            dangerouslySetInnerHTML={{ __html: reply.body_html }}
          />
          {authed && (
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="mt-3 text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
            >
              {open ? "Cancel" : "Reply"}
            </button>
          )}
          {open && (
            <div className="mt-4">
              <ReplyForm
                threadSlug={threadSlug}
                parentId={reply.id}
                onDone={() => setOpen(false)}
              />
            </div>
          )}
        </div>
      </div>
      {reply.replies && reply.replies.length > 0 && (
        <ReplyTree
          replies={reply.replies}
          threadSlug={threadSlug}
          authed={authed}
          currentPath={currentPath}
          depth={depth + 1}
        />
      )}
    </div>
  );
}
