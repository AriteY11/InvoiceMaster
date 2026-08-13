import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import ServerConfigPage from "./pages/ServerConfigPage";
import { setApiBase } from "./api/client";
import "./index.css";

function Root() {
  const [ready, setReady] = useState(false);
  const [needConfig, setNeedConfig] = useState(false);

  useEffect(() => {
    async function init() {
      const pw = window.pywebview;
      if (pw?.api) {
        try {
          const base = await pw.api.get_api_base();
          if (base) {
            setApiBase(base);
            setReady(true);
            return;
          }
          setNeedConfig(true);
          setReady(true);
          return;
        } catch {
          // js_api 调用失败（如浏览器环境），回退默认 API base
        }
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

  if (needConfig) {
    return <ServerConfigPage onConfigured={() => setNeedConfig(false)} />;
  }

  return <App />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>
);
