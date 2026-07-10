import type { InvoiceItem } from "@/types/invoice";

interface ItemsTableProps {
  items: InvoiceItem[];
}

export default function ItemsTable({ items }: ItemsTableProps) {
  if (items.length === 0) {
    return (
      <div className="text-sm text-gray-400 dark:text-gray-600 py-4 text-center">
        未提取到行项目明细
      </div>
    );
  }

  const columns = [
    { key: "line_no", label: "序号", className: "w-12" },
    { key: "item_name", label: "商品/服务名称", className: "" },
    { key: "specification", label: "规格型号", className: "" },
    { key: "unit", label: "单位", className: "w-16" },
    { key: "quantity", label: "数量", className: "w-20 text-right" },
    { key: "unit_price", label: "单价", className: "w-24 text-right" },
    { key: "amount", label: "金额", className: "w-24 text-right" },
    { key: "tax_rate", label: "税率", className: "w-16 text-right" },
    { key: "tax_amount", label: "税额", className: "w-24 text-right" },
  ];

  const totalAmount = items.reduce((sum, item) => sum + (item.amount || 0), 0);
  const totalTax = items.reduce((sum, item) => sum + (item.tax_amount || 0), 0);

  function formatNumeric(value: unknown): string {
    if (value === null || value === undefined) return "-";
    const num = Number(value);
    if (isNaN(num)) return String(value);
    return num % 1 === 0
      ? num.toLocaleString("zh-CN")
      : num.toLocaleString("zh-CN", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 10,
        });
  }

  function formatValue(value: unknown): string {
    if (value === null || value === undefined) return "-";
    const num = Number(value);
    if (isNaN(num)) return String(value);
    if (num === 0) return "0";
    return num % 1 === 0
      ? num.toLocaleString("zh-CN")
      : num.toLocaleString("zh-CN", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-800">
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-3 py-2 text-left font-medium text-gray-600 dark:text-gray-400 ${col.className}`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {items.map((item, idx) => (
            <tr
              key={item.id || idx}
              className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`px-3 py-2 text-gray-700 dark:text-gray-300 ${col.className}`}
                >
                  {col.key === "unit_price"
                    ? formatNumeric((item as unknown as Record<string, unknown>)[col.key])
                    : formatValue((item as unknown as Record<string, unknown>)[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="bg-gray-50 dark:bg-gray-800 font-medium">
            <td colSpan={6} className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">
              合计
            </td>
            <td className="px-3 py-2 text-right text-gray-900 dark:text-white">
              {formatValue(totalAmount)}
            </td>
            <td className="px-3 py-2 text-right text-gray-500">-</td>
            <td className="px-3 py-2 text-right text-gray-900 dark:text-white">
              {formatValue(totalTax)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
