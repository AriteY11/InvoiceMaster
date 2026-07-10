import { useState, useRef, useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { FileUp, FileText, BarChart3, Sun, Moon, Settings } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";
import { cn } from "@/lib/utils";
import ExportConfigDialog from "@/components/ExportConfigDialog";
import TimezoneDialog from "@/components/TimezoneDialog";
import CopyConfigDialog from "@/components/CopyConfigDialog";

const navItems = [
  { to: "/", icon: FileUp, label: "上传发票" },
  { to: "/invoices", icon: FileText, label: "发票列表" },
  { to: "/stats", icon: BarChart3, label: "统计分析" },
];

export default function Layout() {
  const { theme, toggleTheme, isDark } = useTheme();
  const location = useLocation();
  const [showSettings, setShowSettings] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [timezoneDialogOpen, setTimezoneDialogOpen] = useState(false);
  const [copyDialogOpen, setCopyDialogOpen] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(e.target as Node)) {
        setShowSettings(false);
      }
    }
    if (showSettings) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showSettings]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="sticky top-0 z-50 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <img src="data:image/svg+xml,%3Csvg width='32' height='32' viewBox='0 0 32 32' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='32' height='32' rx='6' fill='%231E3A5F'/%3E%3Cpath d='M8 6C8 4.89543 8.89543 4 10 4H22C23.1046 4 24 4.89543 24 6V26C24 27.1046 23.1046 28 22 28H10C8.89543 28 8 27.1046 8 26V6Z' fill='white' opacity='.95'/%3E%3Cpath d='M12 10H20' stroke='%231E3A5F' stroke-width='1.5' stroke-linecap='round'/%3E%3Cpath d='M12 14H20' stroke='%231E3A5F' stroke-width='1.5' stroke-linecap='round'/%3E%3Cpath d='M12 18H17' stroke='%231E3A5F' stroke-width='1.5' stroke-linecap='round'/%3E%3Ccircle cx='22' cy='22' r='5' fill='%233B82F6'/%3E%3Cpath d='M20 22L21.5 23.5L24.5 20.5' stroke='white' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E" alt="InvoiceMaster" className="h-6 w-6" />
              <h1 className="text-lg font-bold text-gray-900 dark:text-white">
                InvoiceMaster
              </h1>
            </div>
            <nav className="flex items-center gap-1">
              {navItems.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                    location.pathname === to
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300"
                      : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-3 text-xs text-gray-400 dark:text-gray-500">
              <span>v1.6.0</span>
              <span className="w-px h-3 bg-gray-300 dark:bg-gray-700" />
              <span>著作人：ForWhat</span>
              <span className="w-px h-3 bg-gray-300 dark:bg-gray-700" />
              <span>联系：1256418086@qq.com</span>
            </div>
            <div className="relative" ref={settingsRef}>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
                title="配置"
              >
                <Settings className="h-4 w-4" />
              </button>
              {showSettings && (
                <div className="absolute right-0 top-full mt-1 z-20 w-36 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg">
                  <button
                    onClick={() => {
                      setShowSettings(false);
                      setExportDialogOpen(true);
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-t-md"
                  >
                    导出配置
                  </button>
                  <button
                    onClick={() => {
                      setShowSettings(false);
                      setCopyDialogOpen(true);
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                  >
                    复制配置
                  </button>
                  <button
                    onClick={() => {
                      setShowSettings(false);
                      setTimezoneDialogOpen(true);
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-b-md"
                  >
                    时间配置
                  </button>
                </div>
              )}
            </div>
            <button
              onClick={toggleTheme}
              className="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
              title={isDark ? "切换到亮色模式" : "切换到暗色模式"}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl p-4">
        <Outlet />
      </main>
      <ExportConfigDialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
      />
      <TimezoneDialog
        open={timezoneDialogOpen}
        onClose={() => setTimezoneDialogOpen(false)}
      />
      <CopyConfigDialog
        open={copyDialogOpen}
        onClose={() => setCopyDialogOpen(false)}
      />
    </div>
  );
}
