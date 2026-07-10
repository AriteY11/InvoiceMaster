import { create } from "zustand";
import { persist } from "zustand/middleware";

export const EXPORT_HEADERS = [
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

export type ExportStore = {
  selectedColumns: string[];
  toggleColumn: (key: string) => void;
  selectAll: () => void;
  deselectAll: () => void;
};

const ALL_KEYS = EXPORT_HEADERS.map((h) => h.key);

export const useExportStore = create<ExportStore>()(
  persist(
    (set) => ({
      selectedColumns: ALL_KEYS,
      toggleColumn: (key) =>
        set((state) => {
          const exists = state.selectedColumns.includes(key);
          return {
            selectedColumns: exists
              ? state.selectedColumns.filter((k) => k !== key)
              : [...state.selectedColumns, key],
          };
        }),
      selectAll: () => set({ selectedColumns: ALL_KEYS }),
      deselectAll: () => set({ selectedColumns: [] }),
    }),
    { name: "export-config" }
  )
);
