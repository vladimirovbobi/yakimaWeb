"use client";

export interface FlyerPresetSummary {
  slug: string;
  name: string;
  blurb: string;
  inspiration: string;
  palette: { primary: string; secondary: string; accent: string; bg: string; fg: string };
  fonts: { heading: string; body: string; label?: string };
}

interface Props {
  preset: FlyerPresetSummary;
  selected: boolean;
  onSelect: (slug: string) => void;
}

export default function PresetCard({ preset, selected, onSelect }: Props) {
  const swatches = [
    preset.palette.primary,
    preset.palette.secondary,
    preset.palette.accent,
    preset.palette.bg,
    preset.palette.fg,
  ];
  const ringClass = selected
    ? "ring-2 ring-gold border-gold/60"
    : "border-gold/22 hover:border-gold/40";
  return (
    <button
      type="button"
      onClick={() => onSelect(preset.slug)}
      aria-pressed={selected}
      className={`text-left bg-panel border ${ringClass} p-5 transition-all duration-300 ease-luxe`}
    >
      <div className="ey text-gold-dim mb-2">{preset.inspiration}</div>
      <h3
        className="font-serif text-2xl text-ivory leading-tight mb-3"
        style={{ fontFamily: preset.fonts.heading }}
      >
        {preset.name}
      </h3>
      <p className="text-mist text-sm leading-relaxed mb-5">{preset.blurb}</p>
      <div className="flex items-center gap-2 mb-4">
        {swatches.map((hex, i) => (
          <span
            key={`${preset.slug}-${i}`}
            aria-hidden
            className="block w-6 h-6 border border-gold/14"
            style={{ backgroundColor: hex }}
            title={hex}
          />
        ))}
      </div>
      <div className="text-[11px] uppercase tracking-cap text-dim">
        {selected ? "Selected" : "Choose this style"}
      </div>
    </button>
  );
}
