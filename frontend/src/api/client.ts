let apiBase: string = import.meta.env.VITE_API_BASE ?? "/api";

export function setApiBase(base: string) {
  if (base) {
    apiBase = base.replace(/\/+$/, "");
  }
}

export function getApiBase(): string {
  return apiBase;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `请求失败: ${res.status}`);
  }
  return res.json();
}

export async function uploadInvoices(files: FileList | File[]) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append("files", files[i]);
  }
  const res = await fetch(`${apiBase}/invoices/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "上传失败");
  }
  return res.json();
}

import type {
  InvoiceDetail,
  InvoiceListResponse,
  StatsOverview,
  StatsTrend,
  StatsCategory,
  InvoiceQueryParams,
  FilterValues,
  ManualInvoiceInput,
  UploadInvoicesResponse,
} from "@/types/invoice";

export function getInvoices(params: InvoiceQueryParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const qs = searchParams.toString();
  return request<InvoiceListResponse>(`/invoices${qs ? `?${qs}` : ""}`);
}

export function getFilterValues() {
  return request<FilterValues>("/invoices/filters");
}

export async function exportInvoices(params: InvoiceQueryParams = {}, format: "xlsx" | "csv" = "xlsx", columns?: string[]) {
  const searchParams = new URLSearchParams();
  searchParams.set("format", format);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  if (columns && columns.length > 0) {
    searchParams.set("columns", columns.join(","));
  }
  const qs = searchParams.toString();

  const res = await fetch(`${apiBase}/invoices/export?${qs}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `导出失败: ${res.status}`);
  }

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match =
    disposition.match(/filename\*=UTF-8''([^;]+)/) ||
    disposition.match(/filename="?([^";]+)"?/);
  const filename = match
    ? decodeURIComponent(match[1])
    : `invoices_${Date.now()}.${format}`;

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function getInvoiceDetail(id: number) {
  return request<InvoiceDetail>(`/invoices/${id}`);
}

export function deleteInvoice(id: number) {
  return request<{ message: string }>(`/invoices/${id}`, { method: "DELETE" });
}

export function createManualInvoices(invoices: ManualInvoiceInput[]) {
  return request<UploadInvoicesResponse>("/invoices/manual", {
    method: "POST",
    body: JSON.stringify(invoices),
  });
}

export function getStatsOverview() {
  return request<StatsOverview>("/stats/overview");
}

export function getStatsTrends(groupBy: "month" | "day" = "month") {
  return request<StatsTrend>(`/stats/trends?group_by=${groupBy}`);
}

export function getStatsCategories(
  dimension: "invoice_type" | "seller_name" | "item_name" = "invoice_type"
) {
  return request<StatsCategory>(`/stats/categories?dimension=${dimension}`);
}

export function getInvoiceFileUrl(id: number) {
  return `${apiBase}/invoices/${id}/file`;
}
