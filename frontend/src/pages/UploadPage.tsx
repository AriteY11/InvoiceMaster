import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";
import { uploadInvoices } from "@/api/client";
import type { UploadInvoiceResult } from "@/types/invoice";
import ManualCreateDialog from "@/components/ManualCreateDialog";

export default function UploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadInvoiceResult[] | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [manualOpen, setManualOpen] = useState(false);

  const handleFiles = useCallback((files: FileList | File[]) => {
    const pdfFiles = Array.from(files).filter(
      (f) => f.name.toLowerCase().endsWith(".pdf")
    );
    setSelectedFiles(pdfFiles);
    setResults(null);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    setUploading(true);
    try {
      const data = await uploadInvoices(selectedFiles);
      setResults(data.results);
    } catch (err) {
      setResults([
        {
          file_name: "",
          invoice_id: null,
          status: "error",
          message: err instanceof Error ? err.message : "上传失败",
          duplicate: false,
        },
      ]);
    } finally {
      setUploading(false);
    }
  };

  const successCount = results?.filter((r) => r.status === "success").length || 0;
  const errorCount = results?.filter((r) => r.status === "error").length || 0;
  const duplicateCount = results?.filter((r) => r.duplicate).length || 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          上传发票
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          支持 PDF 格式的电子发票，可一次上传多个文件
        </p>
        <div className="mt-2 flex items-center gap-2">
          <button
            onClick={() => setManualOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-950/30 px-3 py-1.5 text-sm font-medium text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-950/50 transition-colors"
          >
            <Pencil className="h-4 w-4" />
            人工录入
          </button>
        </div>
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-colors cursor-pointer",
          dragOver
            ? "border-blue-500 bg-blue-50 dark:bg-blue-950/30"
            : "border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900",
          uploading && "pointer-events-none opacity-50"
        )}
      >
        <Upload className={cn("h-12 w-12 mb-4", dragOver ? "text-blue-500" : "text-gray-400")} />
        <p className="text-sm text-gray-600 dark:text-gray-400">
          拖拽 PDF 文件到此处，或点击选择文件
        </p>
        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">
          仅支持 PDF 格式，单个文件不超过 20MB
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {selectedFiles.length > 0 && !results && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            已选择 {selectedFiles.length} 个文件
          </h3>
          <ul className="space-y-1">
            {selectedFiles.map((f, i) => (
              <li key={i} className="text-sm text-gray-500 dark:text-gray-400 flex items-center gap-2">
                <FileText className="h-3.5 w-3.5" />
                {f.name}
                <span className="text-xs">({(f.size / 1024).toFixed(1)} KB)</span>
              </li>
            ))}
          </ul>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {uploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                正在解析...
              </>
            ) : (
              "开始上传并解析"
            )}
          </button>
        </div>
      )}

      {results && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <div className="flex items-center gap-4 mb-3">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              解析结果
            </span>
            <span className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle2 className="h-3 w-3" /> 成功 {successCount}
            </span>
            {duplicateCount > 0 && (
              <span className="flex items-center gap-1 text-xs text-yellow-600">
                <AlertCircle className="h-3 w-3" /> 重复 {duplicateCount}
              </span>
            )}
            {errorCount > 0 && (
              <span className="flex items-center gap-1 text-xs text-red-600">
                <AlertCircle className="h-3 w-3" /> 失败 {errorCount}
              </span>
            )}
          </div>
          <ul className="space-y-1.5">
            {results.map((r, i) => (
              <li
                key={i}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm",
                  r.status === "success" && "bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-300",
                  r.status === "error" && "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300",
                  r.duplicate && "bg-yellow-50 dark:bg-yellow-950/30 text-yellow-700 dark:text-yellow-300"
                )}
              >
                {r.status === "success" && <CheckCircle2 className="h-4 w-4 shrink-0" />}
                {r.status === "error" && <AlertCircle className="h-4 w-4 shrink-0" />}
                {r.duplicate && <AlertCircle className="h-4 w-4 shrink-0" />}
                <span>{r.file_name}</span>
                <span className="text-xs opacity-75">- {r.message}</span>
              </li>
            ))}
          </ul>
          {successCount > 0 && (
            <button
              onClick={() => navigate("/invoices")}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              查看发票列表
            </button>
          )}
        </div>
      )}
      <ManualCreateDialog
        open={manualOpen}
        onClose={() => setManualOpen(false)}
        onCreated={() => {
          setResults([
            { file_name: "手动录入", invoice_id: null, status: "success", message: "创建完成", duplicate: false },
          ]);
        }}
      />
    </div>
  );
}
