"use client";

import { useCallback, useRef, useState } from "react";

interface Props {
  onPick: (file: File) => void;
  disabled?: boolean;
}

const MAX_BYTES = 10 * 1024 * 1024;
const ACCEPTED = ["image/jpeg", "image/png", "image/jpg"];

/**
 * Drag-and-drop file picker with a hidden <input type="file"> fallback.
 * No third-party deps. Validates size + content-type before invoking
 * `onPick` so the caller can move straight to upload.
 */
export default function DropZone({ onPick, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [over, setOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback((file: File): string | null => {
    if (!ACCEPTED.includes(file.type) && !/\.(jpg|jpeg|png)$/i.test(file.name)) {
      return "Only JPG and PNG files are accepted.";
    }
    if (file.size > MAX_BYTES) {
      return "Image must be 10 MB or smaller.";
    }
    return null;
  }, []);

  const handle = useCallback(
    (file: File | null | undefined) => {
      if (!file) return;
      const err = validate(file);
      if (err) {
        setError(err);
        return;
      }
      setError(null);
      onPick(file);
    },
    [onPick, validate],
  );

  return (
    <div className="space-y-3">
      <div
        className={[
          "relative border-2 border-dashed p-10 sm:p-14 text-center transition-colors duration-200",
          over
            ? "border-gold bg-gold/5"
            : "border-gold/30 bg-deep hover:border-gold/60",
          disabled ? "opacity-60 pointer-events-none" : "cursor-pointer",
        ].join(" ")}
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          handle(e.dataTransfer.files?.[0]);
        }}
        role="button"
        tabIndex={0}
        aria-label="Upload room photo"
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
      >
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center border border-gold/40 text-gold">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden
          >
            <path
              d="M12 16V4m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div className="ey mb-2 text-gold">Upload</div>
        <div className="font-serif text-ivory text-xl sm:text-2xl mb-1">
          Drop a room photo here
        </div>
        <p className="text-mist text-sm">
          or click to choose. JPG or PNG, up to 10 MB.
        </p>

        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={(e) => handle(e.target.files?.[0])}
          aria-label="Choose room photo file"
        />
      </div>
      {error && (
        <div className="text-err text-sm" role="alert">
          {error}
        </div>
      )}
    </div>
  );
}
