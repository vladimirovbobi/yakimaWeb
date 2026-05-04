import Link from "next/link";
import Image from "next/image";
import type { VendorProfile } from "@/lib/api/types";

interface VendorChipProps {
  vendor: VendorProfile;
  size?: "sm" | "md";
}

export default function VendorChip({ vendor, size = "md" }: VendorChipProps) {
  const dim = size === "sm" ? 24 : 32;
  return (
    <Link
      href={`/services/vendors/${vendor.slug}`}
      className="inline-flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold rounded"
    >
      {vendor.logo_url ? (
        <Image
          src={vendor.logo_url}
          alt=""
          width={dim}
          height={dim}
          className="rounded-full border border-gold/22"
        />
      ) : (
        <div
          aria-hidden
          className="rounded-full bg-warm border border-gold/22 flex items-center justify-center text-gold"
          style={{ width: dim, height: dim, fontSize: size === "sm" ? 10 : 12 }}
        >
          {vendor.business_name.charAt(0).toUpperCase()}
        </div>
      )}
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
