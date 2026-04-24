import { MODES, getMode } from "./modes.js";

const VALID_MODES = new Set(MODES.map((m) => m.id));

export function initShell({ root, store }) {
  const chipsContainer = root.querySelector('[data-component="mode-chips"]');
  const runtimeTag = root.querySelector('[data-component="runtime-tag"]');
  const statusbar = root.querySelector('[data-component="statusbar"]');
  const statusbarMode = statusbar.querySelector('[data-role="statusbar-mode"]');
  const statusbarData = statusbar.querySelector('[data-role="statusbar-data"]');

  // Render chips once. Stub modes (home/city) are still clickable in Phase 2b
  // — the spec calls for switchable chips with stub board content rather than
  // disabled chips. Per-mode behavior wires up in Phase 3.
  chipsContainer.innerHTML = MODES.map(
    (m) => `<button type="button" class="atlas-mode-chip" data-mode="${m.id}" aria-pressed="false" data-stub="${m.enabled ? "false" : "true"}">⌘${m.hotkey} ${m.label}</button>`,
  ).join("");
  chipsContainer.addEventListener("click", (event) => {
    const target = event.target.closest("[data-mode]");
    if (!target) return;
    setMode(target.dataset.mode);
  });

  // Initial mode from URL ?mode=... falling back to store.
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("mode");
  if (requested && VALID_MODES.has(requested)) {
    store.set({ mode: requested });
  }

  store.subscribe(renderFromState);
  renderFromState(store.get());

  function setMode(modeId) {
    if (!VALID_MODES.has(modeId)) return;
    store.set({ mode: modeId });
    const next = new URLSearchParams(window.location.search);
    next.set("mode", modeId);
    window.history.replaceState({}, "", `${window.location.pathname}?${next.toString()}`);
  }

  function renderFromState(state) {
    const activeMode = state.mode;
    chipsContainer
      .querySelectorAll("[data-mode]")
      .forEach((btn) => {
        btn.setAttribute("aria-pressed", btn.dataset.mode === activeMode ? "true" : "false");
      });
    statusbarMode.textContent = `mode: ${activeMode}`;
    if (state.runtime) {
      const tag = state.runtime.activeDataMode || "—";
      runtimeTag.textContent = `data ${tag}`;
      statusbarData.textContent = `data: ${tag}`;
    }
  }
}
