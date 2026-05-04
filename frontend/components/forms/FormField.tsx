import { useId } from "react";
import { cn } from "@/lib/utils";

interface FormFieldProps {
  label: string;
  helper?: string;
  error?: string;
  required?: boolean;
  className?: string;
  children: (props: {
    id: string;
    "aria-describedby": string | undefined;
    "aria-invalid": boolean;
  }) => React.ReactNode;
}

export default function FormField({
  label,
  helper,
  error,
  required,
  className,
  children,
}: FormFieldProps) {
  const id = useId();
  const helpId = `${id}-help`;
  const describedBy = error || helper ? helpId : undefined;
  return (
    <div className={cn("w-full", className)}>
      <label
        htmlFor={id}
        className="block text-[11px] uppercase tracking-luxe text-mist mb-2"
      >
        {label}
        {required && <span className="text-gold ml-1">*</span>}
      </label>
      {children({ id, "aria-describedby": describedBy, "aria-invalid": !!error })}
      {(helper || error) && (
        <p
          id={helpId}
          className={cn("mt-1.5 text-xs", error ? "text-err" : "text-mist")}
        >
          {error || helper}
        </p>
      )}
    </div>
  );
}
