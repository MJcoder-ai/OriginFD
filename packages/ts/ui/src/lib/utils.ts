import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility for combining class names using clsx and tailwind-merge.
 * Mimics shadcn/ui's `cn` helper.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(...inputs));
}
