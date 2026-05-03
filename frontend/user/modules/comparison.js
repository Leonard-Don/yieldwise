import { api } from "./api.js";
import {
  addComparisonItem,
  buildDecisionMemoPayload,
  candidateFromSelection,
  comparisonCount,
  isCompared,
  normalizeComparisonItems,
  removeComparisonItem,
} from "./comparison-helpers.js";

export function initComparison({ root, store, storage }) {
  const tray = root.querySelector('[data-component="comparison-tray"]');
  const countEl = tray.querySelector('[data-role="comparison-count"]');
  const listEl = tray.querySelector('[data-role="comparison-list"]');
  const statusEl = tray.querySelector('[data-role="comparison-status"]');
  const exportButton = tray.querySelector('[data-role="comparison-export"]');
  const clearButton = tray.querySelector('[data-role="comparison-clear"]');
  const drawerButton = root.querySelector('[data-component="drawer-compare"]');

  root.addEventListener("atlas:add-comparison", (event) => {
    const candidate = event.detail?.candidate;
    addCandidate(candidate);
  });

  listEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-comparison-remove]");
    if (!button) return;
    const next = removeComparisonItem(store.get().comparisonItems, button.dataset.targetId, button.dataset.targetType);
    setItems(next);
  });

  clearButton.addEventListener("click", () => setItems([]));
  exportButton.addEventListener("click", () => {
    void exportMemo();
  });
  drawerButton.addEventListener("click", () => {
    addCandidate(candidateFromSelection(store.get().selection));
  });

  store.subscribe(render);
  render(store.get());

  function addCandidate(candidate) {
    const before = normalizeComparisonItems(store.get().comparisonItems);
    const after = addComparisonItem(before, candidate);
    setItems(after);
    if (!candidate) {
      setStatus("当前对象不可对比", "error");
    } else if (after.length === before.length) {
      setStatus("已在对比中", "idle");
    } else {
      setStatus("已加入对比", "ok");
    }
  }

  function setItems(items) {
    const normalized = normalizeComparisonItems(items);
    storage.write(normalized);
    store.set({ comparisonItems: normalized });
  }

  function render(state) {
    const items = normalizeComparisonItems(state.comparisonItems);
    const count = comparisonCount(items);
    tray.dataset.open = count > 0 ? "true" : "false";
    countEl.textContent = String(count);
    exportButton.disabled = count === 0;
    clearButton.disabled = count === 0;
    listEl.innerHTML = items.map(renderComparisonItem).join("");
    syncDrawerButton(state, items);
  }

  function syncDrawerButton(state, items) {
    const candidate = candidateFromSelection(state.selection);
    if (!candidate) {
      drawerButton.hidden = true;
      drawerButton.setAttribute("aria-pressed", "false");
      return;
    }
    drawerButton.hidden = false;
    drawerButton.disabled =
      !isCompared(items, candidate.target_id, candidate.target_type) &&
      comparisonCount(items) >= 5;
    drawerButton.setAttribute(
      "aria-pressed",
      isCompared(items, candidate.target_id, candidate.target_type) ? "true" : "false",
    );
  }

  async function exportMemo() {
    const items = normalizeComparisonItems(store.get().comparisonItems);
    if (!items.length) return;
    exportButton.disabled = true;
    setStatus("生成中", "idle");
    try {
      const payload = buildDecisionMemoPayload(items);
      const response = await api.decisionMemo(payload);
      saveMemo(response.memo || "", response.generatedAt || new Date().toISOString());
      setStatus("备忘录已生成", "ok");
    } catch (err) {
      console.error("[atlas:comparison] memo export failed", err);
      setStatus("导出失败", "error");
    } finally {
      exportButton.disabled = false;
    }
  }

  function saveMemo(markdown, generatedAt) {
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const stamp = String(generatedAt).replace(/[^0-9]/g, "").slice(0, 14) || "now";
    anchor.href = url;
    anchor.download = `yieldwise-decision-memo-${stamp}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.dataset.state = state;
  }
}

function renderComparisonItem(item) {
  const metric = item.yield_pct === null ? "—" : `${Number(item.yield_pct).toFixed(2)}%`;
  const quality = item.quality_label || "—";
  return `<li class="atlas-comparison-item">
    <span class="atlas-comparison-name" title="${escapeAttr(item.target_name)}">${escapeText(item.target_name)}</span>
    <span class="atlas-comparison-metric mono">${escapeText(metric)}</span>
    <span class="atlas-comparison-quality" data-quality-status="${escapeAttr(item.quality_status || "")}">${escapeText(quality)}</span>
    <button type="button" data-comparison-remove data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}" aria-label="移出对比">×</button>
  </li>`;
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
