import { forwardRef, useId } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helper?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, helper, error, className, id, ...rest },
  ref,
) {
  const reactId = useId();
  const inputId = id || reactId;
  const helpId = `${inputId}-help`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
        >
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={!!error}
        aria-describedby={helper || error ? helpId : undefined}
        className={cn(
          "w-full bg-warm border text-ivory placeholder-dim",
          "px-4 py-3 text-sm rounded-md",
          "focus:outline-none focus:ring-2 focus:ring-gold focus:ring-offset-2 focus:ring-offset-black",
          "transition-colors duration-150",
          error
            ? "border-err focus:border-err focus:ring-err"
            : "border-gold/22 focus:border-gold",
          className,
        )}
        {...rest}
      />
      {(helper || error) && (
        <p
          id={helpId}
          className={cn(
            "mt-1.5 text-xs",
            error ? "text-err" : "text-mist",
          )}
        >
          {error || helper}
        </p>
      )}
    </div>
  );
});

export default Input;
