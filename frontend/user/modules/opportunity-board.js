import { api } from "./api.js";
import { getMode, filtersToApiParams, resolveDefaultFilters } from "./modes.js";

export async function initBoard({ container, store }) {
  const list = container.querySelector('[data-role="board-list"]');
  const empty = container.querySelector('[data-role="board-empty"]');
  const countEl = container.querySelector('[data-role="board-count"]');
  const modeLabelEl = container.querySelector('[data-role="board-mode-label"]');

  let lastItems = [];
  let lastMode = store.get().mode;
  let lastFilterKey = filterKeyFor(store.get(), lastMode);

  function publishCount(value) {
    const current = store.get().boardCount;
    if (current === value) return;
    store.set({ boardCount: value });
  }

  await loadFor(lastMode, store.get());

  store.subscribe(async (state) => {
    const nextFilterKey = filterKeyFor(state, state.mode);
    if (state.mode !== lastMode || nextFilterKey !== lastFilterKey) {
      lastMode = state.mode;
      lastFilterKey = nextFilterKey;
      await loadFor(state.mode, state);
      return;
    }
    render(state);
  });

  async function loadFor(modeId, state) {
    const mode = getMode(modeId);
    if (!mode.enabled) {
      lastItems = [];
      render(store.get());
      return;
    }
    const persisted = state && state.filters ? state.filters[modeId] : null;
    const filters =
      persisted && Object.keys(persisted).length > 0
        ? persisted
        : resolveDefaultFilters(modeId, (state && state.userPrefs) || null);
    const params = filtersToApiParams(filters);
    try {
      const data = await api.opportunities(params);
      lastItems = sortItems(data.items || [], mode.defaultSort);
    } catch (err) {
      console.error("[atlas:board] opportunities load failed", err);
      lastItems = [];
    }
    render(store.get());
  }

  function render(state) {
    const mode = getMode(state.mode);
    modeLabelEl.textContent = mode.label;
    if (!mode.enabled) {
      list.innerHTML = "";
      empty.hidden = false;
      empty.textContent = `${mode.label} 模式将于 Phase 3 启用`;
      countEl.textContent = "--";
      publishCount(null);
      return;
    }
    if (lastItems.length === 0) {
      list.innerHTML = "";
      empty.hidden = false;
      empty.textContent = "暂无机会";
      countEl.textContent = "0";
      publishCount(0);
      return;
    }
    empty.hidden = true;
    countEl.textContent = String(lastItems.length);
    publishCount(lastItems.length);
    list.innerHTML = lastItems
      .map((item) => renderRow(item, mode, state.selection))
      .join("");
    list.querySelectorAll(".atlas-board-row").forEach((row) => {
      row.addEventListener("click", () => {
        const id = row.dataset.id;
        const item = lastItems.find((it) => String(it.id) === id);
        if (!item) return;
        store.set({
          selection: {
            type: "community",
            id: item.id,
            props: item,
            primaryBuildingId: item.primaryBuildingId,
          },
        });
      });
    });
  }
}

function renderRow(item, mode, selection) {
  const selected =
    selection && (selection.id === item.id || selection.id === item.primaryBuildingId);
  const cells = mode.boardColumns
    .map((col) => formatCell(item, col))
    .join("");
  return `<li class="atlas-board-row mono" data-id="${escapeAttr(item.id)}" aria-selected="${selected ? "true" : "false"}">${cells}</li>`;
}

function formatCell(item, col) {
  const raw = item[col.key];
  if (col.key === "name") {
    return `<span class="name" title="${escapeAttr(raw ?? "")}">${escapeText(raw ?? "—")}</span>`;
  }
  if (col.key === "districtName") {
    return `<span class="name">${escapeText(raw ?? "—")}</span>`;
  }
  return `<span class="secondary">${formatValue(raw, col.format)}</span>`;
}

function formatValue(value, format) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (format === "pct") return `${Number(value).toFixed(2)}%`;
  if (format === "wan") return Number(value).toLocaleString("en-US");
  if (format === "int") return String(Math.round(Number(value)));
  return String(value);
}

function sortItems(items, sortSpec) {
  if (!sortSpec) return items;
  const dir = sortSpec.direction === "asc" ? 1 : -1;
  return [...items].sort((a, b) => {
    const av = a[sortSpec.key];
    const bv = b[sortSpec.key];
    if (av === bv) return 0;
    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;
    return av > bv ? dir : -dir;
  });
}

function escapeText(value) {
  return String(value).replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function escapeAttr(value) {
  return escapeText(value).replace(/'/g, "&#39;");
}

function filterKeyFor(state, modeId) {
  const filters = (state && state.filters && state.filters[modeId]) || {};
  const prefsKey =
    state && state.userPrefs && state.userPrefs.updated_at
      ? state.userPrefs.updated_at
      : "";
  return JSON.stringify(filters) + "|" + prefsKey;
}
