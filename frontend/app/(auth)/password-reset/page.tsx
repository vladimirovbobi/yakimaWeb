"use client";

import { useState } from "react";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";

export default function PasswordResetPage() {
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pending) return;
    setPending(true);
    setError(null);
    try {
      await apiFetch("/api/v1/auth/password-reset/", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setDone(true);
    } catch (err) {
      const e = err as ApiError;
      setError(
        e.problem.detail || e.problem.title || "Could not send reset email",
      );
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <div className="text-center">
        <div className="ey mb-5">Reset email sent</div>
        <h1 className="font-serif font-light text-ivory text-2xl sm:text-3xl leading-tight">
          Check your inbox.
        </h1>
        <p className="text-mist mt-4 leading-relaxed">
          If <span className="text-ivory">{email}</span> belongs to an account,
          you'll get a reset link in a minute.
        </p>
        <Link
          href="/login"
          data-touch
          className="inline-flex items-center justify-center gap-2 uppercase tracking-cap text-xs px-8 py-4 bg-gold text-black font-medium hover:bg-gold-hi transition-colors mt-8 w-full sm:w-auto"
        >
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 sm:mb-10">
        <h1 className="font-serif font-light text-ivory text-2xl sm:text-3xl leading-tight">
          Reset password
        </h1>
        <p className="text-mist text-sm mt-2">
          Enter your email. We'll send you a link.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-5">
        {error && (
          <div className="border border-err/30 bg-err/10 text-err text-sm px-4 py-3 rounded-md">
            {error}
          </div>
        )}
        <div>
          <label
            htmlFor="email"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md min-h-11 focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
        </div>
        <Button
          type="submit"
          variant="solid"
          loading={pending}
          className="w-full"
        >
          Send reset link
        </Button>
      </form>

      <p className="text-mist text-sm text-center mt-8">
        Remembered it?{" "}
        <Link
          href="/login"
          className="text-gold hover:text-gold-hi underline underline-offset-4"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
