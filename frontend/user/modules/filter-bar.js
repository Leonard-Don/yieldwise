import { describeFilter, getMode, prunedFilters } from "./modes.js";

const FILTER_API_DEFAULTS = {
  minYield: 0,
  maxBudget: 10000,
  minSamples: 0,
  minScore: 0,
};

export function initFilterBar({ root, store }) {
  const container = root.querySelector('[data-component="filter-bar"]');
  const chipsEl = container.querySelector('[data-role="filter-chips"]');
  const countEl = container.querySelector('[data-role="filter-count"]');

  chipsEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-clear]");
    if (!button) return;
    clearFilter(button.dataset.filterClear);
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const mode = getMode(state.mode);
    const activeFilters = prunedFilters((state.filters && state.filters[state.mode]) || {});
    const entries = Object.entries(activeFilters);

    if (entries.length === 0) {
      chipsEl.innerHTML = `<span class="atlas-filter-empty">${mode.label} 模式 · 无筛选</span>`;
    } else {
      chipsEl.innerHTML = entries
        .map(
          ([key, value]) =>
            `<span class="atlas-filter-chip">${escapeText(describeFilter(key, value))}<button type="button" class="atlas-filter-chip-clear" data-filter-clear="${escapeAttr(key)}" aria-label="移除 ${escapeAttr(describeFilter(key, value))}">×</button></span>`,
        )
        .join("");
    }

    if (typeof state.boardCount === "number") {
      countEl.textContent = `${state.boardCount} 条`;
    } else {
      countEl.textContent = "—";
    }
  }

  function clearFilter(key) {
    const state = store.get();
    const modeId = state.mode;
    const current = (state.filters && state.filters[modeId]) || {};
    if (!Object.prototype.hasOwnProperty.call(current, key)) return;
    const next = { ...current };
    if (Object.prototype.hasOwnProperty.call(FILTER_API_DEFAULTS, key)) {
      // Reset to the API default — keeps the key present in the filter object
      // so reloads still see an explicit value, but prunedFilters hides the chip.
      next[key] = FILTER_API_DEFAULTS[key];
    } else {
      delete next[key];
    }
    const filters = { ...(state.filters || {}), [modeId]: next };
    store.set({ filters });
  }
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function escapeAttr(value) {
  return escapeText(value).replace(/'/g, "&#39;");
}
