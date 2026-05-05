"use client";

import { useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

// Native IntersectionObserver + CSS instead of Framer Motion's useAnimation/
// useInView combo. Framer's animate-on-controls path is unreliable under
// Next 16 + React 19.2 + RSC client boundary (animations sometimes never fire,
// leaving content stuck at opacity:0). CSS keyframes are deterministic.

type Direction = "up" | "down" | "left" | "right" | "fade";

interface ScrollRevealProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  direction?: Direction;
  distance?: number;
  duration?: number;
  threshold?: number;
  once?: boolean;
}

export default function ScrollReveal({
  children,
  className,
  delay = 0,
  direction = "up",
  distance = 30,
  duration = 0.5,
  threshold = 0.15,
  once = true,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Honor prefers-reduced-motion: skip animation, render at final state.
    if (typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setVisible(true);
      return;
    }
    const node = ref.current;
    if (!node) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            if (once) io.disconnect();
          } else if (!once) {
            setVisible(false);
          }
        }
      },
      { threshold },
    );
    io.observe(node);
    return () => io.disconnect();
  }, [threshold, once]);

  const yOff = direction === "up" ? distance : direction === "down" ? -distance : 0;
  const xOff = direction === "left" ? distance : direction === "right" ? -distance : 0;

  const style: React.CSSProperties = visible
    ? {
        opacity: 1,
        transform: "translate3d(0,0,0)",
        transition: `opacity ${duration}s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s, transform ${duration}s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s`,
      }
    : {
        opacity: 0,
        transform: `translate3d(${xOff}px, ${yOff}px, 0)`,
      };

  return (
    <div ref={ref} className={cn(className)} style={style}>
      {children}
    </div>
  );
}
