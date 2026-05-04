import { cn } from "@/lib/utils";

interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  as?: "div" | "section" | "main" | "article" | "header" | "footer";
}

export default function Container({
  as = "div",
  className,
  children,
  ...rest
}: ContainerProps) {
  const Tag = as;
  return (
    <Tag
      className={cn(
        "max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-12",
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}
