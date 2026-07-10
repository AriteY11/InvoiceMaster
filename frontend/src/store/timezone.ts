import { create } from "zustand";
import { persist } from "zustand/middleware";

export const TIMEZONE_OPTIONS = [
  { value: "Asia/Shanghai", label: "东八区 (UTC+8) 北京/上海" },
  { value: "Asia/Tokyo", label: "东九区 (UTC+9) 东京" },
  { value: "Asia/Seoul", label: "东九区 (UTC+9) 首尔" },
  { value: "Asia/Singapore", label: "东八区 (UTC+8) 新加坡" },
  { value: "Asia/Hong_Kong", label: "东八区 (UTC+8) 香港" },
  { value: "Asia/Kolkata", label: "东五区半 (UTC+5:30) 印度" },
  { value: "Asia/Dubai", label: "东四区 (UTC+4) 迪拜" },
  { value: "Europe/Moscow", label: "东三区 (UTC+3) 莫斯科" },
  { value: "Europe/Berlin", label: "东一区 (UTC+1) 柏林" },
  { value: "Europe/London", label: "零时区 (UTC+0) 伦敦" },
  { value: "America/New_York", label: "西五区 (UTC-5) 纽约" },
  { value: "America/Chicago", label: "西六区 (UTC-6) 芝加哥" },
  { value: "America/Los_Angeles", label: "西八区 (UTC-8) 洛杉矶" },
  { value: "Pacific/Auckland", label: "东十二区 (UTC+12) 奥克兰" },
];

export type TimezoneStore = {
  timezone: string;
  setTimezone: (tz: string) => void;
};

export const useTimezoneStore = create<TimezoneStore>()(
  persist(
    (set) => ({
      timezone: "Asia/Shanghai",
      setTimezone: (tz) => set({ timezone: tz }),
    }),
    { name: "timezone-config" }
  )
);

export function formatTzDate(utcStr: string | null, timezone: string): string {
  if (!utcStr) return "-";
  const d = new Date(utcStr.replace(" ", "T") + "Z");
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}
