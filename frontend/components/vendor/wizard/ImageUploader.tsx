"use client";

import { useRef, useState } from "react";
import { cn } from "@/lib/utils";

export interface UploadedImage {
  url: string;
  alt: string;
  caption: string;
}

interface Props {
  value: UploadedImage[];
  onChange: (next: UploadedImage[]) => void;
  uploadType?: "service-hero" | "gallery";
  max?: number;
  reorderable?: boolean;
}

export default function ImageUploader({
  value,
  onChange,
  uploadType = "gallery",
  max = 12,
  reorderable = true,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const dragIdx = useRef<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFiles(files: FileList) {
    if (!files.length) return;
    setBusy(true);
    setError(null);
    try {
      const fresh: UploadedImage[] = [];
      for (const file of Array.from(files)) {
        if (value.length + fresh.length >= max) break;
        // Backend endpoint TODO: /api/v1/uploads/?type=<uploadType>
        // For now, fall back to creating a local object URL preview so the
        // wizard remains usable; the URL is replaced once the upload endpoint
        // ships in Sprint 5.
        const fd = new FormData();
        fd.append("file", file);
        let uploaded: { url: string; alt?: string } | null = null;
        try {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/api/v1/uploads/?type=${uploadType}`,
            { method: "POST", body: fd, credentials: "include" },
          );
          if (res.ok) uploaded = await res.json();
        } catch {
          // network/endpoint not ready
        }
        const url = uploaded?.url || URL.createObjectURL(file);
        fresh.push({ url, alt: uploaded?.alt || file.name, caption: "" });
      }
      onChange([...value, ...fresh].slice(0, max));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function setAt(i: number, patch: Partial<UploadedImage>) {
    const next = value.slice();
    next[i] = { ...next[i], ...patch };
    onChange(next);
  }

  function remove(i: number) {
    onChange(value.filter((_, idx) => idx !== i));
  }

  function onDragStart(i: number) {
    if (!reorderable) return;
    dragIdx.current = i;
  }

  function onDragOver(e: React.DragEvent) {
    if (!reorderable) return;
    e.preventDefault();
  }

  function onDrop(targetIdx: number) {
    if (!reorderable) return;
    const from = dragIdx.current;
    if (from === null || from === targetIdx) return;
    const next = value.slice();
    const [moved] = next.splice(from, 1);
    next.splice(targetIdx, 0, moved);
    onChange(next);
    dragIdx.current = null;
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={busy || value.length >= max}
          className="px-5 py-2.5 text-[11px] uppercase tracking-luxe border border-gold/40 text-gold hover:bg-gold hover:text-black rounded-md disabled:opacity-50"
        >
          {busy ? "Uploading…" : "Add images"}
        </button>
        <span className="text-xs text-mist">
          {value.length}/{max}
        </span>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {error && <p className="text-xs text-err mb-2">{error}</p>}

      {value.length === 0 ? (
        <p className="text-sm text-mist border border-gold/14 rounded-md p-6 text-center">
          No images yet. Add your best work — listings, drone shots, before-and-afters.
        </p>
      ) : (
        <ul className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {value.map((img, i) => (
            <li
              key={`${img.url}-${i}`}
              draggable={reorderable}
              onDragStart={() => onDragStart(i)}
              onDragOver={onDragOver}
              onDrop={() => onDrop(i)}
              className={cn(
                "bg-warm/40 border border-gold/14 p-3 rounded-md",
                reorderable && "cursor-move",
              )}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={img.url}
                alt={img.alt}
                className="w-full aspect-square object-cover rounded-sm mb-2"
              />
              <input
                type="text"
                placeholder="Alt text"
                value={img.alt}
                onChange={(e) => setAt(i, { alt: e.target.value })}
                className="w-full bg-warm border border-gold/22 text-ivory text-xs px-2 py-1 mb-2 rounded-sm focus:outline-none focus:border-gold"
              />
              <input
                type="text"
                placeholder="Caption"
                value={img.caption}
                onChange={(e) => setAt(i, { caption: e.target.value })}
                className="w-full bg-warm border border-gold/22 text-ivory text-xs px-2 py-1 rounded-sm focus:outline-none focus:border-gold"
              />
              <button
                type="button"
                onClick={() => remove(i)}
                className="mt-2 text-[10px] uppercase tracking-luxe text-mist hover:text-rose-400"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
