"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

export default function TotpVerifyForm() {
  const [code, setCode] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const toast = useToast();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await apiFetch(
        "/api/v1/auth/2fa/totp/verify/",
        {
          method: "POST",
          body: JSON.stringify({ totp_code: code }),
        },
        { auth: true },
      );
      toast.push("Two-factor enabled", "success");
      router.push("/dashboard");
    } catch (err) {
      const e = err as ApiError;
      setError(e.problem.detail || "Code didn't work. Try the latest one.");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label
          htmlFor="totp"
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          6-digit code
        </label>
        <input
          id="totp"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          required
          autoFocus
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          placeholder="000000"
          className="w-full bg-warm border border-gold/22 text-ivory px-4 py-4 text-lg rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold tracking-[0.5em] text-center font-mono"
        />
        {error && <p className="text-err text-xs mt-2">{error}</p>}
      </div>
      <Button
        type="submit"
        variant="solid"
        loading={pending}
        className="w-full"
      >
        Confirm and turn on 2FA
      </Button>
    </form>
  );
}
