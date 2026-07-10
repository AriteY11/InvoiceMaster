import { X } from "lucide-react";
import { useCopyStore, COPY_FIELDS } from "@/store/copy";

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function CopyConfigDialog({ open, onClose }: Props) {
  const selectedFields = useCopyStore((s) => s.selectedFields);
  const toggleField = useCopyStore((s) => s.toggleField);
  const selectAll = useCopyStore((s) => s.selectAll);
  const deselectAll = useCopyStore((s) => s.deselectAll);

  if (!open) return null;

  const all = selectedFields.length === COPY_FIELDS.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="relative w-full max-w-lg max-h-[80vh] overflow-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white">
            复制配置
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-5 py-3 flex items-center gap-3 border-b border-gray-100 dark:border-gray-800">
          <button
            onClick={all ? deselectAll : selectAll}
            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            {all ? "取消全选" : "全选"}
          </button>
          <span className="text-xs text-gray-400">
            已选 {selectedFields.length}/{COPY_FIELDS.length}
          </span>
        </div>

        <div className="px-5 py-3 grid grid-cols-2 gap-2">
          {COPY_FIELDS.map(({ key, label }) => (
            <label
              key={key}
              className="flex items-center gap-2 cursor-pointer text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            >
              <input
                type="checkbox"
                checked={selectedFields.includes(key)}
                onChange={() => toggleField(key)}
                className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              {label}
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
