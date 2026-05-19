import { PRIMARY_MODE_ID, getMode, normalizeModeId } from "./modes.js?v=20260519-no-notes";

export function initShell({ root, store }) {
  const chipsContainer = root.querySelector('[data-component="mode-chips"]');
  const runtimeTag = root.querySelector('[data-component="runtime-tag"]');
  const statusbar = root.querySelector('[data-component="statusbar"]');
  const statusbarMode = statusbar.querySelector('[data-role="statusbar-mode"]');
  const statusbarData = statusbar.querySelector('[data-role="statusbar-data"]');

  chipsContainer.innerHTML = `<span class="atlas-mode-current">${getMode(PRIMARY_MODE_ID).label}</span>`;

  const prefsButton = root.querySelector('[data-component="prefs-button"]');
  if (prefsButton) {
    prefsButton.addEventListener("click", () => {
      store.set({ onboardingOpen: true });
    });
  }

  // Legacy ?mode=home/city links now land on the single rent-sale-ratio view.
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("mode");
  const normalizedMode = normalizeModeId(requested || store.get().mode);
  if (store.get().mode !== normalizedMode) {
    store.set({ mode: normalizedMode });
  }
  if (requested) {
    params.delete("mode");
    replaceSearch(params);
  }

  store.subscribe(renderFromState);
  renderFromState(store.get());

  function renderFromState(state) {
    const modeLabel = getMode(state.mode).label;
    statusbarMode.textContent = `指标：${modeLabel}`;
    if (state.runtime) {
      const tag = state.runtime.activeDataMode || "—";
      const dataLabel = dataModeLabel(tag);
      runtimeTag.textContent = `数据：${dataLabel}`;
      statusbarData.textContent = `数据：${dataLabel}`;
    }
  }
}

function replaceSearch(params) {
  const query = params.toString();
  const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
  window.history.replaceState({}, "", nextUrl);
}

function dataModeLabel(mode) {
  return {
    database: "本机数据库",
    staged: "暂存样本",
    mock: "演示样本",
    empty: "待导入",
  }[mode] || "演示/暂存样本";
}
