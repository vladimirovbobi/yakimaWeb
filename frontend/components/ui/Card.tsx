"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export function Card({ className, hover = true, children, ...rest }: CardProps) {
  if (hover) {
    return (
      <motion.div
        whileHover={{ y: -4 }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className={cn(
          "bg-deep border border-gold/14 transition-colors duration-300 hover:border-gold/35 flex flex-col",
          className,
        )}
        {...(rest as React.ComponentProps<typeof motion.div>)}
      >
        {children}
      </motion.div>
    );
  }
  return (
    <div
      className={cn(
        "bg-deep border border-gold/14 flex flex-col",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-6 md:p-7 border-b border-gold/14", className)} {...rest}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "font-serif text-xl md:text-2xl font-light text-ivory leading-tight",
        className,
      )}
      {...rest}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-mist text-sm mt-2 leading-relaxed", className)} {...rest}>
      {children}
    </p>
  );
}

export function CardBody({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-6 md:p-7 flex-1", className)} {...rest}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-6 md:px-7 py-5 border-t border-gold/14 mt-auto",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
