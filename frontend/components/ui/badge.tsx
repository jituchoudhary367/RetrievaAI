import React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: "default" | "success" | "warning" | "destructive" | "neutral";
}

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  const tones = {
    default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    success: "border-transparent bg-green-500/10 text-green-700 hover:bg-green-500/20",
    warning: "border-transparent bg-yellow-500/10 text-yellow-700 hover:bg-yellow-500/20",
    destructive: "border-transparent bg-red-500/10 text-red-700 hover:bg-red-500/20",
    neutral: "border-transparent bg-gray-500/10 text-gray-700 hover:bg-gray-500/20",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}
