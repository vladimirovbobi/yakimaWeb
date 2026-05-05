import Link from "next/link";
import Image from "next/image";
import type { VendorProfile } from "@/lib/api/types";
import { vendorLogoPlaceholder } from "@/lib/placeholders";

interface VendorChipProps {
  vendor: VendorProfile;
  size?: "sm" | "md";
}

export default function VendorChip({ vendor, size = "md" }: VendorChipProps) {
  const dim = size === "sm" ? 24 : 32;
  const logoSrc =
    vendor.logo_url || vendorLogoPlaceholder(vendor.slug || vendor.id);
  return (
    <Link
      href={`/services/vendors/${vendor.slug}`}
      data-touch
      className="inline-flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold rounded py-1"
    >
      <Image
        src={logoSrc}
        alt=""
        width={dim}
        height={dim}
        className="rounded-full border border-gold/22"
      />
      <span
        className={
          size === "sm"
            ? "text-xs text-mist group-hover:text-gold-hi transition-colors"
            : "text-sm text-ivory group-hover:text-gold-hi transition-colors"
        }
      >
        {vendor.business_name}
      </span>
      {vendor.is_verified && (
        <span
          title="Verified vendor"
          aria-label="Verified vendor"
          className="w-2 h-2 rounded-full bg-gold"
        />
      )}
    </Link>
  );
}
