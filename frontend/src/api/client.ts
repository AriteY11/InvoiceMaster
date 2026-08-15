let apiBase: string = import.meta.env.VITE_API_BASE ?? "/api";
let apiToken: string = "";

export function setApiBase(base: string) {
  if (base) {
    apiBase = base.replace(/\/+$/, "");
  }
}

export function getApiBase(): string {
  return apiBase;
}

export function setApiToken(token: string) {
  apiToken = token.trim();
}

export function getApiToken(): string {
  return apiToken;
}

function authHeaders(extra?: HeadersInit): HeadersInit {
  const headers: Record<string, string> = {};
  if (apiToken) {
    headers.Authorization = `Bearer ${apiToken}`;
  }
  if (extra) {
    return { ...headers, ...(extra as Record<string, string>) };
  }
  return headers;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase}${url}`, {
    headers: { "Content-Type": "application/json", ...authHeaders() },
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
    headers: authHeaders(),
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

  const res = await fetch(`${apiBase}/invoices/export?${qs}`, {
    headers: authHeaders(),
  });
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

/** react-pdf 加载 PDF 时携带的请求头（有 Token 时注入鉴权头）。 */
export function getInvoiceFileHeaders(): Record<string, string> {
  return apiToken ? { Authorization: `Bearer ${apiToken}` } : {};
}

/** 鉴权场景下用 fetch 携带 Token 打开 PDF（新窗口）。 */
export async function openInvoiceFile(id: number) {
  const res = await fetch(getInvoiceFileUrl(id), { headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "打开 PDF 失败");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
