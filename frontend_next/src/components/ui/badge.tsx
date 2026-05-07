import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "outline" | "success" | "warning" | "danger";
}
const variantClasses: Record<string, string> = {
  default: "bg-slate-100 text-slate-700",
  outline: "border border-slate-200 text-slate-700",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-700",
};

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return <div className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", variantClasses[variant], className)} {...props} />;
}
export { Badge };
