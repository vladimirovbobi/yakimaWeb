"use client";

import Input from "@/components/ui/Input";
import { useState } from "react";

export interface PackageInputData {
  tier: "basic" | "standard" | "premium";
  name: string;
  description: string;
  price: number | "";
  delivery_days: number | "";
  deliverables: string[];
}

interface Props {
  value: PackageInputData;
  onChange: (next: PackageInputData) => void;
}

export default function PackageInput({ value, onChange }: Props) {
  const [chip, setChip] = useState("");

  function set<K extends keyof PackageInputData>(k: K, v: PackageInputData[K]) {
    onChange({ ...value, [k]: v });
  }

  function addChip() {
    const text = chip.trim();
    if (!text) return;
    if (value.deliverables.includes(text)) return;
    onChange({ ...value, deliverables: [...value.deliverables, text] });
    setChip("");
  }

  function removeChip(t: string) {
    onChange({
      ...value,
      deliverables: value.deliverables.filter((d) => d !== t),
    });
  }

  return (
    <div className="bg-warm/40 border border-gold/14 p-4 rounded-md">
      <div className="text-[11px] uppercase tracking-luxe text-gold mb-3">
        {value.tier} package
      </div>
      <div className="space-y-3">
        <Input
          label="Name"
          value={value.name}
          onChange={(e) => set("name", e.target.value)}
          placeholder="Listing essentials"
        />
        <div>
          <label className="block text-[11px] uppercase tracking-luxe text-mist mb-2">
            Description
          </label>
          <textarea
            rows={3}
            value={value.description}
            onChange={(e) => set("description", e.target.value)}
            className="w-full bg-warm border border-gold/22 text-ivory px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Price (USD)"
            type="number"
            min={0}
            value={value.price}
            onChange={(e) =>
              set("price", e.target.value === "" ? "" : Number(e.target.value))
            }
          />
          <Input
            label="Turnaround (days)"
            type="number"
            min={1}
            value={value.delivery_days}
            onChange={(e) =>
              set(
                "delivery_days",
                e.target.value === "" ? "" : Number(e.target.value),
              )
            }
          />
        </div>
        <div>
          <label className="block text-[11px] uppercase tracking-luxe text-mist mb-2">
            Deliverables
          </label>
          <div className="flex gap-2 flex-wrap mb-2">
            {value.deliverables.map((d) => (
              <span
                key={d}
                className="inline-flex items-center gap-2 bg-black/40 border border-gold/22 text-ivory px-3 py-1 text-xs rounded-full"
              >
                {d}
                <button
                  type="button"
                  onClick={() => removeChip(d)}
                  className="text-mist hover:text-rose-400"
                  aria-label={`Remove ${d}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={chip}
              onChange={(e) => setChip(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addChip();
                }
              }}
              placeholder="e.g. 25 photos, virtual tour"
              className="flex-1 bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-2 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
            />
            <button
              type="button"
              onClick={addChip}
              className="px-4 py-2 text-[11px] uppercase tracking-luxe border border-gold/30 text-mist hover:border-gold hover:text-gold rounded-md"
            >
              Add
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
