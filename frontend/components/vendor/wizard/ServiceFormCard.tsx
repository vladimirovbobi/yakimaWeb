"use client";

import Input from "@/components/ui/Input";
import PackageInput, { PackageInputData } from "./PackageInput";
import ImageUploader, { UploadedImage } from "./ImageUploader";

export interface ServiceFormData {
  title: string;
  description: string;
  hero?: UploadedImage;
  price_low: number | "";
  price_high: number | "";
  packages: PackageInputData[];
}

export function emptyService(): ServiceFormData {
  return {
    title: "",
    description: "",
    price_low: "",
    price_high: "",
    packages: [
      { tier: "basic", name: "", description: "", price: "", delivery_days: "", deliverables: [] },
      { tier: "standard", name: "", description: "", price: "", delivery_days: "", deliverables: [] },
      { tier: "premium", name: "", description: "", price: "", delivery_days: "", deliverables: [] },
    ],
  };
}

interface Props {
  index: number;
  value: ServiceFormData;
  onChange: (next: ServiceFormData) => void;
  onRemove?: () => void;
  onBlurAny: () => void;
}

export default function ServiceFormCard({
  index,
  value,
  onChange,
  onRemove,
  onBlurAny,
}: Props) {
  function set<K extends keyof ServiceFormData>(k: K, v: ServiceFormData[K]) {
    onChange({ ...value, [k]: v });
  }

  function setPackage(i: number, next: PackageInputData) {
    const ps = value.packages.slice();
    ps[i] = next;
    onChange({ ...value, packages: ps });
  }

  return (
    <article className="border border-gold/14 bg-panel/60 p-6 rounded-md">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-serif text-2xl text-gold">Service {index + 1}</h3>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className="text-[11px] uppercase tracking-luxe text-mist hover:text-rose-400"
          >
            Remove
          </button>
        )}
      </div>

      <div className="space-y-4">
        <Input
          label="Title"
          value={value.title}
          onChange={(e) => set("title", e.target.value)}
          onBlur={onBlurAny}
          placeholder="Real estate photography"
        />
        <div>
          <label className="block text-[11px] uppercase tracking-luxe text-mist mb-2">
            Description (markdown)
          </label>
          <textarea
            rows={5}
            value={value.description}
            onChange={(e) => set("description", e.target.value)}
            onBlur={onBlurAny}
            className="w-full bg-warm border border-gold/22 text-ivory placeholder-dim px-4 py-3 text-sm rounded-md focus:outline-none focus:ring-2 focus:ring-gold focus:border-gold"
            placeholder="What buyers get, why it's better, your process."
          />
        </div>
        <div>
          <label className="block text-[11px] uppercase tracking-luxe text-mist mb-2">
            Hero image
          </label>
          <ImageUploader
            value={value.hero ? [value.hero] : []}
            onChange={(arr) => set("hero", arr[0])}
            uploadType="service-hero"
            max={1}
            reorderable={false}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Price low"
            type="number"
            min={0}
            value={value.price_low}
            onChange={(e) =>
              set(
                "price_low",
                e.target.value === "" ? "" : Number(e.target.value),
              )
            }
            onBlur={onBlurAny}
          />
          <Input
            label="Price high"
            type="number"
            min={0}
            value={value.price_high}
            onChange={(e) =>
              set(
                "price_high",
                e.target.value === "" ? "" : Number(e.target.value),
              )
            }
            onBlur={onBlurAny}
          />
        </div>

        <div className="pt-2">
          <h4 className="font-serif text-lg text-ivory mb-4">Packages</h4>
          <div className="grid gap-4 lg:grid-cols-3">
            {value.packages.map((p, i) => (
              <PackageInput
                key={p.tier}
                value={p}
                onChange={(next) => {
                  setPackage(i, next);
                  onBlurAny();
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}
