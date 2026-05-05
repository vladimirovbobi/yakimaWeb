"use client";

import { useState } from "react";
import Image from "next/image";
import type { Comment as CommentType } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";
import { avatarPlaceholder } from "@/lib/placeholders";
import CommentForm from "./CommentForm";
import CommentThread from "./CommentThread";

interface CommentProps {
  comment: CommentType;
  postSlug: string;
  authed: boolean;
  depth?: number;
}

export default function Comment({
  comment,
  postSlug,
  authed,
  depth = 0,
}: CommentProps) {
  const [replyOpen, setReplyOpen] = useState(false);
  const indent = Math.min(depth, 4);

  if (comment.is_removed) {
    return (
      <div
        className="border-l border-gold/14 pl-4 py-2 text-xs text-dim italic"
        style={{ marginLeft: indent * 20 }}
      >
        [removed by moderation]
      </div>
    );
  }

  return (
    <div style={{ marginLeft: indent * 20 }}>
      <div className="border-l border-gold/14 pl-4 py-3">
        <div className="flex items-center gap-3 mb-2">
          <Image
            src={
              comment.author.avatar_url ||
              avatarPlaceholder(
                comment.author.id || comment.author.display_name,
              )
            }
            alt=""
            width={24}
            height={24}
            className="rounded-full border border-gold/22"
          />
          <span className="text-sm text-ivory">
            {comment.author.display_name}
          </span>
          {comment.author.is_realtor && comment.author.is_verified && (
            <span
              title="Verified realtor"
              aria-label="Verified realtor"
              className="w-2 h-2 rounded-full bg-gold flex-shrink-0"
            />
          )}
          <span className="text-[11px] uppercase tracking-luxe text-dim ml-auto">
            {formatDate(comment.created_at)}
          </span>
        </div>
        <div
          className="text-mist text-sm leading-relaxed prose-comment"
          dangerouslySetInnerHTML={{ __html: comment.body_html }}
        />
        {authed && (
          <button
            type="button"
            onClick={() => setReplyOpen((v) => !v)}
            className="mt-3 text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
          >
            {replyOpen ? "Cancel" : "Reply"}
          </button>
        )}
        {replyOpen && (
          <div className="mt-4">
            <CommentForm
              postSlug={postSlug}
              parentId={comment.id}
              onDone={() => setReplyOpen(false)}
            />
          </div>
        )}
      </div>
      {comment.replies && comment.replies.length > 0 && (
        <CommentThread
          comments={comment.replies}
          postSlug={postSlug}
          authed={authed}
          depth={depth + 1}
        />
      )}
    </div>
  );
}
