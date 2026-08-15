import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import LoginPage from "./pages/LoginPage";
import { isOnlineShell } from "./lib/runtime";
import "./index.css";

function Root() {
  const [ready, setReady] = useState(false);
  // 在线版桌面壳每次启动先登录；离线版/浏览器直接进入
  const [onlineShell, setOnlineShell] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    // pywebview 在页面加载完成后才注入 window.pywebview 并派发 pywebviewready 事件，
    // 必须等待该事件后再判断运行环境；纯浏览器环境用超时兜底。
    if (isOnlineShell()) {
      setOnlineShell(true);
      setReady(true);
      return;
    }
    const onReady = () => {
      setOnlineShell(isOnlineShell());
      setReady(true);
    };
    window.addEventListener("pywebviewready", onReady);
    const fallback = setTimeout(onReady, 1000);
    return () => {
      window.removeEventListener("pywebviewready", onReady);
      clearTimeout(fallback);
    };
  }, []);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
        <p className="text-sm text-gray-400">加载中...</p>
      </div>
    );
  }

  if (onlineShell && !loggedIn) {
    return <LoginPage onLoggedIn={() => setLoggedIn(true)} />;
  }

  return <App />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>
);
