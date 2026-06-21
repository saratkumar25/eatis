import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, toZonedTime } from "date-fns-tz";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const IST = "Asia/Kolkata";

/**
 * Format a UTC ISO string for display in IST.
 * e.g.  "2026-06-28T13:30:00Z"  →  "Jun 28, 19:00"
 */
export function formatIST(
  iso: string | null | undefined,
  fmt = "MMM d, yyyy HH:mm",
): string {
  if (!iso) return "—";
  try {
    return format(toZonedTime(new Date(iso), IST), fmt, { timeZone: IST });
  } catch {
    return "—";
  }
}

/**
 * Convert a UTC ISO string to a datetime-local input value in IST.
 * Used to pre-fill edit forms so the user sees IST times.
 * e.g.  "2026-06-28T13:30:00Z"  →  "2026-06-28T19:00"
 */
export function toISTInputValue(iso: string | null | undefined): string {
  if (!iso) return "";
  try {
    return format(toZonedTime(new Date(iso), IST), "yyyy-MM-dd'T'HH:mm", { timeZone: IST });
  } catch {
    return "";
  }
}
