"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api/fetch";
import { useToast } from "@/components/ui/Toast";
import Button from "@/components/ui/Button";
import type { Service } from "@/lib/api/types";
import type { CurrentUser } from "@/lib/auth/server";

interface InquiryFormProps {
  service: Service;
  user: CurrentUser;
}

export default function InquiryForm({ service, user }: InquiryFormProps) {
  const [packageId, setPackageId] = useState<number | "">("");
  const [name, setName] = useState(user.display_name || "");
  const [email, setEmail] = useState(user.email);
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const router = useRouter();
  const toast = useToast();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pending) return;
    setPending(true);
    setErrors({});
    try {
      await apiFetch(
        `/api/v1/services/${service.slug}/inquiries/`,
        {
          method: "POST",
          body: JSON.stringify({
            package_id: packageId || null,
            name,
            email,
            phone,
            message,
          }),
        },
        { auth: true },
      );
      toast.push("Inquiry sent. The vendor will reach out.", "success");
      setMessage("");
      setPhone("");
      router.refresh();
    } catch (err) {
      const e = err as ApiError;
      const flat: Record<string, string> = {};
      if (e.problem.errors) {
        for (const [k, v] of Object.entries(e.problem.errors)) {
          flat[k] = Array.isArray(v) ? v[0] : String(v);
        }
      }
      setErrors(flat);
      if (Object.keys(flat).length === 0) {
        toast.push(e.problem.detail || "Could not send inquiry", "error");
      }
    } finally {
      setPending(false);
    }
  }

  const packages = service.packages || [];

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      {packages.length > 0 && (
        <div>
          <label
            htmlFor="inq-pkg"
            className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
          >
            Package
          </label>
          <select
            id="inq-pkg"
            value={packageId}
            onChange={(e) =>
              setPackageId(e.target.value ? Number(e.target.value) : "")
            }
            className="w-full bg-warm border border-gold/22 text-ivory px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          >
            <option value="">No package - general inquiry</option>
            {packages.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} - ${p.price.toLocaleString()}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        <label
          htmlFor="inq-name"
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          Your name
        </label>
        <input
          id="inq-name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full bg-warm border border-gold/22 text-ivory px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
        />
        {errors.name && <p className="text-err text-xs mt-1">{errors.name}</p>}
      </div>

      <div>
        <label
          htmlFor="inq-email"
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          Email
        </label>
        <input
          id="inq-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-warm border border-gold/22 text-ivory px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
        />
        {errors.email && <p className="text-err text-xs mt-1">{errors.email}</p>}
      </div>

      <div>
        <label
          htmlFor="inq-phone"
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          Phone (optional)
        </label>
        <input
          id="inq-phone"
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="w-full bg-warm border border-gold/22 text-ivory px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
        />
      </div>

      <div>
        <label
          htmlFor="inq-msg"
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          Message
        </label>
        <textarea
          id="inq-msg"
          required
          rows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Tell them about the property, timeline, anything that helps."
          className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-3 py-2.5 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold resize-y"
        />
        {errors.message && (
          <p className="text-err text-xs mt-1">{errors.message}</p>
        )}
      </div>

      <Button type="submit" variant="solid" loading={pending} className="w-full">
        Send inquiry
      </Button>
      <p className="text-[11px] text-dim text-center">
        Direct to the vendor. We don't take a cut.
      </p>
    </form>
  );
}
