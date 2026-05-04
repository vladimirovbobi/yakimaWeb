import Link from "next/link";
import { cn } from "@/lib/utils";

interface SignInPromptProps {
  verb: string;
  next?: string;
  className?: string;
}

export default function SignInPrompt({
  verb,
  next,
  className,
}: SignInPromptProps) {
  const href = next ? `/login?next=${encodeURIComponent(next)}` : "/login";
  return (
    <div
      className={cn(
        "border border-gold/22 bg-deep p-6 text-center",
        className,
      )}
    >
      <p className="text-mist text-sm leading-relaxed">
        <Link
          href={href}
          className="text-gold hover:text-gold-hi underline underline-offset-4"
        >
          Sign in
        </Link>{" "}
        to {verb}.
      </p>
    </div>
  );
}
