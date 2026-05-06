"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface Props {
  beforeUrl: string;
  afterUrl: string;
  beforeAlt?: string;
  afterAlt?: string;
}

/**
 * Two stacked images with a draggable vertical handle that reveals the
 * `afterUrl` from the right side. No third-party dependencies — pointer
 * events for desktop and touch, arrow keys when the handle is focused.
 */
export default function BeforeAfterSlider({
  beforeUrl,
  afterUrl,
  beforeAlt = "Before",
  afterAlt = "After",
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [position, setPosition] = useState(50);
  const [dragging, setDragging] = useState(false);

  const setFromClientX = useCallback((clientX: number) => {
    const node = containerRef.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    const pct = ((clientX - rect.left) / rect.width) * 100;
    setPosition(Math.min(100, Math.max(0, pct)));
  }, []);

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e: PointerEvent) => setFromClientX(e.clientX);
    const onUp = () => setDragging(false);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };
  }, [dragging, setFromClientX]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      setPosition((p) => Math.max(0, p - 4));
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      setPosition((p) => Math.min(100, p + 4));
    } else if (e.key === "Home") {
      setPosition(0);
    } else if (e.key === "End") {
      setPosition(100);
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full select-none overflow-hidden border border-gold/22 bg-black"
      role="img"
      aria-label="Before and after comparison slider, drag to reveal"
      style={{ aspectRatio: "16/10" }}
      onPointerDown={(e) => {
        setDragging(true);
        setFromClientX(e.clientX);
      }}
    >
      {/* Before (full width, behind) */}
      <img
        src={beforeUrl}
        alt={beforeAlt}
        className="absolute inset-0 h-full w-full object-cover"
        draggable={false}
      />
      {/* After (clipped from the left) */}
      <div
        className="absolute inset-0"
        style={{ clipPath: `inset(0 0 0 ${position}%)` }}
      >
        <img
          src={afterUrl}
          alt={afterAlt}
          className="absolute inset-0 h-full w-full object-cover"
          draggable={false}
        />
      </div>

      {/* Labels */}
      <span className="absolute left-3 top-3 ey text-dark-text bg-dark-bg/60 px-2 py-1 text-[10px]">
        Before
      </span>
      <span className="absolute right-3 top-3 ey text-dark-text bg-dark-bg/60 px-2 py-1 text-[10px]">
        After
      </span>

      {/* Handle */}
      <div
        className="pointer-events-none absolute top-0 bottom-0 w-px bg-gold/80"
        style={{ left: `${position}%` }}
      />
      <button
        type="button"
        aria-label="Adjust before/after split"
        className="absolute top-1/2 grid h-11 w-11 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-gold/60 bg-dark-bg/85 text-gold-hi cursor-ew-resize hover:bg-dark-bg focus:outline-none focus:ring-2 focus:ring-gold/70 touch-none"
        style={{ left: `${position}%` }}
        onKeyDown={onKeyDown}
        onPointerDown={(e) => {
          e.stopPropagation();
        }}
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 14 14"
          fill="none"
          aria-hidden
        >
          <path
            d="M5 4L1 7l4 3M9 4l4 3-4 3"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
    </div>
  );
}
