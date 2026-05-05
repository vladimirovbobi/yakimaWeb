// Vendor onboarding step definitions — pure data, no React.
// Lives in its own module so server components can import without pulling
// the "use client" boundary of WizardChrome.tsx (which breaks page.tsx
// static collection: client modules export Proxy refs, not plain arrays).

export const STEPS = [
  { key: "business",   label: "Business" },
  { key: "categories", label: "Categories" },
  { key: "services",   label: "Services" },
  { key: "gallery",    label: "Gallery" },
  { key: "publish",    label: "Publish" },
] as const;

export type StepKey = (typeof STEPS)[number]["key"];
