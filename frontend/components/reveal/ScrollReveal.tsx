"use client";

import { useRef, useEffect } from "react";
import {
  motion,
  useInView,
  useAnimation,
  useReducedMotion,
} from "framer-motion";
import { cn } from "@/lib/utils";

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
  const isInView = useInView(ref, { once, amount: threshold });
  const controls = useAnimation();
  const reduced = useReducedMotion();

  useEffect(() => {
    if (reduced) {
      controls.set({ opacity: 1, x: 0, y: 0 });
      return;
    }
    if (isInView) controls.start("visible");
  }, [isInView, controls, reduced]);

  const y =
    direction === "up" ? distance : direction === "down" ? -distance : 0;
  const x =
    direction === "left" ? distance : direction === "right" ? -distance : 0;

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={controls}
      variants={{
        hidden: {
          opacity: reduced ? 1 : 0,
          y: reduced ? 0 : y,
          x: reduced ? 0 : x,
        },
        visible: {
          opacity: 1,
          y: 0,
          x: 0,
          transition: {
            duration: reduced ? 0 : duration,
            delay: reduced ? 0 : delay,
            ease: [0.16, 1, 0.3, 1],
          },
        },
      }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
