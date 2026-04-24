let amapScriptPromise = null;

export function loadAmap({ apiKey, securityJsCode, timeoutMs = 8000 }) {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("loadAmap: window unavailable (SSR?)"));
  }
  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }
  if (amapScriptPromise) {
    return amapScriptPromise;
  }
  if (!apiKey) {
    return Promise.reject(new Error("loadAmap: missing apiKey"));
  }
  if (securityJsCode) {
    window._AMapSecurityConfig = { securityJsCode };
  }
  amapScriptPromise = new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      reject(new Error("AMap script timeout"));
    }, timeoutMs);
    const script = document.createElement("script");
    script.async = true;
    script.defer = true;
    script.dataset.amapLoader = "user-platform";
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(apiKey)}&plugin=AMap.Scale,AMap.ToolBar`;
    script.onload = () => {
      window.clearTimeout(timeoutId);
      if (window.AMap) {
        resolve(window.AMap);
      } else {
        reject(new Error("AMap unavailable after script load"));
      }
    };
    script.onerror = () => {
      window.clearTimeout(timeoutId);
      reject(new Error("AMap script failed"));
    };
    document.head.appendChild(script);
  });
  return amapScriptPromise;
}
