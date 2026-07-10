import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import { Receipt, DollarSign, TrendingUp, Calendar } from "lucide-react";
import { getStatsOverview, getStatsTrends, getStatsCategories } from "@/api/client";
import type { StatsOverview, StatsTrend, StatsCategory } from "@/types/invoice";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"];

const CARD_ICONS: Record<string, React.ReactNode> = {
  total_invoices: <Receipt className="h-5 w-5" />,
  total_amount: <DollarSign className="h-5 w-5" />,
  total_tax_amount: <TrendingUp className="h-5 w-5" />,
  latest_issue_date: <Calendar className="h-5 w-5" />,
};

const CARD_LABELS: Record<string, string> = {
  total_invoices: "总发票数",
  total_amount: "总金额（价税合计）",
  total_tax_amount: "总税额",
  latest_issue_date: "最近开票日期",
};

function formatAmount(value: unknown): string {
  const num = Number(value);
  if (isNaN(num) || num === 0) return "CN¥0.00";
  if (Math.abs(num) >= 10000) {
    return `CN¥${(num / 10000).toFixed(2)} 万`;
  }
  return `CN¥${num.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatCardValue(key: string, value: unknown): string {
  if (key === "latest_issue_date") {
    return String(value || "-").slice(0, 10);
  }
  return formatAmount(value);
}

function RenderPieLabel({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }: {
  cx: number; cy: number; midAngle?: number; innerRadius?: number;
  outerRadius?: number; percent?: number; name?: string;
}) {
  if (midAngle === undefined || outerRadius === undefined || innerRadius === undefined) return null;
  const RADIAN = Math.PI / 180;
  const radius = outerRadius + 30;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  if (!percent || percent < 0.03) return null;

  const displayName = name || "";
  const shortName = displayName.length > 6 ? displayName.slice(0, 6) + "…" : displayName;
  return (
    <text
      x={x}
      y={y}
      fill="#6b7280"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      fontSize={11}
    >
      {shortName} {(percent * 100).toFixed(0)}%
    </text>
  );
}

export default function StatsPage() {
  const [overview, setOverview] = useState<StatsOverview | null>(null);
  const [trends, setTrends] = useState<StatsTrend | null>(null);
  const [categoryType, setCategoryType] = useState<StatsCategory | null>(null);
  const [categorySeller, setCategorySeller] = useState<StatsCategory | null>(null);
  const [categoryService, setCategoryService] = useState<StatsCategory | null>(null);
  const [groupBy, setGroupBy] = useState<"month" | "day">("month");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getStatsOverview(),
      getStatsTrends(groupBy),
      getStatsCategories("invoice_type"),
      getStatsCategories("seller_name"),
      getStatsCategories("item_name"),
    ])
      .then(([ov, tr, ct, cs, ci]) => {
        setOverview(ov);
        setTrends(tr);
        setCategoryType(ct);
        setCategorySeller(cs);
        setCategoryService(ci);
      })
      .finally(() => setLoading(false));
  }, [groupBy]);

  function reloadTrends() {
    getStatsTrends(groupBy).then(setTrends);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-gray-400">加载统计数据...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">统计分析</h2>

      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(CARD_LABELS).map(([key, label]) => (
            <div
              key={key}
              className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4"
            >
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 mb-1">
                {CARD_ICONS[key]}
                <span className="text-xs font-medium">{label}</span>
              </div>
              <p className="text-lg font-bold text-gray-900 dark:text-white">
                {formatCardValue(key, (overview as unknown as Record<string, unknown>)[key])}
              </p>
            </div>
          ))}
        </div>
      )}

      {trends && trends.items.length > 0 && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              金额趋势
            </h3>
            <div className="flex items-center gap-1 rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5">
              <button
                onClick={() => { setGroupBy("month"); setTimeout(reloadTrends, 0); }}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  groupBy === "month"
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                }`}
              >
                按月
              </button>
              <button
                onClick={() => { setGroupBy("day"); setTimeout(reloadTrends, 0); }}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  groupBy === "day"
                    ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                    : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                }`}
              >
                按日
              </button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trends.items}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis
                dataKey="period"
                tick={{ fontSize: 12 }}
                className="text-gray-500 dark:text-gray-400"
              />
              <YAxis yAxisId="left" tick={{ fontSize: 12 }} className="text-gray-500 dark:text-gray-400" />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} className="text-gray-500 dark:text-gray-400" />
              <Tooltip />
              <Bar yAxisId="left" dataKey="invoice_count" name="发票数量" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="right" dataKey="total_amount" name="总金额" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400">
                  <th className="px-3 py-1.5 text-left">时间</th>
                  <th className="px-3 py-1.5 text-right">发票数量</th>
                  <th className="px-3 py-1.5 text-right">总金额</th>
                  <th className="px-3 py-1.5 text-right">税额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {trends.items.map((item, i) => (
                  <tr key={i} className="text-gray-700 dark:text-gray-300">
                    <td className="px-3 py-1.5">{item.period}</td>
                    <td className="px-3 py-1.5 text-right">{item.invoice_count}</td>
                    <td className="px-3 py-1.5 text-right">{formatAmount(item.total_amount)}</td>
                    <td className="px-3 py-1.5 text-right">{formatAmount(item.tax_amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {categoryType && categoryType.items.length > 0 && (
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
              发票类型分布
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={categoryType.items.map((c) => ({ name: c.name, value: c.count }))}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  dataKey="value"
                  label={RenderPieLabel}
                  labelLine={{ stroke: "#9ca3af", strokeWidth: 1 }}
                >
                  {categoryType.items.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => [`${value} 张`, "发票数量"]} />
              </PieChart>
            </ResponsiveContainer>
            <table className="w-full text-xs mt-3">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400">
                  <th className="px-3 py-1.5 text-left">类型</th>
                  <th className="px-3 py-1.5 text-right">数量</th>
                  <th className="px-3 py-1.5 text-right">金额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {categoryType.items.map((c, i) => (
                  <tr key={i} className="text-gray-700 dark:text-gray-300">
                    <td className="px-3 py-1.5">{c.name}</td>
                    <td className="px-3 py-1.5 text-right">{c.count}</td>
                    <td className="px-3 py-1.5 text-right">{formatAmount(c.total_amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {categorySeller && categorySeller.items.length > 0 && (
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
              销售方 Top {Math.min(categorySeller.items.length, 10)}
            </h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={categorySeller.items.slice(0, 10).reverse()}
                layout="vertical"
                margin={{ left: 80 }}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
                <XAxis type="number" tick={{ fontSize: 11 }} className="text-gray-500" />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={80} className="text-gray-500" />
                <Tooltip formatter={(value: number) => [`${value} 张`, "发票数量"]} />
                <Bar dataKey="count" name="发票数量" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <table className="w-full text-xs mt-3">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400">
                  <th className="px-3 py-1.5 text-left">销售方</th>
                  <th className="px-3 py-1.5 text-right">数量</th>
                  <th className="px-3 py-1.5 text-right">金额</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {categorySeller.items.map((c, i) => (
                  <tr key={i} className="text-gray-700 dark:text-gray-300">
                    <td className="px-3 py-1.5 max-w-[200px] truncate">{c.name}</td>
                    <td className="px-3 py-1.5 text-right">{c.count}</td>
                    <td className="px-3 py-1.5 text-right">{formatAmount(c.total_amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {categoryService && categoryService.items.length > 0 && (
        <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">
            服务类型统计
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={categoryService.items}
              margin={{ bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11 }}
                angle={-20}
                textAnchor="end"
                height={60}
                className="text-gray-500 dark:text-gray-400"
              />
              <YAxis yAxisId="left" tick={{ fontSize: 11 }} className="text-gray-500 dark:text-gray-400" />
              <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} className="text-gray-500 dark:text-gray-400" />
              <Tooltip formatter={(value: number, name: string) => [name === "cnt" ? `${value} 张` : formatAmount(value), name === "cnt" ? "发票数量" : "金额"]} />
              <Bar yAxisId="left" dataKey="count" name="发票数量" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="right" dataKey="total_amount" name="金额" fill="#10b981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <table className="w-full text-xs mt-3">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400">
                <th className="px-3 py-1.5 text-left">服务类型</th>
                <th className="px-3 py-1.5 text-right">数量</th>
                <th className="px-3 py-1.5 text-right">金额</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {categoryService.items.map((c, i) => (
                <tr key={i} className="text-gray-700 dark:text-gray-300">
                  <td className="px-3 py-1.5">{c.name}</td>
                  <td className="px-3 py-1.5 text-right">{c.count}</td>
                  <td className="px-3 py-1.5 text-right">{formatAmount(c.total_amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
