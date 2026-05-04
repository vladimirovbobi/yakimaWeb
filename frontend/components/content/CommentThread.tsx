import type { Comment as CommentType } from "@/lib/api/types";
import Comment from "./Comment";

interface CommentThreadProps {
  comments: CommentType[];
  postSlug: string;
  authed: boolean;
  depth?: number;
}

export default function CommentThread({
  comments,
  postSlug,
  authed,
  depth = 0,
}: CommentThreadProps) {
  if (!comments || comments.length === 0) {
    if (depth === 0) {
      return (
        <p className="text-mist text-sm">
          No comments yet. Be the first to write one.
        </p>
      );
    }
    return null;
  }
  return (
    <div className="space-y-2">
      {comments.map((c) => (
        <Comment
          key={c.id}
          comment={c}
          postSlug={postSlug}
          authed={authed}
          depth={depth}
        />
      ))}
    </div>
  );
}
