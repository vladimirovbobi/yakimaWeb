"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";

function passwordStrength(p: string): {
  score: 0 | 1 | 2 | 3 | 4;
  label: string;
} {
  if (p.length === 0) return { score: 0, label: "" };
  if (p.length < 8) return { score: 1, label: "Too short" };
  let score = 1;
  if (/[A-Z]/.test(p)) score++;
  if (/\d/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p) || p.length >= 14) score++;
  const labels = ["", "Weak", "Okay", "Strong", "Excellent"] as const;
  return { score: Math.min(score, 4) as 0 | 1 | 2 | 3 | 4, label: labels[Math.min(score, 4)] };
}

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [isRealtor, setIsRealtor] = useState(false);
  const [accept, setAccept] = useState(false);
  const [pending, setPending] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const strength = useMemo(() => passwordStrength(pw), [pw]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pending) return;
    if (pw !== pw2) {
      setErrors({ password_confirm: "Passwords don't match." });
      return;
    }
    if (!accept) {
      setErrors({ accept: "You need to accept the terms to sign up." });
      return;
    }
    setPending(true);
    setErrors({});
    try {
      await apiFetch("/api/v1/auth/signup/", {
        method: "POST",
        body: JSON.stringify({ email, password: pw, password_confirm: pw2 }),
      });
      try {
        if (isRealtor) {
          localStorage.setItem("yw_signup_role", "realtor");
        }
      } catch {
        // localStorage unavailable - skip
      }
      router.push(`/verify-email-sent?email=${encodeURIComponent(email)}`);
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
          e.problem.detail || e.problem.title || "Could not sign up";
      }
      setErrors(flat);
    } finally {
      setPending(false);
    }
  }

  const strengthColor =
    strength.score >= 4
      ? "bg-ok"
      : strength.score === 3
        ? "bg-gold"
        : strength.score === 2
          ? "bg-warn"
          : "bg-err";

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-8 sm:mb-10">
        <div className="min-w-0">
          <h1 className="font-serif font-light text-ivory text-2xl sm:text-3xl leading-tight">
            Create account
          </h1>
          <p className="text-mist text-sm mt-2">
            Free. Takes 30 seconds.
          </p>
        </div>
        <Link
          href="/login"
          className="flex-shrink-0 min-h-11 inline-flex items-center text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
        >
          Sign in
        </Link>
      </div>

      <form onSubmit={onSubmit} className="space-y-5">
        {errors._global && (
          <div className="border border-err/30 bg-err/10 text-err text-sm px-4 py-3 rounded-md">
            {errors._global}
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
          {errors.email && (
            <p className="text-err text-xs mt-1">{errors.email}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md min-h-11 focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          {pw && (
            <div className="mt-2 flex items-center gap-3">
              <div className="flex-1 h-1.5 bg-warm rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${strengthColor}`}
                  style={{ width: `${strength.score * 25}%` }}
                />
              </div>
              <span className="text-[11px] uppercase tracking-luxe text-mist">
                {strength.label}
              </span>
            </div>
          )}
          {errors.password && (
            <p className="text-err text-xs mt-1">{errors.password}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="password_confirm"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            Confirm password
          </label>
          <input
            id="password_confirm"
            type="password"
            autoComplete="new-password"
            required
            value={pw2}
            onChange={(e) => setPw2(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md min-h-11 focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          {errors.password_confirm && (
            <p className="text-err text-xs mt-1">{errors.password_confirm}</p>
          )}
        </div>

        <label className="flex items-start gap-3 cursor-pointer p-4 border border-gold/22 hover:border-gold/35 transition-colors rounded-md bg-deep">
          <input
            type="checkbox"
            checked={isRealtor}
            onChange={(e) => setIsRealtor(e.target.checked)}
            className="w-4 h-4 accent-gold mt-0.5"
          />
          <span className="text-sm text-mist leading-relaxed">
            <span className="text-ivory">I'm a licensed realtor.</span> After you
            sign in, we'll walk you through ARELLO license verification.
          </span>
        </label>

        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={accept}
            onChange={(e) => setAccept(e.target.checked)}
            required
            className="w-4 h-4 accent-gold mt-0.5"
          />
          <span className="text-xs text-mist leading-relaxed">
            I agree to the{" "}
            <Link
              href="/terms"
              className="text-gold underline underline-offset-4"
            >
              terms
            </Link>{" "}
            and{" "}
            <Link
              href="/privacy"
              className="text-gold underline underline-offset-4"
            >
              privacy policy
            </Link>
            .
          </span>
        </label>
        {errors.accept && (
          <p className="text-err text-xs">{errors.accept}</p>
        )}

        <Button
          type="submit"
          variant="solid"
          loading={pending}
          className="w-full"
        >
          Create account
        </Button>
      </form>

      <p className="text-mist text-sm text-center mt-8">
        Already have one?{" "}
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
