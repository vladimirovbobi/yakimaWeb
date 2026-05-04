"use client";

import { motion } from "framer-motion";
import { useCallback, useRef, useState } from "react";

import { apiFetch } from "@/lib/api/fetch";

interface RunResponse {
  task_id: number;
  status: string;
}

interface TaskStatus {
  task_id: number;
  status: "queued" | "running" | "success" | "failed" | "blocked";
  progress: number;
  result?: {
    url?: string;
    compression?: {
      filename: string;
      format: string;
      input_size: number;
      output_size: number;
      bytes_saved: number;
      percent_saved: number;
      width: number;
      height: number;
      method: string;
    };
  } | null;
  error?: string;
}

interface FileEntry {
  id: string;
  file: File;
  status: "queued" | "uploading" | "processing" | "done" | "error";
  taskId?: number;
  progress: number;
  result?: TaskStatus["result"];
  errorMessage?: string;
}

const ALLOWED_EXT = ["jpg", "jpeg", "png", "webp", "gif", "heic", "heif", "tiff", "tif", "bmp"];
const MAX_BYTES = 50 * 1024 * 1024;

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

function uid(): string {
  return Math.random().toString(36).slice(2, 11);
}

function extOf(name: string): string {
  return (name.split(".").pop() || "").toLowerCase();
}

