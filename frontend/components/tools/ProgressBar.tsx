"use client";

import { motion } from "framer-motion";

interface Props {
  /** 0..100 */
  value: number;
  label?: string;
  indeterminate?: boolean;
}

export default function ProgressBar({ value, label, indeterminate }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-2" role="progressbar"
         aria-valuenow={indeterminate ? undefined : Math.round(clamped)}
         aria-valuemin={0} aria-valuemax={100} aria-label={label || "Progress"}>
      {label && (
        <div className="ey text-gold flex items-center justify-between">
          <span>{label}</span>
          {!indeterminate && <span className="text-mist">{Math.round(clamped)}%</span>}
        </div>
      )}
      <div className="relative h-1 w-full overflow-hidden bg-gold/15">
        {indeterminate ? (
          <motion.div
            className="absolute inset-y-0 w-1/3 bg-gold"
            initial={{ x: "-100%" }}
            animate={{ x: "300%" }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        ) : (
          <motion.div
            className="absolute inset-y-0 left-0 bg-gold"
            initial={{ width: 0 }}
            animate={{ width: `${clamped}%` }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          />
        )}
      </div>
    </div>
  );
}
