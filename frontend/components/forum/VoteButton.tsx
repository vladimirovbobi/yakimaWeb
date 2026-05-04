"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";

type Direction = "up" | "down";

interface VoteButtonProps {
  itemType: "thread" | "reply";
  itemId: number;
  score: number;
  userVote?: 1 | -1 | 0;
  authed: boolean;
  currentPath: string;
}

export default function VoteButton({
  itemType,
  itemId,
  score,
  userVote = 0,
  authed,
  currentPath,
}: VoteButtonProps) {
  const [optimisticScore, setOptimisticScore] = useState(score);
  const [myVote, setMyVote] = useState<1 | -1 | 0>(userVote);
  const router = useRouter();
  const toast = useToast();

  const mutation = useMutation({
    mutationFn: async (dir: Direction) => {
      const value = dir === "up" ? 1 : -1;
      const newVote = myVote === value ? 0 : value;
      return apiFetch(
        `/api/v1/forum/items/${itemId}/vote/`,
        {
          method: "POST",
          body: JSON.stringify({ value: newVote, item_type: itemType }),
        },
        { auth: true },
      );
    },
    onMutate: (dir) => {
      const value = dir === "up" ? 1 : -1;
      const newVote: 1 | -1 | 0 = myVote === value ? 0 : value;
      setOptimisticScore((s) => s - myVote + newVote);
      setMyVote(newVote);
    },
    onError: (err) => {
      const e = err as ApiError;
      setOptimisticScore(score);
      setMyVote(userVote);
      if (e.status === 401) {
        const url = `/login?next=${encodeURIComponent(currentPath)}`;
        router.push(url);
        return;
      }
      toast.push(e.problem.detail || "Vote failed", "error");
    },
    onSuccess: () => {
      router.refresh();
    },
  });

  function vote(dir: Direction) {
    if (!authed) {
      router.push(`/login?next=${encodeURIComponent(currentPath)}`);
      return;
    }
    mutation.mutate(dir);
  }

  return (
    <div className="flex flex-col items-center gap-1 select-none">
      <button
        type="button"
        onClick={() => vote("up")}
        aria-label="Upvote"
        aria-pressed={myVote === 1}
        className={cn(
          "inline-flex items-center justify-center w-11 h-11 transition-colors",
          myVote === 1 ? "text-gold" : "text-dim hover:text-mist",
        )}
      >
        <svg width="18" height="14" viewBox="0 0 18 14" fill="none" aria-hidden>
          <path
            d="M1 11l8-8 8 8"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      <span className="font-serif text-lg text-ivory leading-none">
        {optimisticScore}
      </span>
      <button
        type="button"
        onClick={() => vote("down")}
        aria-label="Downvote"
        aria-pressed={myVote === -1}
        className={cn(
          "inline-flex items-center justify-center w-11 h-11 transition-colors",
          myVote === -1 ? "text-err" : "text-dim hover:text-mist",
        )}
      >
        <svg width="18" height="14" viewBox="0 0 18 14" fill="none" aria-hidden>
          <path
            d="M1 3l8 8 8-8"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  );
}
