"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/api/fetch";

import BeforeAfterSlider from "./BeforeAfterSlider";
import DropZone from "./DropZone";
import ProgressBar from "./ProgressBar";
import ResultActions from "./ResultActions";

type AppState =
  | { kind: "idle" }
  | { kind: "uploading"; pct: number }
  | { kind: "processing"; taskId: number; progress: number; startedAt: number }
  | { kind: "done"; beforeUrl: string; afterUrl: string; runtimeMs: number; cost: number }
  | { kind: "error"; code: string; message: string };

interface RunResponse {
  task_id: number;
  status: string;
  original_url: string | null;
  result_url: string | null;
}

interface StreamFrame {
  task_id: number;
  status: string;
  progress: number;
  result_url: string | null;
  input_url: string | null;
  error: string | null;
  block_reason: string | null;
  cost_usd: number;
  runtime_ms: number;
  final?: boolean;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function errorMessageFor(code: string, raw?: string): string {
  if (code === "spend_cap_exceeded")
    return "We're at our daily AI budget. Please try again tomorrow.";
  if (code === "rate_limited" || code === "rate_limit")
    return "You're going fast. Wait a minute and try again.";
  if (code.startsWith("input_moderation"))
    return "We couldn't process this image. Please try a different photo.";
  if (code === "bad_image")
    return "We need a JPG or PNG under 10 MB.";
  if (code === "auth")
    return "Your session expired. Sign in again to continue.";
  return raw || "Something went wrong on our side. No charges. Please retry.";
}

export default function FurnitureRemoverApp() {
  const [state, setState] = useState<AppState>({ kind: "idle" });
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  const cleanupStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => cleanupStream(), [cleanupStream]);

  const onResult = useCallback(
    (frame: StreamFrame) => {
      cleanupStream();
      if (frame.status === "success" && frame.result_url) {
        setState({
          kind: "done",
          beforeUrl: frame.input_url || "",
          afterUrl: frame.result_url,
          runtimeMs: frame.runtime_ms,
          cost: frame.cost_usd,
        });
      } else if (frame.status === "blocked") {
        setState({
          kind: "error",
          code: frame.block_reason || "blocked",
          message: errorMessageFor(frame.block_reason || "", frame.error || undefined),
        });
      } else {
        setState({
          kind: "error",
          code: frame.error || "unknown",
          message: errorMessageFor("unknown", frame.error || undefined),
        });
      }
    },
    [cleanupStream],
  );

  const startStream = useCallback(
    (taskId: number) => {
      // Prefer SSE; fall back to polling if EventSource isn't available or
      // the connection errors out before the first message.
      if (typeof window !== "undefined" && "EventSource" in window) {
        try {
          const es = new EventSource(
            `${API_BASE}/api/v1/tools/streams/${taskId}/`,
            { withCredentials: true },
          );
          eventSourceRef.current = es;
          es.onmessage = (evt) => {
            try {
              const frame = JSON.parse(evt.data) as StreamFrame;
              setState((prev) =>
                prev.kind === "processing"
                  ? { ...prev, progress: frame.progress }
                  : prev,
              );
              if (frame.final) onResult(frame);
            } catch {
              // ignore parse errors; SSE keeps streaming
            }
          };
          es.onerror = () => {
            // First-error fallback to polling.
            es.close();
            eventSourceRef.current = null;
            pollLoop(taskId);
          };
          return;
        } catch {
          // fallthrough to polling
        }
      }
      pollLoop(taskId);
    },
    [onResult],
  );

  const pollLoop = useCallback(
    async (taskId: number) => {
      try {
        const data = await apiFetch<{
          status: string;
          progress: number;
          result?: { url?: string; input_url?: string; cost_usd?: number; runtime_ms?: number } | null;
          error?: string;
        }>(`/api/v1/tools/tasks/${taskId}/`, {}, { auth: true });
        setState((prev) =>
          prev.kind === "processing"
            ? { ...prev, progress: data.progress }
            : prev,
        );
        if (data.status === "success" && data.result?.url) {
          onResult({
            task_id: taskId,
            status: "success",
            progress: 100,
            result_url: data.result.url,
            input_url: data.result.input_url || null,
            error: null,
            block_reason: null,
            cost_usd: data.result.cost_usd || 0,
            runtime_ms: data.result.runtime_ms || 0,
            final: true,
          });
          return;
        }
        if (data.status === "failed" || data.status === "blocked") {
          onResult({
            task_id: taskId,
            status: data.status,
            progress: 100,
            result_url: null,
            input_url: null,
            error: data.error || null,
            block_reason: null,
            cost_usd: 0,
            runtime_ms: 0,
            final: true,
          });
          return;
        }
      } catch {
        // ignore transient errors and keep polling
      }
      pollTimerRef.current = window.setTimeout(() => pollLoop(taskId), 2500);
    },
    [onResult],
  );

