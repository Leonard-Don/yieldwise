import { api } from "./api.js";
import { candidateFromItem, isCompared } from "./comparison-helpers.js";
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
    if (modeId === "city") {
      try {
        const data = await api.mapDistricts();
        lastItems = sortItems(data.districts || [], mode.defaultSort);
      } catch (err) {
        console.error("[atlas:board] districts load failed", err);
        lastItems = [];
      }
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
      .map((item) => renderRow(item, mode, state.selection, state.comparisonItems, state.mode))
      .join("");
    list.querySelectorAll("[data-comparison-add]").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const item = lastItems.find((it) => String(it.id) === button.dataset.id);
        const candidate = candidateFromItem(item, state.mode);
        button.dispatchEvent(
          new CustomEvent("atlas:add-comparison", {
            bubbles: true,
            detail: { candidate },
          }),
        );
      });
    });
    list.querySelectorAll(".atlas-board-row").forEach((row) => {
      row.addEventListener("click", () => {
        const id = row.dataset.id;
        const item = lastItems.find((it) => String(it.id) === id);
        if (!item) return;
        const selectionType = state.mode === "city" ? "district" : "community";
        const selection = {
          type: selectionType,
          id: item.id,
          props: item,
        };
        if (selectionType === "community" && item.primaryBuildingId) {
          selection.primaryBuildingId = item.primaryBuildingId;
        }
        store.set({ selection });
      });
    });
  }
}

function renderRow(item, mode, selection, comparisonItems, modeId) {
  const selected =
    selection && (selection.id === item.id || selection.id === item.primaryBuildingId);
  const candidate = candidateFromItem(item, modeId);
  const compared = candidate && isCompared(comparisonItems, candidate.target_id, candidate.target_type);
  const cells = mode.boardColumns
    .map((col) => formatCell(item, col))
    .join("");
  return `<li class="atlas-board-row mono" data-id="${escapeAttr(item.id)}" aria-selected="${selected ? "true" : "false"}">${cells}${renderCompareButton(item, compared)}</li>`;
}

function formatCell(item, col) {
  const raw = item[col.key];
  if (col.key === "name") {
    return `<span class="atlas-board-name-cell"><span class="name" title="${escapeAttr(raw ?? "")}">${escapeText(raw ?? "—")}</span>${renderQualityBadge(item.quality)}${renderDecisionBadge(item.decisionBrief)}</span>`;
  }
  if (col.key === "districtName") {
    return `<span class="name">${escapeText(raw ?? "—")}</span>`;
  }
  return `<span class="secondary">${formatValue(raw, col.format)}</span>`;
}

function renderCompareButton(item, compared) {
  return `<button type="button" class="atlas-compare-toggle" data-comparison-add data-id="${escapeAttr(item.id)}" aria-pressed="${compared ? "true" : "false"}" title="${compared ? "已加入对比" : "加入对比"}">${compared ? "已选" : "对比"}</button>`;
}

function renderQualityBadge(quality) {
  if (!quality || typeof quality !== "object") return "";
  const status = String(quality.status || "thin");
  const label = quality.label || {
    strong: "高可信",
    usable: "可用",
    thin: "样本薄",
    blocked: "待补样",
  }[status] || "待复核";
  const title = quality.summary || quality.sampleLabel || label;
  return `<span class="atlas-quality-mini" data-quality-status="${escapeAttr(status)}" title="${escapeAttr(title)}">${escapeText(label)}</span>`;
}

function renderDecisionBadge(brief) {
  if (!brief || typeof brief !== "object") return "";
  const stance = String(brief.stance || "watch");
  const label = brief.label || {
    shortlist: "候选",
    watch: "观察",
    sample_first: "补样",
  }[stance] || "观察";
  const title = brief.summary || label;
  return `<span class="atlas-decision-mini" data-decision-stance="${escapeAttr(stance)}" title="${escapeAttr(title)}">${escapeText(label)}</span>`;
}

function formatValue(value, format) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (format === "pct") return `${Number(value).toFixed(2)}%`;
  if (format === "years") {
    const n = Number(value);
    return n > 0 ? `${n.toFixed(1)} 年` : "—";
  }
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
