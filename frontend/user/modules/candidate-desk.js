import { api } from "./api.js";
import {
  buildWatchlistMemoPayload,
  candidateToComparisonItem,
  formatCandidateMetric,
  normalizeWatchlistItems,
  targetTypeLabel,
} from "./watchlist-helpers.js";

export function initCandidateDesk({ root, store }) {
  const toggleButton = root.querySelector('[data-component="candidate-desk-toggle"]');
  const desk = root.querySelector('[data-component="candidate-desk"]');
  const summaryEl = desk.querySelector('[data-role="candidate-summary"]');
  const listEl = desk.querySelector('[data-role="candidate-list"]');
  const emptyEl = desk.querySelector('[data-role="candidate-empty"]');
  const statusEl = desk.querySelector('[data-role="candidate-status"]');
  const closeButton = desk.querySelector('[data-role="candidate-close"]');
  const exportButton = desk.querySelector('[data-role="candidate-export"]');
  const markSeenButton = desk.querySelector('[data-role="candidate-mark-seen"]');

  toggleButton.addEventListener("click", () => {
    const state = store.get();
    store.set({ candidateDeskOpen: !state.candidateDeskOpen });
  });
  closeButton.addEventListener("click", () => store.set({ candidateDeskOpen: false }));
  exportButton.addEventListener("click", () => {
    void exportWatchlistMemo();
  });
  markSeenButton.addEventListener("click", () => {
    void markSeenAndRefresh();
  });
  listEl.addEventListener("click", (event) => {
    const compareButton = event.target.closest("[data-candidate-compare]");
    if (compareButton) {
      const item = findCandidate(compareButton.dataset.targetId, compareButton.dataset.targetType);
      const candidate = candidateToComparisonItem(item);
      if (candidate) {
        root.dispatchEvent(new CustomEvent("atlas:add-comparison", { detail: { candidate } }));
        setStatus("已加入对比", "ok");
      }
      return;
    }
    const openButton = event.target.closest("[data-candidate-open]");
    if (openButton) {
      const item = findCandidate(openButton.dataset.targetId, openButton.dataset.targetType);
      if (item) {
        store.set({
          selection: {
            type: item.target_type,
            id: item.target_id,
            props: {
              name: item.target_name,
              districtName: item.current_snapshot?.districtName,
              primaryBuildingId: item.current_snapshot?.primaryBuildingId,
            },
          },
        });
      }
    }
  });
  listEl.addEventListener("change", (event) => {
    const field = event.target.closest("[data-candidate-field]");
    if (!field) return;
    void patchCandidateField(field);
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const items = normalizeWatchlistItems(state.watchlist);
    const alerts = Array.isArray(state.alerts?.items) ? state.alerts.items : [];
    const open = Boolean(state.candidateDeskOpen) && items.length > 0;
    desk.dataset.open = open ? "true" : "false";
    toggleButton.dataset.open = open ? "true" : "false";
    toggleButton.setAttribute("aria-expanded", open ? "true" : "false");
    exportButton.disabled = items.length === 0;
    markSeenButton.disabled = items.length === 0;
    emptyEl.hidden = items.length > 0;
    listEl.hidden = items.length === 0;
    summaryEl.textContent = summarize(items, alerts);
    listEl.innerHTML = items.map((item) => renderCandidateItem(item, alertsFor(alerts, item))).join("");
  }

  function findCandidate(targetId, targetType) {
    return normalizeWatchlistItems(store.get().watchlist).find(
      (item) => item.target_id === targetId && item.target_type === targetType,
    );
  }

  async function patchCandidateField(field) {
    const row = field.closest("[data-candidate-row]");
    if (!row) return;
    const targetId = row.dataset.targetId;
    const before = normalizeWatchlistItems(store.get().watchlist);
    const value = valueFromField(field);
    const payload = { [field.dataset.candidateField]: value };
    const optimistic = before.map((item) => (item.target_id === targetId ? { ...item, ...payload } : item));
    store.set({ watchlist: optimistic });
    setStatus("保存中", "idle");
    try {
      const saved = await api.watchlist.update(targetId, payload);
      store.set({
        watchlist: normalizeWatchlistItems(store.get().watchlist).map((item) =>
          item.target_id === targetId ? saved : item,
        ),
      });
      setStatus("已保存", "ok");
    } catch (err) {
      console.error("[atlas:candidates] update failed", err);
      setStatus("保存失败，已回滚", "error");
      store.set({ watchlist: before });
    }
  }

  async function exportWatchlistMemo() {
    const items = normalizeWatchlistItems(store.get().watchlist);
    if (!items.length) return;
    exportButton.disabled = true;
    setStatus("生成备忘录中", "idle");
    try {
      const response = await api.decisionMemo(buildWatchlistMemoPayload(items));
      saveMemo(response.memo || "", response.generatedAt || new Date().toISOString());
      setStatus("候选备忘录已生成", "ok");
    } catch (err) {
      console.error("[atlas:candidates] memo export failed", err);
      setStatus("备忘录导出失败", "error");
    } finally {
      exportButton.disabled = false;
    }
  }

  async function markSeenAndRefresh() {
    markSeenButton.disabled = true;
    setStatus("更新基线中", "idle");
    try {
      await api.alerts.markSeen();
      const [watchlist, alerts] = await Promise.all([
        api.watchlist.list(),
        api.alerts.sinceLastOpen(),
      ]);
      store.set({
        watchlist: watchlist.items || [],
        alerts: {
          items: alerts.items || [],
          last_open_at: alerts.last_open_at || null,
        },
      });
      setStatus("基线已更新", "ok");
    } catch (err) {
      console.error("[atlas:candidates] mark seen failed", err);
      setStatus("基线更新失败", "error");
    } finally {
      markSeenButton.disabled = false;
    }
  }

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.dataset.state = state;
  }
}

