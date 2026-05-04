"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import { useAutosave } from "./useAutosave";
import type { AutosaveState } from "./useAutosave";
import ServiceFormCard, {
  emptyService,
  type ServiceFormData,
} from "./ServiceFormCard";

interface Props {
  initial?: ServiceFormData[];
  onSaveStateChange?: (s: AutosaveState) => void;
}

export default function ServicesStep({
  initial,
  onSaveStateChange,
}: Props) {
  const router = useRouter();
  const [services, setServices] = useState<ServiceFormData[]>(
    initial && initial.length > 0 ? initial : [emptyService()],
  );
  const [error, setError] = useState<string | null>(null);

  const { state, schedule, flush } = useAutosave<ServiceFormData[]>({
    onSave: async (value) => {
      await apiFetch(
        "/api/v1/vendors/onboard/services/",
        {
          method: "PATCH",
          body: JSON.stringify({ services: value }),
        },
        { auth: true },
      );
    },
  });

  useEffect(() => {
    onSaveStateChange?.(state);
  }, [state, onSaveStateChange]);

  function update(i: number, next: ServiceFormData) {
    setServices((curr) => {
      const arr = curr.slice();
      arr[i] = next;
      schedule(arr);
      return arr;
    });
  }

  function add() {
    setServices((curr) => {
      const arr = [...curr, emptyService()];
      schedule(arr);
      return arr;
    });
  }

  function remove(i: number) {
    setServices((curr) => {
      const arr = curr.filter((_, idx) => idx !== i);
      schedule(arr);
      return arr;
    });
  }

  async function continueNext() {
    setError(null);
    if (services.length === 0) {
      setError("Add at least one service.");
      return;
    }
    if (services.some((s) => !s.title.trim() || !s.description.trim())) {
      setError("Each service needs a title and description.");
      return;
    }
    await flush(services);
    router.push("/dashboard/vendor/onboard/gallery");
  }

  return (
    <section className="max-w-4xl">
      <h1 className="font-serif text-3xl text-gold mb-2">Your services</h1>
      <p className="text-sm text-mist mb-8">
        Add the offerings you want buyers to book.
      </p>
      <div className="space-y-6">
        {services.map((s, i) => (
          <ServiceFormCard
            key={i}
            index={i}
            value={s}
            onChange={(n) => update(i, n)}
            onRemove={services.length > 1 ? () => remove(i) : undefined}
            onBlurAny={() => flush(services)}
          />
        ))}
      </div>
      <div className="mt-6">
        <Button type="button" variant="secondary" onClick={add}>
          Add another service
        </Button>
      </div>
      {error && (
        <p role="alert" className="mt-4 text-xs text-err">
          {error}
        </p>
      )}
      <div className="pt-8 flex justify-between">
        <Button href="/dashboard/vendor/onboard/categories" variant="ghost">
          Back
        </Button>
        <Button type="button" variant="solid" onClick={continueNext}>
          Continue
        </Button>
      </div>
    </section>
  );
}
