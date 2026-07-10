import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, AlertTriangle, ChevronDown, ChevronUp, FileText, ExternalLink } from "lucide-react";
import { getInvoiceDetail } from "@/api/client";
import type { InvoiceDetail } from "@/types/invoice";
import FieldCard from "@/components/FieldCard";
import ItemsTable from "@/components/ItemsTable";
import { cn } from "@/lib/utils";

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRaw, setShowRaw] = useState(false);
  const [showPdf, setShowPdf] = useState(true);
  const [pdfError, setPdfError] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getInvoiceDetail(Number(id))
      .then(setInvoice)
      .catch(() => setInvoice(null))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    setPdfError(false);
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-400">加载中...</p>
      </div>
    );
  }

  if (!invoice) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-4">
        <p className="text-gray-400">发票不存在或加载失败</p>
        <button
          onClick={() => navigate("/invoices")}
          className="text-sm text-blue-600 hover:underline"
        >
          返回列表
        </button>
      </div>
    );
  }

  function formatDate(dateStr: string | null) {
    if (!dateStr) return null;
    return dateStr.slice(0, 10);
  }

  function formatAmount(amount: number | null) {
    if (amount === null || amount === undefined) return null;
    return `CN¥${amount.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate("/invoices")}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <ArrowLeft className="h-4 w-4" /> 返回列表
        </button>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">发票详情</h2>
        <span
          className={cn(
            "rounded-full px-2.5 py-0.5 text-xs font-medium",
            invoice.parse_confidence >= 0.8
              ? "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300"
              : invoice.parse_confidence >= 0.5
              ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-950 dark:text-yellow-300"
              : "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300"
          )}
        >
          置信度 {(invoice.parse_confidence * 100).toFixed(0)}%
        </span>
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
        <div className="flex items-center">
          <button
            onClick={() => setShowPdf(!showPdf)}
            className="flex items-center gap-2 px-5 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 flex-1 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
          >
            <FileText className="h-4 w-4" />
            原始发票 PDF
            {showPdf ? <ChevronUp className="h-4 w-4 ml-auto" /> : <ChevronDown className="h-4 w-4 ml-auto" />}
          </button>
          {id && (
            <a
              href={`/api/invoices/${id}/file`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 px-4 py-3 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors border-l border-gray-200 dark:border-gray-700"
              title="在新窗口中打开 PDF"
            >
              <ExternalLink className="h-4 w-4" />
              <span className="hidden sm:inline">新窗口打开</span>
            </a>
          )}
        </div>
        {showPdf && (
          <div className="border-t border-gray-200 dark:border-gray-700">
            {!pdfError ? (
              <iframe
                src={`/api/invoices/${id}/file`}
                className="w-full h-[680px]"
                title="发票PDF预览"
                onError={() => setPdfError(true)}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-64 gap-3 text-gray-500 dark:text-gray-400">
                <p>浏览器不支持内嵌 PDF 预览</p>
                {id && (
                  <a
                    href={`/api/invoices/${id}/file`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    <ExternalLink className="h-4 w-4" />
                    在新窗口中打开 PDF
                  </a>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          发票基础信息
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <FieldCard label="发票名称" value={invoice.invoice_name} />
          <FieldCard label="发票号码" value={invoice.invoice_number} />
          <FieldCard label="开票日期" value={formatDate(invoice.issue_date)} />
          <FieldCard label="校验码" value={invoice.check_code} />
          <FieldCard label="机器编号" value={invoice.machine_number} />
          <FieldCard label="发票类型" value={invoice.invoice_type} />
          <FieldCard label="币种" value={invoice.currency} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            购买方信息
          </h3>
          <div className="space-y-3">
            <FieldCard label="名称" value={invoice.buyer_name} />
            <FieldCard label="纳税人识别号" value={invoice.buyer_tax_number} />
            <FieldCard label="地址、电话" value={invoice.buyer_address_phone} />
            <FieldCard label="开户行及账号" value={invoice.buyer_bank_account} />
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            销售方信息
          </h3>
          <div className="space-y-3">
            <FieldCard label="名称" value={invoice.seller_name} />
            <FieldCard label="纳税人识别号" value={invoice.seller_tax_number} />
            <FieldCard label="地址、电话" value={invoice.seller_address_phone} />
            <FieldCard label="开户行及账号" value={invoice.seller_bank_account} />
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          金额信息
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <FieldCard label="不含税金额" value={formatAmount(invoice.amount_excluding_tax)} />
          <FieldCard label="税额" value={formatAmount(invoice.tax_amount)} />
          <FieldCard
            label="价税合计"
            value={formatAmount(invoice.total_amount)}
            className="font-semibold"
          />
          <FieldCard label="大写金额" value={invoice.total_amount_text} />
          <FieldCard label="备注" value={invoice.remarks} />
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          行项目明细 ({invoice.items.length} 项)
        </h3>
        <ItemsTable items={invoice.items} />
      </div>

      {invoice.parser_warnings.length > 0 && (
        <div className="rounded-lg border border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950/30 p-5">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-yellow-700 dark:text-yellow-300 mb-2">
            <AlertTriangle className="h-4 w-4" />
            解析告警 ({invoice.parser_warnings.length})
          </h3>
          <ul className="list-disc list-inside space-y-0.5">
            {invoice.parser_warnings.map((w, i) => (
              <li key={i} className="text-sm text-yellow-600 dark:text-yellow-400">
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
        <button
          onClick={() => setShowRaw(!showRaw)}
          className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 w-full text-left"
        >
          原始提取文本
          {showRaw ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
        {showRaw && (
          <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-gray-50 dark:bg-gray-800 p-3 text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
            {invoice.raw_text || "无原始文本"}
          </pre>
        )}
      </div>
    </div>
  );
}
