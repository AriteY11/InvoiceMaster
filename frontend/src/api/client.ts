const API_BASE = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
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
  const res = await fetch(`${API_BASE}/invoices/upload`, {
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

export function exportInvoices(params: InvoiceQueryParams = {}, format: "xlsx" | "csv" = "xlsx", columns?: string[]) {
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
  window.open(`${API_BASE}/invoices/export?${qs}`, "_blank");
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
