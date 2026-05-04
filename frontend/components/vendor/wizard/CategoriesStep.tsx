"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { useAutosave } from "./useAutosave";
import type { AutosaveState } from "./useAutosave";

interface CategoryNode {
  id: number;
  slug: string;
  name: string;
  depth: number;
  children: CategoryNode[];
}

interface Props {
  initial?: string[];
  onSaveStateChange?: (s: AutosaveState) => void;
}

const MAX_PICKS = 3;

export default function CategoriesStep({
  initial = [],
  onSaveStateChange,
}: Props) {
  const router = useRouter();
  const [tree, setTree] = useState<CategoryNode[] | null>(null);
  const [picked, setPicked] = useState<string[]>(initial);
  const [error, setError] = useState<string | null>(null);

  const { state, schedule, flush } = useAutosave<string[]>({
    onSave: async (value) => {
      await apiFetch(
        "/api/v1/vendors/onboard/categories/",
        {
          method: "PATCH",
          body: JSON.stringify({ categories: value }),
        },
        { auth: true },
      );
    },
  });

  useEffect(() => {
    onSaveStateChange?.(state);
  }, [state, onSaveStateChange]);

  useEffect(() => {
    let cancel = false;
    apiFetch<CategoryNode[]>("/api/public/v1/services/categories/", {})
      .then((rows) => {
        if (!cancel) setTree(rows);
      })
      .catch(() => {
        if (!cancel) setTree([]);
      });
    return () => {
      cancel = true;
    };
  }, []);

  function toggle(slug: string) {
    setPicked((curr) => {
      let next: string[];
      if (curr.includes(slug)) {
        next = curr.filter((s) => s !== slug);
      } else {
        if (curr.length >= MAX_PICKS) {
          setError(`You can pick up to ${MAX_PICKS} categories.`);
          return curr;
        }
        next = [...curr, slug];
        setError(null);
      }
      schedule(next);
      return next;
    });
  }

  async function continueNext() {
    if (picked.length === 0) {
      setError("Pick at least one category.");
      return;
    }
    await flush(picked);
    router.push("/dashboard/vendor/onboard/services");
  }

  return (
    <section className="max-w-3xl">
      <h1 className="font-serif text-3xl text-gold mb-2">Pick your categories</h1>
      <p className="text-sm text-mist mb-2">
        Up to {MAX_PICKS} so buyers find you in the right places.
      </p>
      <p className="text-[11px] uppercase tracking-luxe text-dim mb-8">
        {picked.length}/{MAX_PICKS} selected
      </p>

      {tree === null ? (
        <p className="text-mist">Loading categories…</p>
      ) : tree.length === 0 ? (
        <p className="text-mist">No categories available yet.</p>
      ) : (
        <ul className="space-y-6">
          {tree.map((node) => (
            <CategoryBranch
              key={node.id}
              node={node}
              picked={picked}
              onToggle={toggle}
            />
          ))}
        </ul>
      )}

      {error && (
        <p role="alert" className="mt-4 text-xs text-err">
          {error}
        </p>
      )}

      <div className="pt-8 flex justify-between">
        <Button href="/dashboard/vendor/onboard/business" variant="ghost">
          Back
        </Button>
        <Button type="button" variant="solid" onClick={continueNext}>
          Continue
        </Button>
      </div>
    </section>
  );
}

function CategoryBranch({
  node,
  picked,
  onToggle,
}: {
  node: CategoryNode;
  picked: string[];
  onToggle: (slug: string) => void;
}) {
  const isLeaf = !node.children || node.children.length === 0;
  return (
    <li>
      <p className="font-serif text-lg text-ivory mb-2">{node.name}</p>
      {isLeaf ? (
        <CategoryChip
          slug={node.slug}
          name={node.name}
          active={picked.includes(node.slug)}
          onToggle={onToggle}
        />
      ) : (
        <ul className="flex flex-wrap gap-2">
          {node.children.map((c) => (
            <li key={c.id}>
              <CategoryChip
                slug={c.slug}
                name={c.name}
                active={picked.includes(c.slug)}
                onToggle={onToggle}
              />
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

function CategoryChip({
  slug,
  name,
  active,
  onToggle,
}: {
  slug: string;
  name: string;
  active: boolean;
  onToggle: (slug: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onToggle(slug)}
      className={cn(
        "px-4 py-2 text-xs uppercase tracking-luxe border rounded-full transition-colors",
        active
          ? "bg-gold text-black border-gold"
          : "border-gold/30 text-mist hover:border-gold hover:text-gold",
      )}
    >
      {name}
    </button>
  );
}
