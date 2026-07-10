import { useState } from "react";
import { X, Plus, Trash2, Loader2 } from "lucide-react";
import { createManualInvoices } from "@/api/client";
import type { ManualInvoiceInput } from "@/types/invoice";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

const EMPTY_CARD: ManualInvoiceInput = {
  invoice_name: "",
  invoice_number: "",
  invoice_code: "",
  issue_date: "",
  invoice_type: "",
  buyer_name: "",
  buyer_tax_number: "",
  seller_name: "",
  seller_tax_number: "",
  total_amount: undefined,
  tax_amount: undefined,
  amount_excluding_tax: undefined,
};

const FIELD_META: { key: keyof ManualInvoiceInput; label: string; span: number }[] = [
  { key: "invoice_name", label: "发票名称", span: 2 },
  { key: "invoice_number", label: "发票号码", span: 1 },
  { key: "invoice_code", label: "发票代码", span: 1 },
  { key: "issue_date", label: "开票日期", span: 1 },
  { key: "invoice_type", label: "发票类型", span: 1 },
  { key: "buyer_name", label: "购买方名称", span: 2 },
  { key: "buyer_tax_number", label: "购买方纳税人识别号", span: 1 },
  { key: "seller_name", label: "销售方名称", span: 2 },
  { key: "seller_tax_number", label: "销售方纳税人识别号", span: 1 },
  { key: "amount_excluding_tax", label: "不含税金额", span: 1 },
  { key: "tax_amount", label: "税额", span: 1 },
  { key: "total_amount", label: "价税合计", span: 1 },
];

export default function ManualCreateDialog({ open, onClose, onCreated }: Props) {
  const [cards, setCards] = useState<ManualInvoiceInput[]>([{ ...EMPTY_CARD }]);
  const [submitting, setSubmitting] = useState(false);

  if (!open) return null;

  function updateCard(index: number, key: keyof ManualInvoiceInput, value: string) {
    setCards((prev) =>
      prev.map((c, i) => (i === index ? { ...c, [key]: value || undefined } : c))
    );
  }

  function addCard() {
    setCards((prev) => [...prev, { ...EMPTY_CARD }]);
  }

  function removeCard(index: number) {
    setCards((prev) => {
      if (prev.length <= 1) return prev;
      return prev.filter((_, i) => i !== index);
    });
  }

  async function handleSubmit() {
    const valid = cards
      .map((c) => {
        const cleaned: ManualInvoiceInput = {};
        for (const [k, v] of Object.entries(c)) {
          if (v !== undefined && v !== null && v !== "") {
            (cleaned as Record<string, unknown>)[k] = v;
          }
        }
        return cleaned;
      })
      .filter((c) => Object.keys(c).length > 0);

    if (valid.length === 0) return;

    setSubmitting(true);
    try {
      await createManualInvoices(valid);
      onCreated();
      setCards([{ ...EMPTY_CARD }]);
      onClose();
    } catch {
      alert("创建失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 pt-[5vh] overflow-auto">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 rounded-t-xl">
          <h2 className="text-base font-semibold text-gray-900 dark:text-white">
            手动录入发票
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-6">
          {cards.map((card, idx) => (
            <div
              key={idx}
              className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  发票 {idx + 1}
                </span>
                <button
                  onClick={() => removeCard(idx)}
                  disabled={cards.length <= 1}
                  className="rounded p-1 text-gray-400 hover:text-red-500 disabled:opacity-30 transition-colors"
                  title="删除此发票"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {FIELD_META.map(({ key, label, span }) => (
                  <div key={key} className={span === 2 ? "col-span-2" : "col-span-1"}>
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-0.5">
                      {label}
                    </label>
                    <input
                      type={["total_amount", "tax_amount", "amount_excluding_tax"].includes(key) ? "number" : key === "issue_date" ? "date" : "text"}
                      value={card[key] ?? ""}
                      onChange={(e) => updateCard(idx, key, e.target.value)}
                      className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
                      placeholder={label}
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="sticky bottom-0 flex items-center justify-between px-5 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 rounded-b-xl">
          <button
            onClick={addCard}
            className="flex items-center gap-1 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Plus className="h-4 w-4" />
            添加发票
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="rounded-lg border border-gray-300 dark:border-gray-600 px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  创建中...
                </>
              ) : (
                "提交"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