export default function ImageCompressorApp() {
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const dragCounterRef = useRef(0);
  const [isDragging, setIsDragging] = useState(false);

  const totalIn = entries.reduce((s, e) => s + (e.file?.size || 0), 0);
  const totalOut = entries.reduce(
    (s, e) => s + (e.result?.compression?.output_size || 0),
    0,
  );
  const totalSaved = Math.max(0, totalIn - totalOut);
  const savedPct =
    totalIn > 0 && totalOut > 0 ? Math.round((totalSaved / totalIn) * 1000) / 10 : 0;

  const validate = useCallback((file: File): string | null => {
    if (file.size > MAX_BYTES) return `Too large (${formatBytes(file.size)}; limit 50 MB)`;
    if (!ALLOWED_EXT.includes(extOf(file.name)))
      return `Format .${extOf(file.name)} not supported`;
    return null;
  }, []);

  const pollTask = useCallback(async (taskId: number, fileId: string) => {
    const deadline = Date.now() + 90_000;
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 1000));
      try {
        const status = await apiFetch<TaskStatus>(
          `/api/v1/tools/tasks/${taskId}/`,
          {},
          { auth: true },
        );
        if (status.status === "success") {
          setEntries((prev) =>
            prev.map((e) =>
              e.id === fileId
                ? { ...e, status: "done", progress: 100, result: status.result }
                : e,
            ),
          );
          return;
        }
        if (status.status === "failed" || status.status === "blocked") {
          setEntries((prev) =>
            prev.map((e) =>
              e.id === fileId
                ? {
                    ...e,
                    status: "error",
                    progress: 100,
                    errorMessage: status.error || `Task ${status.status}`,
                  }
                : e,
            ),
          );
          return;
        }
        setEntries((prev) =>
          prev.map((e) =>
            e.id === fileId ? { ...e, progress: status.progress || 50 } : e,
          ),
        );
      } catch {
        // transient — keep polling
      }
    }
    setEntries((prev) =>
      prev.map((e) =>
        e.id === fileId
          ? { ...e, status: "error", errorMessage: "Timed out — try again." }
          : e,
      ),
    );
  }, []);

  const submitOne = useCallback(
    async (entry: FileEntry) => {
      setEntries((prev) =>
        prev.map((e) =>
          e.id === entry.id ? { ...e, status: "uploading", progress: 10 } : e,
        ),
      );
      const form = new FormData();
      form.append("image", entry.file);
      try {
        const resp = await apiFetch<RunResponse>(
          "/api/v1/tools/image-compressor/",
          { method: "POST", body: form },
          { auth: true },
        );
        setEntries((prev) =>
          prev.map((e) =>
            e.id === entry.id
              ? {
                  ...e,
                  status: "processing",
                  taskId: resp.task_id,
                  progress: 30,
                }
              : e,
          ),
        );
        await pollTask(resp.task_id, entry.id);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Submission failed";
        setEntries((prev) =>
          prev.map((e) =>
            e.id === entry.id
              ? { ...e, status: "error", errorMessage: msg }
              : e,
          ),
        );
      }
    },
    [pollTask],
  );

  const handleFiles = useCallback(
    (files: FileList | File[]) => {
      const arr = Array.from(files);
      const newEntries: FileEntry[] = arr.map((f) => {
        const err = validate(f);
        return {
          id: uid(),
          file: f,
          status: err ? "error" : "queued",
          progress: 0,
          errorMessage: err || undefined,
        };
      });
      setEntries((prev) => [...prev, ...newEntries]);
      const valid = newEntries.filter((e) => e.status === "queued");
      if (valid.length === 0) return;
      setBusy(true);
      (async () => {
        // Sequential: keeps the rate limiter happy and the UI readable.
        for (const e of valid) {
          await submitOne(e);
        }
        setBusy(false);
      })();
    },
    [submitOne, validate],
  );

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };
  const onDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current += 1;
    setIsDragging(true);
  };
  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current -= 1;
    if (dragCounterRef.current <= 0) {
      dragCounterRef.current = 0;
      setIsDragging(false);
    }
  };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current = 0;
    setIsDragging(false);
    const dt = e.dataTransfer;
    if (dt?.files?.length) handleFiles(dt.files);
  };

  return (
    <section className="space-y-6">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={[
          "w-full text-left",
          "border border-dashed transition-colors duration-200",
          "p-8 md:p-12 cursor-pointer",
          isDragging
            ? "bg-warm/40 border-gold"
            : "bg-panel border-gold/35 hover:border-gold/60",
        ].join(" ")}
        aria-label="Drop images here or click to choose"
      >
        <div className="flex flex-col items-center text-center gap-3">
          <div className="ey">Drop images</div>
          <div className="font-serif text-2xl md:text-3xl text-ivory leading-tight font-light">
            Drag JPG, PNG, WebP, HEIC, TIFF, GIF or BMP files here.
          </div>
          <p className="text-mist text-sm max-w-xl">
            Up to 50 MB each. We re-encode losslessly — no pixels lost, just
            wasted bytes. Compression runs locally on the worker; nothing leaves
            our servers.
          </p>
          <div className="mt-3 inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-6 py-3 bg-gold text-black font-medium hover:bg-gold-hi transition-colors">
            Choose files
          </div>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.webp,.gif,.heic,.heif,.tiff,.tif,.bmp,image/*"
          className="sr-only"
          onChange={(e) => {
            if (e.target.files?.length) handleFiles(e.target.files);
            if (inputRef.current) inputRef.current.value = "";
          }}
        />
      </button>

      {entries.length > 0 && (
        <div className="border border-gold/22 bg-deep">
          <div className="px-5 py-4 border-b border-gold/14 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <div>
              <span className="label-luxe">In</span>{" "}
              <span className="text-ivory">{formatBytes(totalIn)}</span>
            </div>
            <div>
              <span className="label-luxe">Out</span>{" "}
              <span className="text-ivory">
                {totalOut > 0 ? formatBytes(totalOut) : "—"}
              </span>
            </div>
            <div>
              <span className="label-luxe">Saved</span>{" "}
              <span className="text-gold-hi">
                {totalSaved > 0
                  ? `${formatBytes(totalSaved)} (${savedPct}%)`
                  : "—"}
              </span>
            </div>
            <div className="ml-auto label-luxe">
              {entries.length} file{entries.length === 1 ? "" : "s"}
              {busy ? " · processing…" : ""}
            </div>
          </div>
          <ul className="divide-y divide-gold/14">
            {entries.map((e) => {
              const c = e.result?.compression;
              return (
                <li
                  key={e.id}
                  className="px-5 py-4 grid gap-3 md:grid-cols-[1fr_auto] items-center"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-3">
                      <span className="font-serif text-base text-ivory truncate">
                        {e.file.name}
                      </span>
                      <span className="label-luxe text-dim">
                        {formatBytes(e.file.size)}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-xs">
                      <span
                        className={[
                          "uppercase tracking-luxe text-[10px] px-2 py-1 border",
                          e.status === "done"
                            ? "border-ok/40 text-ok"
                            : e.status === "error"
                            ? "border-err/40 text-err"
                            : "border-gold/35 text-gold",
                        ].join(" ")}
                      >
                        {e.status}
                      </span>
                      {c && (
                        <span className="text-mist">
                          {formatBytes(c.input_size)} →{" "}
                          <span className="text-ivory">
                            {formatBytes(c.output_size)}
                          </span>{" "}
                          <span className="text-gold-hi">
                            ({c.percent_saved}% saved)
                          </span>
                        </span>
                      )}
                      {e.errorMessage && (
                        <span className="text-err">{e.errorMessage}</span>
                      )}
                    </div>
                    <div className="mt-2 h-1 bg-warm rounded">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{
                          width: `${
                            e.status === "done"
                              ? 100
                              : e.status === "error"
                              ? 100
                              : e.progress
                          }%`,
                        }}
                        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                        className={
                          e.status === "error"
                            ? "h-full bg-err/60"
                            : e.status === "done"
                            ? "h-full bg-ok/70"
                            : "h-full bg-gold/70"
                        }
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    {e.status === "done" && e.result?.url && (
                      <a
                        href={e.result.url}
                        download={c?.filename || e.file.name}
                        className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-5 py-2 border border-gold/52 text-gold hover:bg-gold hover:text-black transition-colors"
                      >
                        Download
                      </a>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </section>
  );
}
