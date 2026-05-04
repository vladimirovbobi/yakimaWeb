"use client";

import { useState } from "react";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";

export default function NewsletterSubscribe() {
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);
  const toast = useToast();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || pending) return;
    setPending(true);
    try {
      await apiFetch("/api/public/v1/posts/newsletter/", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setDone(true);
      setEmail("");
      toast.push("Subscribed. Watch your inbox.", "success");
    } catch (err) {
      const e = err as ApiError;
      toast.push(e.problem.detail || "Subscribe failed", "error");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="border border-gold/22 bg-deep p-10 md:p-16">
      <div className="max-w-2xl mx-auto text-center">
        <div className="ey mb-4">Get it in your inbox</div>
        <h2 className="font-serif font-light text-ivory text-[clamp(1.75rem,3.2vw,2.5rem)] leading-[1.15]">
          Yakima Valley real estate, in one weekly read.
        </h2>
        <p className="text-mist mt-4 leading-relaxed">
          New posts, market notes, and the occasional tool. No noise. Unsubscribe
          anytime.
        </p>

        {done ? (
          <p className="mt-8 text-gold uppercase tracking-luxe text-sm">
            You're on the list.
          </p>
        ) : (
          <form
            onSubmit={onSubmit}
            className="mt-8 flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
          >
            <label className="sr-only" htmlFor="newsletter-email">
              Email address
            </label>
            <input
              id="newsletter-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="flex-1 bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
            />
            <Button type="submit" variant="solid" loading={pending}>
              Subscribe
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
