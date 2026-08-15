/**
 * 运行时环境检测。
 *
 * pywebview 在页面加载完成后才注入 window.pywebview（并派发 pywebviewready 事件），
 * 因此检测必须在事件之后进行，不能在模块加载时缓存结果。
 */

export function isOnlineShell(): boolean {
  const pw = window.pywebview;
  if (!pw?.api) return false;
  // 在线版桌面壳暴露 get_api_base 等 js_api 方法；离线壳无 js_api（api 为空对象）
  return typeof (pw.api as unknown as Record<string, unknown>).get_api_base === "function";
}
