import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import LoginPage from "./pages/LoginPage";
import "./index.css";

function Root() {
  const [ready, setReady] = useState(false);
  // 在线版桌面壳（存在 js_api）每次启动先登录；离线版/浏览器无 js_api 直接进入
  const [isOnlineShell, setIsOnlineShell] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    async function init() {
      const pw = window.pywebview;
      if (pw?.api) {
        setIsOnlineShell(true);
      }
      setReady(true);
    }
    init();
  }, []);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
        <p className="text-sm text-gray-400">加载中...</p>
      </div>
    );
  }

  if (isOnlineShell && !loggedIn) {
    return <LoginPage onLoggedIn={() => setLoggedIn(true)} />;
  }

  return <App />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>
);
