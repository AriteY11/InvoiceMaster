import { create } from "zustand";
import { persist } from "zustand/middleware";

export const COPY_FIELDS = [
  { key: "invoice_name", label: "发票名称" },
  { key: "invoice_code", label: "发票代码" },
  { key: "invoice_number", label: "发票号码" },
  { key: "issue_date", label: "开票日期" },
  { key: "check_code", label: "校验码" },
  { key: "machine_number", label: "机器编号" },
  { key: "invoice_type", label: "发票类型" },
  { key: "currency", label: "币种" },
  { key: "buyer_name", label: "购买方名称" },
  { key: "buyer_tax_number", label: "购买方纳税人识别号" },
  { key: "buyer_address_phone", label: "购买方地址电话" },
  { key: "buyer_bank_account", label: "购买方开户行及账号" },
  { key: "seller_name", label: "销售方名称" },
  { key: "seller_tax_number", label: "销售方纳税人识别号" },
  { key: "seller_address_phone", label: "销售方地址电话" },
  { key: "seller_bank_account", label: "销售方开户行及账号" },
  { key: "amount_excluding_tax", label: "不含税金额" },
  { key: "tax_amount", label: "税额" },
  { key: "total_amount", label: "价税合计" },
  { key: "total_amount_text", label: "价税合计(大写)" },
  { key: "remarks", label: "备注" },
  { key: "file_name", label: "文件名称" },
  { key: "page_count", label: "PDF页数" },
  { key: "parse_status", label: "解析状态" },
  { key: "parse_confidence", label: "解析置信度" },
  { key: "parser_warnings", label: "解析警告" },
  { key: "created_at", label: "上传时间" },
];

export type CopyStore = {
  selectedFields: string[];
  toggleField: (key: string) => void;
  selectAll: () => void;
  deselectAll: () => void;
};

const ALL_KEYS = COPY_FIELDS.map((f) => f.key);

export const useCopyStore = create<CopyStore>()(
  persist(
    (set) => ({
      selectedFields: ALL_KEYS,
      toggleField: (key) =>
        set((state) => {
          const exists = state.selectedFields.includes(key);
          return {
            selectedFields: exists
              ? state.selectedFields.filter((k) => k !== key)
              : [...state.selectedFields, key],
          };
        }),
      selectAll: () => set({ selectedFields: ALL_KEYS }),
      deselectAll: () => set({ selectedFields: [] }),
    }),
    { name: "copy-config" }
  )
);

export function formatFieldLabel(key: string): string {
  return COPY_FIELDS.find((f) => f.key === key)?.label || key;
}

export function formatFieldValue(key: string, detail: Record<string, unknown>): string {
  const v = detail[key];
  if (v === null || v === undefined) return "";
  if (key === "parse_confidence") return `${(Number(v) * 100).toFixed(0)}%`;
  if (key === "parser_warnings" && Array.isArray(v)) return v.join("; ");
  if (key === "created_at") return String(v).slice(0, 19).replace("T", " ");
  if (key === "issue_date") return String(v).slice(0, 10);
  if (key === "page_count") return String(v);
  if (["total_amount", "tax_amount", "amount_excluding_tax"].includes(key) && typeof v === "number") {
    return `CN¥${v.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return String(v);
}
