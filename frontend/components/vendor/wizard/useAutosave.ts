"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type AutosaveState = "idle" | "saving" | "saved" | "error";

export interface UseAutosaveOptions<T> {
  /** Debounce delay in ms (default 800ms). */
  delay?: number;
  /** Save callback — should reject on failure. */
  onSave: (value: T) => Promise<void>;
}

export function useAutosave<T>({ delay = 800, onSave }: UseAutosaveOptions<T>) {
  const [state, setState] = useState<AutosaveState>("idle");
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dirty = useRef(false);

  const flush = useCallback(
    async (value: T) => {
      setState("saving");
      try {
        await onSave(value);
        setState("saved");
        setError(null);
        dirty.current = false;
      } catch (err) {
        setState("error");
        setError(err instanceof Error ? err.message : "Save failed");
      }
    },
    [onSave],
  );

  const schedule = useCallback(
    (value: T) => {
      dirty.current = true;
      setState("saving");
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => flush(value), delay);
    },
    [delay, flush],
  );

  // Warn on unload while still dirty.
  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!dirty.current) return;
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, []);

  // Cleanup timer on unmount.
  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  return { state, error, schedule, flush };
}