function renderCandidateItem(item, alerts) {
  const snapshot = item.current_snapshot || {};
  const action = item.candidate_action || {};
  const delta = item.snapshot_delta || {};
  const alertBadge = alerts.length ? `<span class="atlas-candidate-alert">${alerts.length} 条变化</span>` : "";
  return `<li class="atlas-candidate-item" data-candidate-row data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">
    <div class="atlas-candidate-main">
      <button type="button" class="atlas-candidate-name" data-candidate-open data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">${escapeText(item.target_name)}</button>
      <span class="mono dim">${escapeText(targetTypeLabel(item.target_type))} · ${escapeText(snapshot.districtName || "—")}</span>
      <span class="atlas-candidate-action" data-level="${escapeAttr(action.level || "idle")}">${escapeText(action.label || "观察")}</span>
      ${alertBadge}
    </div>
    <div class="atlas-candidate-metrics">
      <span>${escapeText(formatCandidateMetric(snapshot.yield, "%"))}</span>
      <span>${escapeText(formatCandidateMetric(snapshot.price, "万"))}</span>
      <span>${escapeText(formatDelta(delta.yieldDeltaPct, "%"))}</span>
      <span>${escapeText(snapshot.qualityLabel || snapshot.sampleLabel || "—")}</span>
    </div>
    <div class="atlas-candidate-controls">
      <label>状态${renderStatusSelect(item)}</label>
      <label>优先级<input type="number" min="1" max="5" step="1" value="${escapeAttr(item.priority)}" data-candidate-field="priority" /></label>
      <label>复核日<input type="date" value="${escapeAttr(item.review_due_at || "")}" data-candidate-field="review_due_at" /></label>
      <label>目标价<input type="number" min="0" step="10" value="${escapeAttr(item.target_price_wan ?? "")}" data-candidate-field="target_price_wan" /></label>
      <label>目标租金<input type="number" min="0" step="100" value="${escapeAttr(item.target_monthly_rent ?? "")}" data-candidate-field="target_monthly_rent" /></label>
    </div>
    <div class="atlas-candidate-notes">
      <input type="text" value="${escapeAttr(item.thesis || "")}" placeholder="投资假设" data-candidate-field="thesis" />
      <input type="text" value="${escapeAttr(item.notes || "")}" placeholder="${escapeAttr(action.next || "下一步动作")}" data-candidate-field="notes" />
      <button type="button" data-candidate-compare data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">对比</button>
    </div>
  </li>`;
}

function renderStatusSelect(item) {
  const options = [
    ["watching", "观察"],
    ["researching", "复核中"],
    ["shortlisted", "候选"],
    ["rejected", "搁置"],
  ];
  return `<select data-candidate-field="status">${options
    .map(([value, label]) => `<option value="${value}" ${item.status === value ? "selected" : ""}>${label}</option>`)
    .join("")}</select>`;
}

function summarize(items, alerts) {
  const changed = new Set(alerts.map((item) => item.target_id)).size;
  const shortlisted = items.filter((item) => item.status === "shortlisted").length;
  const due = items.filter((item) => item.review_due_at).length;
  return `${items.length} 个候选 · ${shortlisted} 个已候选 · ${changed} 个有变化 · ${due} 个待复核`;
}

function alertsFor(alerts, item) {
  return alerts.filter((alert) => alert.target_id === item.target_id);
}

function valueFromField(field) {
  const name = field.dataset.candidateField;
  if (["priority"].includes(name)) return Number(field.value || 3);
  if (["target_price_wan", "target_monthly_rent"].includes(name)) {
    return field.value === "" ? null : Number(field.value);
  }
  return field.value || null;
}

function formatDelta(value, suffix) {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (!Number.isFinite(number) || number === 0) return "—";
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toFixed(2)}${suffix}`;
}

function saveMemo(markdown, generatedAt) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const stamp = String(generatedAt).replace(/[^0-9]/g, "").slice(0, 14) || "now";
  anchor.href = url;
  anchor.download = `yieldwise-watchlist-memo-${stamp}.md`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
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
