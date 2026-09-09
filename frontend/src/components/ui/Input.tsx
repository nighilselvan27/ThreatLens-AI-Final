import { InputHTMLAttributes, forwardRef } from "react";
import { cn } from "@/utils/cn";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({ className, error, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        "w-full h-11 rounded-lg bg-background-surface border border-border px-3.5 text-sm text-slate-100 placeholder:text-slate-500",
        "focus:outline-none focus:ring-2 focus:ring-accent-cyan/50 focus:border-accent-cyan/50 transition-colors",
        error && "border-severity-critical/60 focus:ring-severity-critical/40",
        className
      )}
      {...props}
    />
  );
});
Input.displayName = "Input";

export default Input;
