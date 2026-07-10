import { X } from "lucide-react";
import { useTimezoneStore, TIMEZONE_OPTIONS } from "@/store/timezone";

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function TimezoneDialog({ open, onClose }: Props) {
  const timezone = useTimezoneStore((s) => s.timezone);
  const setTimezone = useTimezoneStore((s) => s.setTimezone);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="relative w-full max-w-md rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white">
            时间配置
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-5 py-3 text-xs text-gray-500 dark:text-gray-400">
          选择时区后，系统中的上传时间将按此时区显示
        </div>

        <div className="px-5 pb-4 max-h-64 overflow-auto">
          {TIMEZONE_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className="flex items-center gap-2 cursor-pointer px-2 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <input
                type="radio"
                name="timezone"
                value={opt.value}
                checked={timezone === opt.value}
                onChange={() => setTimezone(opt.value)}
                className="h-3.5 w-3.5 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">{opt.label}</span>
            </label>
          ))}
        </div>

        <div className="px-5 py-3 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            确定
          </button>
        </div>
      </div>
    </div>
  );
}
