import { useState } from "react";
import { Server, KeyRound } from "lucide-react";
import { setApiBase, setApiToken } from "@/api/client";

interface Props {
  onConfigured: () => void;
}

export default function ServerConfigPage({ onConfigured }: Props) {
  const [value, setValue] = useState("");
  const [token, setToken] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleSave() {
    const url = value.trim().replace(/\/+$/, "");
    if (!/^https?:\/\//.test(url)) {
      setError("请输入以 http:// 或 https:// 开头的服务器地址");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const pw = window.pywebview;
      if (pw?.api) {
        await pw.api.save_api_base(url);
        await pw.api.save_api_token(token.trim());
      }
      setApiBase(url);
      setApiToken(token);
      onConfigured();
    } catch (e) {
      setError(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 p-4">
      <div className="w-full max-w-md rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-8 shadow-sm">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-300">
            <Server className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              连接服务器
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              首次使用请填写后端服务器地址
            </p>
          </div>
        </div>

        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          服务器地址
        </label>
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSave();
          }}
          placeholder="http://192.168.1.100:8000"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <label className="mt-4 flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          <KeyRound className="h-3.5 w-3.5" />
          API Token（可选）
        </label>
        <input
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSave();
          }}
          placeholder="服务器开启鉴权时填写，与 INVOICEMASTER_API_TOKEN 一致"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}

        <button
          onClick={handleSave}
          disabled={saving}
          className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {saving ? "连接中..." : "连接"}
        </button>
      </div>
    </div>
  );
}
