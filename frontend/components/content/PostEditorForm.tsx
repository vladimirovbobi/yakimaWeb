"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import RichEditor from "./RichEditor";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import type { Post } from "@/lib/api/types";

interface PostEditorFormProps {
  initial?: {
    slug?: string;
    title: string;
    excerpt: string;
    body: string;
    tag_slugs: string[];
  };
  mode: "create" | "edit";
}

export default function PostEditorForm({ initial, mode }: PostEditorFormProps) {
  const router = useRouter();
  const [title, setTitle] = useState(initial?.title ?? "");
  const [excerpt, setExcerpt] = useState(initial?.excerpt ?? "");
  const [body, setBody] = useState(initial?.body ?? "");
  const [tagsRaw, setTagsRaw] = useState(initial?.tag_slugs?.join(", ") ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);

    const tag_slugs = tagsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      const payload = { title, excerpt, body, tag_slugs };
      const path =
        mode === "create"
          ? "/api/v1/posts/"
          : `/api/v1/posts/${encodeURIComponent(initial?.slug ?? "")}/`;
      const method = mode === "create" ? "POST" : "PATCH";
      const result = await apiFetch<Post>(
        path,
        { method, body: JSON.stringify(payload) },
        { auth: true },
      );
      router.push(`/dashboard/realtor/posts`);
      router.refresh();
      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError("Save failed.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-6">
      <label className="block">
        <span className="ey mb-2 block">Title</span>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          className="w-full bg-deep border border-gold/22 text-ivory px-4 py-3 text-lg"
        />
      </label>

      <label className="block">
        <span className="ey mb-2 block">Excerpt</span>
        <textarea
          value={excerpt}
          onChange={(e) => setExcerpt(e.target.value)}
          rows={2}
          maxLength={300}
          className="w-full bg-deep border border-gold/22 text-mist px-4 py-3"
        />
      </label>

      <div>
        <div className="ey mb-2">Body</div>
        <RichEditor value={body} onChange={setBody} />
      </div>

      <label className="block">
        <span className="ey mb-2 block">Tags (comma-separated)</span>
        <input
          type="text"
          value={tagsRaw}
          onChange={(e) => setTagsRaw(e.target.value)}
          placeholder="market, yakima, trends"
          className="w-full bg-deep border border-gold/22 text-mist px-4 py-3"
        />
      </label>

      {error && (
        <div className="text-rose-300 border border-rose-400/40 bg-rose-400/10 p-3 text-sm">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={busy}
          className="px-5 py-3 border border-gold/40 text-gold uppercase tracking-luxe text-[11px] hover:bg-gold/10 disabled:opacity-50"
        >
          {mode === "create" ? "Create draft" : "Save changes"}
        </button>
      </div>
    </form>
  );
}
