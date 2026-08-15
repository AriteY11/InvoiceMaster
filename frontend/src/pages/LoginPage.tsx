import { useEffect, useState } from "react";
import { KeyRound, Server, User } from "lucide-react";
import { login, setApiBase, setApiToken } from "@/api/client";

interface Props {
  onLoggedIn: () => void;
}

export default function LoginPage({ onLoggedIn }: Props) {
  const [server, setServer] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // 预填上次保存的服务器地址
    const pw = window.pywebview;
    if (pw?.api) {
      pw.api
        .get_api_base()
        .then((base) => {
          if (base) setServer(base);
        })
        .catch(() => {});
    }
  }, []);

  async function handleLogin() {
    const url = server.trim().replace(/\/+$/, "");
    if (!/^https?:\/\//.test(url)) {
      setError("请输入以 http:// 或 https:// 开头的服务器地址");
      return;
    }
    if (!username.trim()) {
      setError("请输入账号");
      return;
    }
    if (!password) {
      setError("请输入密码");
      return;
    }
    setSaving(true);
    setError("");
    try {
      setApiBase(url);
      const result = await login(username.trim(), password);
      setApiToken(result.token);
      const pw = window.pywebview;
      if (pw?.api) {
        await pw.api.save_api_base(url);
        await pw.api.save_api_token(result.token);
      }
      onLoggedIn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "登录失败，请检查服务器地址与账号密码");
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
              登录 InvoiceMaster
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              请填写服务器地址与账号密码
            </p>
          </div>
        </div>

        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          服务器地址
        </label>
        <input
          type="text"
          value={server}
          onChange={(e) => setServer(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleLogin();
          }}
          placeholder="http://192.168.1.100:8000"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <label className="mt-4 flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          <User className="h-3.5 w-3.5" />
          账号
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleLogin();
          }}
          placeholder="请输入账号名称"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <label className="mt-4 flex items-center gap-1.5 text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          <KeyRound className="h-3.5 w-3.5" />
          密码
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleLogin();
          }}
          placeholder="请输入密码"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}

        <button
          onClick={handleLogin}
          disabled={saving}
          className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {saving ? "登录中..." : "登录"}
        </button>

        <p className="mt-3 text-xs text-gray-400 dark:text-gray-500">
          账号由服务器管理员通过账号管理脚本创建，登录后即可上传与查看发票。
        </p>
      </div>
    </div>
  );
}