  const upload = useCallback(
    async (file: File) => {
      cleanupStream();
      setState({ kind: "uploading", pct: 8 });
      const fd = new FormData();
      fd.append("image", file);
      fd.append("preserve_layout", "true");

      try {
        const res = await apiFetch<RunResponse>(
          "/api/v1/tools/furniture-remover/",
          { method: "POST", body: fd },
          { auth: true },
        );
        setState({
          kind: "processing",
          taskId: res.task_id,
          progress: 12,
          startedAt: Date.now(),
        });
        startStream(res.task_id);
      } catch (err: unknown) {
        const status = (err as { status?: number })?.status;
        const code =
          (err as { problem?: { detail?: string } })?.problem?.detail ||
          (status === 401
            ? "auth"
            : status === 429
              ? "rate_limit"
              : "server");
        setState({
          kind: "error",
          code,
          message: errorMessageFor(code),
        });
      }
    },
    [cleanupStream, startStream],
  );

  const reset = useCallback(() => {
    cleanupStream();
    setState({ kind: "idle" });
  }, [cleanupStream]);

  return (
    <section className="border border-gold/22 bg-deep p-6 sm:p-8 lg:p-10">
      <AnimatePresence mode="wait">
        {state.kind === "idle" && (
          <motion.div
            key="idle"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <DropZone onPick={(file) => void upload(file)} />
          </motion.div>
        )}

        {state.kind === "uploading" && (
          <motion.div
            key="uploading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4 py-12"
          >
            <ProgressBar value={state.pct} label="Uploading" />
            <p className="text-mist text-sm">Sending photo to the AI worker.</p>
          </motion.div>
        )}

        {state.kind === "processing" && (
          <ProcessingPanel
            startedAt={state.startedAt}
            progress={state.progress}
          />
        )}

        {state.kind === "done" && (
          <motion.div
            key="done"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-6"
          >
            {state.beforeUrl && state.afterUrl ? (
              <BeforeAfterSlider
                beforeUrl={state.beforeUrl}
                afterUrl={state.afterUrl}
              />
            ) : (
              <div className="border border-gold/22 bg-black p-8 text-mist">
                Result is ready, but we couldn&apos;t load the comparison view.
              </div>
            )}
            <div className="text-mist text-sm">
              Runtime {Math.round(state.runtimeMs / 1000)}s · Est. cost $
              {state.cost.toFixed(3)}
            </div>
            <ResultActions resultUrl={state.afterUrl} onReset={reset} />
          </motion.div>
        )}

        {state.kind === "error" && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="space-y-5 py-8"
            role="alert"
          >
            <div className="ey text-err">Run failed</div>
            <p className="text-ivory text-lg">{state.message}</p>
            <button
              type="button"
              onClick={reset}
              className="ey px-5 py-3 border border-gold/40 text-gold hover:border-gold hover:text-gold-hi"
            >
              Try again
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

function ProcessingPanel({
  progress,
  startedAt,
}: {
  progress: number;
  startedAt: number;
}) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const t = window.setInterval(
      () => setElapsed(Math.floor((Date.now() - startedAt) / 1000)),
      500,
    );
    return () => window.clearInterval(t);
  }, [startedAt]);

  const expected = 35;
  const remaining = Math.max(0, expected - elapsed);

  return (
    <motion.div
      key="processing"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-5 py-12"
    >
      <motion.div
        animate={{ opacity: [0.6, 1, 0.6] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="font-serif text-ivory text-xl sm:text-2xl"
      >
        Emptying the room.
      </motion.div>
      <p className="text-mist text-sm">
        Typically 25-40 seconds. {elapsed}s elapsed · ~{remaining}s remaining.
      </p>
      <ProgressBar
        value={progress}
        label="Processing"
        indeterminate={progress < 60}
      />
    </motion.div>
  );
}
