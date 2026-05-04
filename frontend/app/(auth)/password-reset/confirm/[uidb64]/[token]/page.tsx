"use client";

import { useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";

interface ConfirmPageProps {
  params: Promise<{ uidb64: string; token: string }>;
}

export default function PasswordResetConfirmPage({ params }: ConfirmPageProps) {
  const { uidb64, token } = use(params);
  const router = useRouter();
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pending) return;
    if (pw !== pw2) {
      setErrors({ password_confirm: "Passwords don't match." });
      return;
    }
    setPending(true);
    setErrors({});
    try {
      await apiFetch(
        `/api/v1/auth/password-reset-confirm/${uidb64}/${token}/`,
        {
          method: "POST",
          body: JSON.stringify({ password: pw, password_confirm: pw2 }),
        },
      );
      setDone(true);
      setTimeout(() => router.push("/login"), 1500);
    } catch (err) {
      const e = err as ApiError;
      const flat: Record<string, string> = {};
      if (e.problem.errors) {
        for (const [k, v] of Object.entries(e.problem.errors)) {
          flat[k] = Array.isArray(v) ? v[0] : String(v);
        }
      }
      if (Object.keys(flat).length === 0) {
        flat._global =
          e.problem.detail ||
          "This reset link may have expired. Request a new one.";
      }
      setErrors(flat);
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <div className="text-center">
        <div className="ey mb-5">Done</div>
        <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
          Password updated.
        </h1>
        <p className="text-mist mt-4 leading-relaxed">
          Redirecting to sign in...
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-10">
        <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
          Set new password
        </h1>
        <p className="text-mist text-sm mt-2">
          Pick something you'll remember.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-5">
        {errors._global && (
          <div className="border border-err/30 bg-err/10 text-err text-sm px-4 py-3 rounded-md">
            {errors._global}
          </div>
        )}
        <div>
          <label
            htmlFor="pw"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            New password
          </label>
          <input
            id="pw"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          {errors.password && (
            <p className="text-err text-xs mt-1">{errors.password}</p>
          )}
        </div>
        <div>
          <label
            htmlFor="pw2"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            Confirm new password
          </label>
          <input
            id="pw2"
            type="password"
            autoComplete="new-password"
            required
            value={pw2}
            onChange={(e) => setPw2(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          {errors.password_confirm && (
            <p className="text-err text-xs mt-1">{errors.password_confirm}</p>
          )}
        </div>
        <Button
          type="submit"
          variant="solid"
          loading={pending}
          className="w-full"
        >
          Update password
        </Button>
      </form>

      <p className="text-mist text-sm text-center mt-8">
        <Link
          href="/login"
          className="text-gold hover:text-gold-hi underline underline-offset-4"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
