"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  useEffect,
} from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

type Tone = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  tone: Tone;
}

interface ToastContextValue {
  push: (message: string, tone?: Tone) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}

const tones: Record<Tone, string> = {
  success: "border-ok/40 bg-deep text-ok",
  error: "border-err/40 bg-deep text-err",
  info: "border-gold/40 bg-deep text-gold",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const reduced = useReducedMotion();

  const push = useCallback((message: string, tone: Tone = "info") => {
    const id = Date.now() + Math.random();
    setItems((prev) => [...prev, { id, message, tone }]);
  }, []);

  useEffect(() => {
    if (items.length === 0) return;
    const timers = items.map((t) =>
      setTimeout(
        () => setItems((prev) => prev.filter((i) => i.id !== t.id)),
        4000,
      ),
    );
    return () => {
      for (const t of timers) clearTimeout(t);
    };
  }, [items]);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div
        className="fixed bottom-4 left-4 right-4 sm:bottom-auto sm:top-4 sm:left-auto sm:right-4 z-[200] flex flex-col gap-2 pointer-events-none safe-bottom-tight sm:!pb-0"
        aria-live="polite"
        aria-atomic="true"
      >
        <AnimatePresence>
          {items.map((t) => (
            <motion.div
              key={t.id}
              initial={reduced ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
              className={cn(
                "pointer-events-auto px-5 py-3 border text-sm w-full sm:max-w-sm shadow-card",
                tones[t.tone],
              )}
              role="status"
            >
              {t.message}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
