import Link from "next/link";
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "solid";
type Size = "sm" | "md" | "lg";

const variants: Record<Variant, string> = {
  primary:
    "border border-gold/52 text-gold hover:bg-gold hover:text-black hover:border-gold",
  solid: "bg-gold text-black hover:bg-gold-hi shadow-card hover:shadow-gold-glow",
  secondary:
    "border border-mist/20 text-mist hover:text-gold hover:border-gold/40",
  ghost: "text-mist hover:text-ivory",
};

const sizes: Record<Size, string> = {
  sm: "px-4 py-2 text-[11px] min-h-11",
  md: "px-6 py-3 text-xs min-h-11",
  lg: "px-8 py-4 text-sm min-h-11",
};

interface ButtonBaseProps {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  className?: string;
  children: React.ReactNode;
}

interface ButtonProps
  extends ButtonBaseProps,
    Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  href?: undefined;
}

interface AnchorProps extends ButtonBaseProps {
  href: string;
  external?: boolean;
}

export type Props = ButtonProps | AnchorProps;

const baseClasses =
  "inline-flex items-center justify-center gap-2 uppercase tracking-cap font-medium transition-colors duration-200 ease-luxe focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold focus-visible:ring-offset-2 focus-visible:ring-offset-black disabled:opacity-50 disabled:cursor-not-allowed";

const Button = forwardRef<HTMLButtonElement | HTMLAnchorElement, Props>(
  function Button(
    {
      variant = "primary",
      size = "md",
      loading,
      className,
      children,
      ...rest
    },
    ref,
  ) {
    const cls = cn(baseClasses, variants[variant], sizes[size], className);

    const inner = loading ? (
      <span className="inline-flex items-center gap-2">
        <span
          aria-hidden
          className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin"
        />
        <span>Loading</span>
      </span>
    ) : (
      children
    );

    if ("href" in rest && rest.href) {
      const { href, external, ...anchorRest } = rest as AnchorProps;
      if (external) {
        return (
          <a
            ref={ref as React.Ref<HTMLAnchorElement>}
            href={href}
            className={cls}
            target="_blank"
            rel="noopener noreferrer"
            {...(anchorRest as React.AnchorHTMLAttributes<HTMLAnchorElement>)}
          >
            {inner}
          </a>
        );
      }
      return (
        <Link
          ref={ref as React.Ref<HTMLAnchorElement>}
          href={href}
          className={cls}
          {...(anchorRest as React.AnchorHTMLAttributes<HTMLAnchorElement>)}
        >
          {inner}
        </Link>
      );
    }

    const { ...buttonRest } = rest as ButtonProps;
    return (
      <button
        ref={ref as React.Ref<HTMLButtonElement>}
        className={cls}
        disabled={loading || buttonRest.disabled}
        {...buttonRest}
      >
        {inner}
      </button>
    );
  },
);

export default Button;
