"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api/fetch";
import Button from "@/components/ui/Button";
import ImageUploader, { UploadedImage } from "./ImageUploader";
import { useAutosave } from "./useAutosave";
import type { AutosaveState } from "./useAutosave";

interface Props {
  initial?: UploadedImage[];
  onSaveStateChange?: (s: AutosaveState) => void;
}

export default function GalleryStep({
  initial = [],
  onSaveStateChange,
}: Props) {
  const router = useRouter();
  const [images, setImages] = useState<UploadedImage[]>(initial);
  const { state, schedule, flush } = useAutosave<UploadedImage[]>({
    onSave: async (value) => {
      await apiFetch(
        "/api/v1/vendors/onboard/gallery/",
        {
          method: "PATCH",
          body: JSON.stringify({ gallery: value }),
        },
        { auth: true },
      );
    },
  });

  useEffect(() => {
    onSaveStateChange?.(state);
  }, [state, onSaveStateChange]);

  function setAll(next: UploadedImage[]) {
    setImages(next);
    schedule(next);
  }

  async function continueNext() {
    await flush(images);
    router.push("/dashboard/vendor/onboard/publish");
  }

  return (
    <section className="max-w-4xl">
      <h1 className="font-serif text-3xl text-gold mb-2">Your portfolio</h1>
      <p className="text-sm text-mist mb-8">
        Up to 12 images of your best work. Drag to reorder.
      </p>
      <ImageUploader
        value={images}
        onChange={setAll}
        uploadType="gallery"
        max={12}
        reorderable
      />
      <div className="pt-8 flex justify-between">
        <Button href="/dashboard/vendor/onboard/services" variant="ghost">
          Back
        </Button>
        <Button type="button" variant="solid" onClick={continueNext}>
          Continue
        </Button>
      </div>
    </section>
  );
}
