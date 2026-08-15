// pywebview js_api 类型声明（仅在线版桌面壳存在 window.pywebview）

interface PywebviewApi {
  get_api_base(): Promise<string>;
  save_api_base(apiBase: string): Promise<void>;
  get_api_token(): Promise<string>;
  save_api_token(apiToken: string): Promise<void>;
}

interface Window {
  pywebview?: {
    api: PywebviewApi;
  };
}
