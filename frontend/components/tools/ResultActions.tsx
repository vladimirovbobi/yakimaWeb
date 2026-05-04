"use client";

import { useState } from "react";

interface Props {
  resultUrl: string;
  onReset: () => void;
}

export default function ResultActions({ resultUrl, onReset }: Props) {
  const [copied, setCopied] = useState(false);

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(resultUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // ignore — older browsers without clipboard permission
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <a
        href={resultUrl}
        download="empty-room.png"
        className="ey px-5 py-3 bg-gold text-black hover:bg-gold-hi transition-colors duration-200"
      >
        Download empty-room
      </a>
      <button
        type="button"
        onClick={onReset}
        className="ey px-5 py-3 border border-gold/40 text-gold hover:border-gold hover:text-gold-hi transition-colors duration-200"
      >
        Try another photo
      </button>
      <button
        type="button"
        onClick={onCopy}
        className="ey px-5 py-3 border border-mist/30 text-mist hover:border-mist/60 hover:text-ivory transition-colors duration-200"
      >
        {copied ? "Link copied" : "Copy share link"}
      </button>
    </div>
  );
}
