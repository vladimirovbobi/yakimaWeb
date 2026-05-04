"use client";

import { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

function LoginInner() {
  const router = useRouter();
  const sp = useSearchParams();
  const next = sp.get("next") || "/dashboard";
  const toast = useToast();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [stay, setStay] = useState(true);
  const [pending, setPending] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [needsTotp, setNeedsTotp] = useState(false);
  const [totp, setTotp] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pending) return;
    setPending(true);
    setErrors({});
    try {
      await apiFetch("/api/v1/auth/login/", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          stay_signed_in: stay,
          totp_code: totp || undefined,
        }),
      });
      toast.push("Signed in", "success");
      router.push(next);
      router.refresh();
    } catch (err) {
      const e = err as ApiError;
      if (e.status === 401 && e.problem.code === "totp_required") {
        setNeedsTotp(true);
        setPending(false);
        return;
      }
      const flat: Record<string, string> = {};
      if (e.problem.errors) {
        for (const [k, v] of Object.entries(e.problem.errors)) {
          flat[k] = Array.isArray(v) ? v[0] : String(v);
        }
      }
      if (Object.keys(flat).length === 0) {
        flat._global =
          e.problem.detail || e.problem.title || "Could not sign in";
      }
      setErrors(flat);
    } finally {
      setPending(false);
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="font-serif font-light text-ivory text-3xl leading-tight">
            Sign in
          </h1>
          <p className="text-mist text-sm mt-2">
            Welcome back to Yakima Web.
          </p>
        </div>
        <Link
          href="/signup"
          className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
        >
          Sign up
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
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          {errors.email && (
            <p className="text-err text-xs mt-1">{errors.email}</p>
          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label
              htmlFor="password"
              className="text-[11px] uppercase tracking-luxe text-mist"
            >
              Password
            </label>
            <Link
              href="/password-reset"
              className="text-[11px] uppercase tracking-luxe text-gold hover:text-gold-hi"
            >
              Forgot?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
          {errors.password && (
            <p className="text-err text-xs mt-1">{errors.password}</p>
          )}
        </div>

        {needsTotp && (
          <div>
            <label
              htmlFor="totp"
              className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
            >
              Authenticator code
            </label>
            <input
              id="totp"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              required
              autoFocus
              value={totp}
              onChange={(e) => setTotp(e.target.value.replace(/\D/g, ""))}
              placeholder="000000"
              className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold tracking-[0.5em] text-center font-mono"
            />
          </div>
        )}

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={stay}
            onChange={(e) => setStay(e.target.checked)}
            className="w-4 h-4 accent-gold"
          />
          <span className="text-sm text-mist">Stay signed in</span>
        </label>

        <Button
          type="submit"
          variant="solid"
          loading={pending}
          className="w-full"
        >
          Sign in
        </Button>
      </form>

      <p className="text-mist text-sm text-center mt-8">
        New here?{" "}
        <Link
          href="/signup"
          className="text-gold hover:text-gold-hi underline underline-offset-4"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}
