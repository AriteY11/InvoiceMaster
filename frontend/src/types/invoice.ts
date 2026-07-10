export interface InvoiceItem {
  id: number;
  line_no: number;
  item_name: string | null;
  specification: string | null;
  unit: string | null;
  quantity: number | null;
  unit_price: number | null;
  amount: number | null;
  tax_rate: number | null;
  tax_amount: number | null;
  raw_row: string | null;
}

export interface InvoiceSummary {
  id: number;
  file_name: string;
  invoice_name: string | null;
  invoice_code: string | null;
  invoice_number: string | null;
  issue_date: string | null;
  invoice_type: string | null;
  buyer_name: string | null;
  seller_name: string | null;
  total_amount: number | null;
  tax_amount: number | null;
  parse_status: string;
  parse_confidence: number;
  created_at: string;
}

export interface InvoiceDetail extends InvoiceSummary {
  page_count: number;
  check_code: string | null;
  machine_number: string | null;
  currency: string | null;
  buyer_tax_number: string | null;
  buyer_address_phone: string | null;
  buyer_bank_account: string | null;
  seller_tax_number: string | null;
  seller_address_phone: string | null;
  seller_bank_account: string | null;
  amount_excluding_tax: number | null;
  total_amount_text: string | null;
  remarks: string | null;
  raw_text: string | null;
  parser_warnings: string[];
  items: InvoiceItem[];
}

export interface InvoiceListResponse {
  items: InvoiceSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface UploadInvoiceResult {
  file_name: string;
  invoice_id: number | null;
  status: string;
  message: string;
  duplicate: boolean;
}

export interface UploadInvoicesResponse {
  results: UploadInvoiceResult[];
}

export interface DeleteInvoiceResponse {
  message: string;
}

export interface StatsOverview {
  total_invoices: number;
  total_amount: number;
  total_tax_amount: number;
  latest_issue_date: string | null;
}

export interface TrendPoint {
  period: string;
  invoice_count: number;
  total_amount: number;
  tax_amount: number;
}

export interface StatsTrend {
  group_by: string;
  items: TrendPoint[];
}

export interface CategoryPoint {
  name: string;
  count: number;
  total_amount: number;
}

export interface StatsCategory {
  dimension: string;
  items: CategoryPoint[];
}

export interface FilterValues {
  sellers: string[];
  invoice_types: string[];
}

export interface InvoiceQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  seller_name?: string;
  invoice_type?: string;
  uploaded_from?: string;
  uploaded_to?: string;
}

export interface ManualInvoiceInput {
  invoice_name?: string;
  invoice_code?: string;
  invoice_number?: string;
  issue_date?: string;
  check_code?: string;
  machine_number?: string;
  invoice_type?: string;
  buyer_name?: string;
  buyer_tax_number?: string;
  buyer_address_phone?: string;
  buyer_bank_account?: string;
  seller_name?: string;
  seller_tax_number?: string;
  seller_address_phone?: string;
  seller_bank_account?: string;
  amount_excluding_tax?: number;
  tax_amount?: number;
  total_amount?: number;
  total_amount_text?: string;
  remarks?: string;
}
