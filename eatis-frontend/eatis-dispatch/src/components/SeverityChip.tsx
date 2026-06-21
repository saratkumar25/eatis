import type { Severity } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<Severity, string> = {
  low: "bg-sev-low",
  medium: "bg-sev-medium text-black",
  high: "bg-sev-high",
  critical: "bg-sev-critical",
};

export function SeverityChip({
  level,
  className,
}: {
  level: Severity;
  className?: string;
}) {
  return <span className={cn("sign-chip", styles[level], className)}>{level}</span>;
}

export const severityHex: Record<Severity, string> = {
  low: "#2E933C",
  medium: "#E0C32C",
  high: "#E8841A",
  critical: "#D7263D",
};
