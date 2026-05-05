"use client";

import Link from "next/link";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { AutosaveState } from "./useAutosave";
import { STEPS, type StepKey } from "./steps";

// Re-export so existing import sites (`@/components/vendor/wizard/WizardChrome`)
// still resolve. New code should import from "./steps" directly.
export { STEPS };
export type { StepKey };

interface Props {
  currentStep: StepKey;
  completedSteps: string[];
  saveState?: AutosaveState;
}

export default function WizardChrome({
  currentStep,
  completedSteps,
  saveState = "idle",
}: Props) {
  const [open, setOpen] = useState(false);
  const currentIdx = STEPS.findIndex((s) => s.key === currentStep);
  const totalSteps = STEPS.length;

  return (
    <header className="border-b border-gold/14 mb-10 pb-6">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-[11px] uppercase tracking-luxe text-mist hover:text-gold"
          >
            ← Save & exit
          </Link>
        </div>
        <SavedPip state={saveState} />
      </div>

      {/* Mobile collapsible label */}
      <div className="sm:hidden">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="w-full flex justify-between items-center text-left"
        >
          <span className="text-[11px] uppercase tracking-luxe text-mist">
            Step {currentIdx + 1} of {totalSteps}
          </span>
          <span className="text-gold font-serif text-xl">
            {STEPS[currentIdx]?.label}
          </span>
        </button>
        {open && (
          <ul className="mt-3 space-y-2 text-xs">
            {STEPS.map((s, i) => (
              <li key={s.key}>
                <span
                  className={cn(
                    "uppercase tracking-luxe",
                    i === currentIdx
                      ? "text-gold"
                      : completedSteps.includes(s.key)
                        ? "text-mist"
                        : "text-dim",
                  )}
                >
                  {i + 1}. {s.label}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Desktop progress bar */}
      <ol className="hidden sm:flex items-center gap-2">
        {STEPS.map((s, i) => {
          const active = s.key === currentStep;
          const done = completedSteps.includes(s.key) && !active;
          return (
            <li key={s.key} className="flex-1">
              <div
                className={cn(
                  "h-1 rounded-full transition-colors",
                  active
                    ? "bg-gold"
                    : done
                      ? "bg-gold/40"
                      : "bg-warm",
                )}
              />
              <div
                className={cn(
                  "mt-2 text-[10px] uppercase tracking-luxe",
                  active
                    ? "text-gold"
                    : done
                      ? "text-mist"
                      : "text-dim",
                )}
              >
                {i + 1}. {s.label}
              </div>
            </li>
          );
        })}
      </ol>
    </header>
  );
}

function SavedPip({ state }: { state: AutosaveState }) {
  if (state === "idle") return null;
  const dot = {
    saving: "bg-gold/60 animate-pulse",
    saved:  "bg-emerald-500",
    error:  "bg-rose-500",
  }[state];
  const label = {
    saving: "Saving",
    saved:  "Saved",
    error:  "Save failed",
  }[state];
  return (
    <span
      role="status"
      className="flex items-center gap-2 text-[11px] uppercase tracking-luxe text-mist"
    >
      <span className={cn("w-2 h-2 rounded-full", dot)} />
      {label}
    </span>
  );
}
