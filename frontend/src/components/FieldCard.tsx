import { cn } from "@/lib/utils";

interface FieldCardProps {
  label: string;
  value: string | number | null | undefined;
  className?: string;
}

export default function FieldCard({ label, value, className }: FieldCardProps) {
  const displayValue = value !== null && value !== undefined && value !== ""
    ? String(value)
    : null;

  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
        {label}
      </span>
      {displayValue ? (
        <span className="text-sm text-gray-900 dark:text-gray-100 break-all">
          {displayValue}
        </span>
      ) : (
        <span className="text-sm text-gray-400 dark:text-gray-600 italic">
          未识别
        </span>
      )}
    </div>
  );
}
