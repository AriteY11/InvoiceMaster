import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Trash2, ChevronLeft, ChevronRight, Filter, X, Download, ChevronDown, Copy } from "lucide-react";
import { getInvoices, deleteInvoice, getFilterValues, exportInvoices, getInvoiceDetail } from "@/api/client";
import { useExportStore } from "@/store/export";
import { useTimezoneStore, formatTzDate } from "@/store/timezone";
import { useCopyStore, formatFieldLabel, formatFieldValue } from "@/store/copy";
import type { InvoiceSummary, FilterValues } from "@/types/invoice";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 20;

export default function InvoiceListPage() {
  const navigate = useNavigate();
  const [data, setData] = useState<{ items: InvoiceSummary[]; total: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [keyword, setKeyword] = useState("");
  const [searchText, setSearchText] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [showExport, setShowExport] = useState(false);

  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");
  const [filterAmountMin, setFilterAmountMin] = useState("");
  const [filterAmountMax, setFilterAmountMax] = useState("");
  const [filterSeller, setFilterSeller] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterUploadFrom, setFilterUploadFrom] = useState("");
  const [filterUploadTo, setFilterUploadTo] = useState("");

  const [filterOptions, setFilterOptions] = useState<FilterValues>({ sellers: [], invoice_types: [] });
  const timezone = useTimezoneStore((s) => s.timezone);

  useEffect(() => {
    getFilterValues().then(setFilterOptions).catch(() => {});
  }, []);

  const hasFilters =
    filterDateFrom || filterDateTo || filterAmountMin || filterAmountMax || filterSeller || filterType ||
    filterUploadFrom || filterUploadTo;

  function buildQueryParams() {
    const params: Record<string, string | number | undefined> = {
      page,
      page_size: PAGE_SIZE,
      keyword: keyword || undefined,
    };
    if (filterDateFrom) params.date_from = filterDateFrom;
    if (filterDateTo) params.date_to = filterDateTo;
    if (filterAmountMin) params.amount_min = Number(filterAmountMin);
    if (filterAmountMax) params.amount_max = Number(filterAmountMax);
    if (filterSeller) params.seller_name = filterSeller;
    if (filterType) params.invoice_type = filterType;
    if (filterUploadFrom) params.uploaded_from = filterUploadFrom;
    if (filterUploadTo) params.uploaded_to = filterUploadTo;
    return params;
  }

  function doFetch() {
    let cancelled = false;
    setLoading(true);
    getInvoices(buildQueryParams())
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setData(null);
        setLoading(false);
      });
    return () => { cancelled = true; };
  }

  useEffect(() => {
    const cancel = doFetch();
    return cancel;
  }, [page, keyword, filterDateFrom, filterDateTo, filterAmountMin, filterAmountMax, filterSeller, filterType, filterUploadFrom, filterUploadTo]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  function handleSearch() {
    setKeyword(searchText);
    setPage(1);
  }

  function handleApplyFilters() {
    setPage(1);
  }

  function handleExport(format: "xlsx" | "csv") {
    const filterParams = buildQueryParams();
    delete filterParams.page;
    delete filterParams.page_size;
    exportInvoices(
      filterParams as Record<string, string | number | undefined>,
      format,
      useExportStore.getState().selectedColumns,
    );
    setShowExport(false);
  }

  function handleClearFilters() {
    setFilterDateFrom("");
    setFilterDateTo("");
    setFilterAmountMin("");
    setFilterAmountMax("");
    setFilterSeller("");
    setFilterType("");
    setFilterUploadFrom("");
    setFilterUploadTo("");
    setPage(1);
  }

  async function handleDelete(id: number, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("确定要删除这张发票吗？")) return;
    try {
      await deleteInvoice(id);
      setData((prev) => {
        if (!prev) return prev;
        const newItems = prev.items.filter((inv) => inv.id !== id);
        if (newItems.length === 0 && page > 1) {
          setPage(page - 1);
        }
        return { items: newItems, total: prev.total - 1 };
      });
    } catch {
      alert("删除失败");
    }
  }

  async function handleCopy(id: number, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      const detail = await getInvoiceDetail(id);
      const fields = useCopyStore.getState().selectedFields;
      if (fields.length === 0) {
        alert("没有选中任何字段，请在配置中设置复制字段");
        return;
      }
      const lines = fields
        .map((key) => `${formatFieldLabel(key)}: ${formatFieldValue(key, detail as unknown as Record<string, unknown>)}`)
        .join("\n");
      await navigator.clipboard.writeText(lines);
      alert("已复制到剪贴板");
    } catch {
      alert("复制失败");
    }
  }

  function formatDateOnly(dateStr: string | null) {
    if (!dateStr) return "-";
    return dateStr.slice(0, 10);
  }

  function formatUploadTime(dateStr: string | null) {
    if (!dateStr) return "-";
    return formatTzDate(dateStr, timezone);
  }

  function formatAmount(amount: number | null) {
    if (amount === null || amount === undefined) return "-";
    return `¥${amount.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">发票列表</h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          共 {data?.total || 0} 张
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5">
          <Search className="h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索发票代码/号码/名称..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="bg-transparent text-sm outline-none w-64 text-gray-900 dark:text-white placeholder-gray-400"
          />
        </div>
        <button
          onClick={handleSearch}
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          搜索
        </button>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            "flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
            hasFilters
              ? "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
              : "border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
          )}
        >
          <Filter className="h-4 w-4" />
          筛选
          {hasFilters && (
            <span className="ml-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-blue-600 px-1 text-[10px] font-bold text-white">
              !
            </span>
          )}
        </button>
        <div className="relative">
          <button
            onClick={() => setShowExport(!showExport)}
            className="flex items-center gap-1 rounded-lg border border-gray-300 dark:border-gray-600 px-3 py-1.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Download className="h-4 w-4" />
            导出
            <ChevronDown className={cn("h-3 w-3 transition-transform", showExport && "rotate-180")} />
          </button>
          {showExport && (
            <div className="absolute left-0 top-full mt-1 z-20 w-32 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg">
              <button
                onClick={() => handleExport("xlsx")}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-t-md"
              >
                Excel (.xlsx)
              </button>
              <button
                onClick={() => handleExport("csv")}
                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-b-md"
              >
                CSV (.csv)
              </button>
            </div>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">开票日期从</label>
              <input
                type="date"
                value={filterDateFrom}
                onChange={(e) => setFilterDateFrom(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">开票日期至</label>
              <input
                type="date"
                value={filterDateTo}
                onChange={(e) => setFilterDateTo(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">金额≥</label>
              <input
                type="number"
                placeholder="最低金额"
                value={filterAmountMin}
                onChange={(e) => setFilterAmountMin(e.target.value)}
                min={0}
                step={0.01}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">金额≤</label>
              <input
                type="number"
                placeholder="最高金额"
                value={filterAmountMax}
                onChange={(e) => setFilterAmountMax(e.target.value)}
                min={0}
                step={0.01}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">销售方</label>
              <select
                value={filterSeller}
                onChange={(e) => setFilterSeller(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              >
                <option value="">全部</option>
                {filterOptions.sellers.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">发票类型</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              >
                <option value="">全部</option>
                {filterOptions.invoice_types.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">上传时间从</label>
              <input
                type="date"
                value={filterUploadFrom}
                onChange={(e) => setFilterUploadFrom(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">上传时间至</label>
              <input
                type="date"
                value={filterUploadTo}
                onChange={(e) => setFilterUploadTo(e.target.value)}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-2.5 py-1.5 text-sm text-gray-900 dark:text-white outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex items-center gap-2 mt-3">
            <button
              onClick={handleApplyFilters}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              应用筛选
            </button>
            {hasFilters && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <X className="h-3.5 w-3.5" />
                清除筛选
              </button>
            )}
          </div>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">发票号码</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">开票日期</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">类型</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">购买方</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">销售方</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-400">价税合计</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600 dark:text-gray-400">置信度</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-400">上传时间</th>
              <th className="px-4 py-3 text-center font-medium text-gray-600 dark:text-gray-400">操作</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {loading ? (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center text-gray-400">
                  加载中...
                </td>
              </tr>
            ) : data && data.items.length > 0 ? (
              data.items.map((inv) => (
                <tr
                  key={inv.id}
                  onClick={() => navigate(`/invoices/${inv.id}`)}
                  className="hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300 font-mono text-xs">
                    {inv.invoice_number || "-"}
                  </td>
                  <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300">
                    {formatDateOnly(inv.issue_date)}
                  </td>
                  <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300 max-w-[120px] truncate">
                    {inv.invoice_type || "-"}
                  </td>
                  <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300 max-w-[140px] truncate">
                    {inv.buyer_name || "-"}
                  </td>
                  <td className="px-4 py-2.5 text-gray-700 dark:text-gray-300 max-w-[140px] truncate">
                    {inv.seller_name || "-"}
                  </td>
                  <td className="px-4 py-2.5 text-right text-gray-900 dark:text-white font-medium">
                    {formatAmount(inv.total_amount)}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <span
                      className={cn(
                        "text-xs font-medium",
                        inv.parse_confidence >= 0.8
                          ? "text-green-600"
                          : inv.parse_confidence >= 0.5
                          ? "text-yellow-600"
                          : "text-red-600"
                      )}
                    >
                      {(inv.parse_confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 dark:text-gray-400 text-xs">
                    {formatUploadTime(inv.created_at)}
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        onClick={(e) => handleCopy(inv.id, e)}
                        className="rounded p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors"
                        title="复制"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => handleDelete(inv.id, e)}
                        className="rounded p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center text-gray-400">
                  暂无发票数据，请先上传发票
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-md border border-gray-300 dark:border-gray-600 p-1.5 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {page} / {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-md border border-gray-300 dark:border-gray-600 p-1.5 disabled:opacity-30 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
