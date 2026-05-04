"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";

interface CommentFormProps {
  postSlug: string;
  parentId?: number;
  onDone?: () => void;
}

const MAX_BYTES = 10 * 1024 * 1024;

export default function CommentForm({
  postSlug,
  parentId,
  onDone,
}: CommentFormProps) {
  const [body, setBody] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const toast = useToast();

  function pickImage(file: File | null) {
    if (!file) {
      setImage(null);
      setImagePreview(null);
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("Image exceeds 10 MB.");
      return;
    }
    setImage(file);
    setImagePreview(URL.createObjectURL(file));
  }

  function clearImage() {
    if (imagePreview) URL.revokeObjectURL(imagePreview);
    setImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim() || pending) return;
    setPending(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append("body", body);
      if (parentId) fd.append("parent", String(parentId));
      if (image) fd.append("image", image);

      // Send via fetch directly to preserve multipart Content-Type.
      const BASE =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const res = await fetch(`${BASE}/api/v1/posts/${postSlug}/comments/`, {
        method: "POST",
        body: fd,
        credentials: "include",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      });
      if (!res.ok) {
        const json = await res.json().catch(() => ({}));
        throw new ApiError({
          status: res.status,
          title: json?.title || res.statusText || "Request failed",
          detail: json?.detail,
          ...json,
        });
      }
      setBody("");
      clearImage();
      toast.push("Comment submitted for review", "success");
      onDone?.();
      router.refresh();
    } catch (err) {
      const e = err as ApiError;
      setError(e.problem?.detail || e.problem?.title || "Failed to post comment");
    } finally {
      setPending(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="space-y-3"
      encType="multipart/form-data"
    >
      <label className="block text-[11px] uppercase tracking-luxe text-mist">
        {parentId ? "Your reply" : "Add a comment"}
      </label>
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={4}
        required
        placeholder="Stay on topic. No personal attacks."
        className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold transition-colors resize-y"
      />

      <div className="flex flex-wrap items-center gap-3">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          onChange={(e) => pickImage(e.target.files?.[0] ?? null)}
          className="hidden"
          id={`comment-image-${parentId ?? "root"}`}
        />
        <label
          htmlFor={`comment-image-${parentId ?? "root"}`}
          data-touch
          className="inline-flex items-center gap-2 min-h-11 px-3 py-2 border border-gold/22 text-mist text-[11px] uppercase tracking-luxe cursor-pointer hover:border-gold/40"
        >
          {image ? "Change image" : "Attach image"}
        </label>
        {image && (
          <button
            type="button"
            onClick={clearImage}
            className="text-[11px] uppercase tracking-luxe text-rose-300"
          >
            Remove
          </button>
        )}
      </div>

      {imagePreview && (
        <div className="border border-gold/22 p-2 inline-block">
          <img
            src={imagePreview}
            alt="Preview"
            className="max-h-40 max-w-full object-contain"
          />
        </div>
      )}

      {error && <p className="text-err text-xs" role="alert">{error}</p>}
      <div className="flex flex-col-reverse sm:flex-row sm:items-center gap-3">
        <Button
          type="submit"
          variant="solid"
          size="sm"
          loading={pending}
          className="w-full sm:w-auto"
        >
          Post comment
        </Button>
        {onDone && (
          <button
            type="button"
            onClick={onDone}
            className="min-h-11 text-[11px] uppercase tracking-luxe text-mist hover:text-gold"
          >
            Cancel
          </button>
        )}
      </div>
      <p className="text-xs text-dim">
        Comments are moderated by AI before publishing. Image uploads run a
        separate vision moderation pass.
      </p>
    </form>
  );
}
