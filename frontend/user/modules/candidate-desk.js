import { api } from "./api.js";
import {
  buildWatchlistMemoPayload,
  candidateToComparisonItem,
  candidateMatchesTaskGroup,
  candidateTaskGroupLabel,
  countTaskGroups,
  formatCandidateMetric,
  normalizeWatchlistItems,
  targetTypeLabel,
} from "./watchlist-helpers.js";

export function initCandidateDesk({ root, store }) {
  const toggleButton = root.querySelector('[data-component="candidate-desk-toggle"]');
  const desk = root.querySelector('[data-component="candidate-desk"]');
  const summaryEl = desk.querySelector('[data-role="candidate-summary"]');
  const listEl = desk.querySelector('[data-role="candidate-list"]');
  const queueEl = desk.querySelector('[data-role="candidate-queue"]');
  const emptyEl = desk.querySelector('[data-role="candidate-empty"]');
  const statusEl = desk.querySelector('[data-role="candidate-status"]');
  const closeButton = desk.querySelector('[data-role="candidate-close"]');
  const exportButton = desk.querySelector('[data-role="candidate-export"]');
  const markSeenButton = desk.querySelector('[data-role="candidate-mark-seen"]');
  let activeQueueGroup = "all";

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
    const actionButton = event.target.closest("[data-candidate-action]");
    if (actionButton) {
      const item = findCandidate(actionButton.dataset.targetId, actionButton.dataset.targetType);
      if (item) {
        void runCandidateAction(item, actionButton.dataset.candidateAction);
      }
      return;
    }
    const memoButton = event.target.closest("[data-candidate-memo]");
    if (memoButton) {
      const item = findCandidate(memoButton.dataset.targetId, memoButton.dataset.targetType);
      if (item) {
        void exportWatchlistMemo([item]);
      }
      return;
    }
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
  queueEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-candidate-queue-group]");
    if (!button) return;
    activeQueueGroup = button.dataset.candidateQueueGroup || "all";
    render(store.get());
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
    const visibleItems = items.filter((item) => candidateMatchesTaskGroup(item, activeQueueGroup));
    desk.dataset.open = open ? "true" : "false";
    toggleButton.dataset.open = open ? "true" : "false";
    toggleButton.setAttribute("aria-expanded", open ? "true" : "false");
    exportButton.disabled = items.length === 0;
    markSeenButton.disabled = items.length === 0;
    emptyEl.hidden = items.length > 0;
    listEl.hidden = items.length === 0;
    summaryEl.textContent = summarize(items, alerts);
    queueEl.innerHTML = renderQueue(countTaskGroups(items), activeQueueGroup);
    listEl.innerHTML = visibleItems.map((item) => renderCandidateItem(item, alertsFor(alerts, item))).join("");
    if (items.length > 0 && visibleItems.length === 0) {
      listEl.innerHTML = `<li class="atlas-candidate-empty-row">该队列暂无候选</li>`;
    }
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

  async function exportWatchlistMemo(inputItems = null) {
    const items = normalizeWatchlistItems(inputItems || store.get().watchlist);
    if (!items.length) return;
    exportButton.disabled = true;
    setStatus("生成备忘录中", "idle");
    try {
      const response = await api.decisionMemo(buildWatchlistMemoPayload(items));
      saveMemo(response.memo || "", response.generatedAt || new Date().toISOString());
      setStatus(items.length === 1 ? "下一步备忘录已生成" : "候选备忘录已生成", "ok");
    } catch (err) {
      console.error("[atlas:candidates] memo export failed", err);
      setStatus("备忘录导出失败", "error");
    } finally {
      exportButton.disabled = false;
    }
  }

  async function runCandidateAction(item, action) {
    if (!action) return;
    setStatus("处理候选动作中", "idle");
    const payload = actionPayload(action);
    try {
      const saved = await api.watchlist.action(item.target_id, payload);
      store.set({
        watchlist: normalizeWatchlistItems(store.get().watchlist).map((row) =>
          row.target_id === item.target_id ? saved : row,
        ),
      });
      setStatus(actionStatusText(action), "ok");
    } catch (err) {
      console.error("[atlas:candidates] action failed", err);
      setStatus("候选动作失败", "error");
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
  const taskChips = renderTaskChips(item.candidate_tasks || []);
  const triggerChips = renderTriggerChips(item.candidate_triggers || []);
  return `<li class="atlas-candidate-item" data-candidate-row data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">
    <div class="atlas-candidate-main">
      <button type="button" class="atlas-candidate-name" data-candidate-open data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">${escapeText(item.target_name)}</button>
      <span class="mono dim">${escapeText(targetTypeLabel(item.target_type))} · ${escapeText(snapshot.districtName || "—")}</span>
      <span class="atlas-candidate-action" data-level="${escapeAttr(action.level || "idle")}">${escapeText(action.label || "观察")}</span>
      ${alertBadge}
      ${taskChips}
    </div>
    <div class="atlas-candidate-metrics">
      <span>${escapeText(formatCandidateMetric(snapshot.yield, "%"))}</span>
      <span>${escapeText(formatCandidateMetric(snapshot.price, "万"))}</span>
      <span>${escapeText(formatCandidateMetric(snapshot.rent, "元"))}</span>
      <span>${escapeText(formatDelta(delta.yieldDeltaPct, "%"))}</span>
      <span>${escapeText(snapshot.qualityLabel || snapshot.sampleLabel || "—")}</span>
      ${triggerChips}
    </div>
    <div class="atlas-candidate-controls">
      <label>状态${renderStatusSelect(item)}</label>
      <label>优先级<input type="number" min="1" max="5" step="1" value="${escapeAttr(item.priority)}" data-candidate-field="priority" /></label>
      <label>复核日<input type="date" value="${escapeAttr(item.review_due_at || "")}" data-candidate-field="review_due_at" /></label>
      <label>目标价<input type="number" min="0" step="10" value="${escapeAttr(item.target_price_wan ?? "")}" data-candidate-field="target_price_wan" /></label>
      <label>目标租金<input type="number" min="0" step="100" value="${escapeAttr(item.target_monthly_rent ?? "")}" data-candidate-field="target_monthly_rent" /></label>
      <label>目标收益<input type="number" min="0" step="0.1" value="${escapeAttr(item.target_yield_pct ?? "")}" data-candidate-field="target_yield_pct" /></label>
    </div>
    <div class="atlas-candidate-notes">
      <input type="text" value="${escapeAttr(item.thesis || "")}" placeholder="投资假设" data-candidate-field="thesis" />
      <input type="text" value="${escapeAttr(item.notes || "")}" placeholder="${escapeAttr(action.next || "下一步动作")}" data-candidate-field="notes" />
      <div class="atlas-candidate-row-actions">
        <button type="button" data-candidate-action="complete_review" data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">复核完成</button>
        <button type="button" data-candidate-action="defer_review" data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">延后</button>
        <button type="button" data-candidate-action="shortlist" data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">候选</button>
        <button type="button" data-candidate-action="reject" data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">放弃</button>
        <button type="button" data-candidate-memo data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">下一步 memo</button>
        <button type="button" data-candidate-compare data-target-id="${escapeAttr(item.target_id)}" data-target-type="${escapeAttr(item.target_type)}">对比</button>
      </div>
    </div>
  </li>`;
}

function renderQueue(counts, activeQueueGroup) {
  const groups = ["all", "due_review", "target_rule", "changed", "evidence_missing", "shortlisted"];
  return groups
    .map((group) => {
      const active = group === activeQueueGroup ? "true" : "false";
      const label = group === "all" ? "全部" : candidateTaskGroupLabel(group);
      return `<button type="button" data-candidate-queue-group="${escapeAttr(group)}" data-active="${active}">${escapeText(label)} <span>${escapeText(counts[group] ?? 0)}</span></button>`;
    })
    .join("");
}

function renderTaskChips(tasks) {
  if (!tasks.length) return "";
  return `<span class="atlas-candidate-taskline">${tasks
    .slice(0, 3)
    .map((task) => `<span data-group="${escapeAttr(task.group || "ready")}">${escapeText(task.label || "待办")}</span>`)
    .join("")}</span>`;
}

function renderTriggerChips(triggers) {
  if (!triggers.length) return "";
  return triggers
    .slice(0, 2)
    .map((trigger) => `<span class="atlas-candidate-trigger">${escapeText(trigger.label || "目标触发")}</span>`)
    .join("");
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
  const counts = countTaskGroups(items);
  return `${items.length} 个候选 · ${shortlisted} 个已候选 · ${changed} 个有变化 · ${counts.due_review} 个到期复核`;
}

function alertsFor(alerts, item) {
  return alerts.filter((alert) => alert.target_id === item.target_id);
}

function valueFromField(field) {
  const name = field.dataset.candidateField;
  if (["priority"].includes(name)) return Number(field.value || 3);
  if (["target_price_wan", "target_monthly_rent", "target_yield_pct"].includes(name)) {
    return field.value === "" ? null : Number(field.value);
  }
  return field.value || null;
}

function actionPayload(action) {
  if (action === "complete_review") return { action, days: 14 };
  if (action === "defer_review") return { action, days: 7 };
  if (action === "shortlist") return { action, days: 7 };
  return { action };
}

function actionStatusText(action) {
  return {
    complete_review: "复核已完成，已排入下一轮",
    defer_review: "已延后复核",
    shortlist: "已加入 shortlist",
    reject: "已标记放弃",
  }[action] || "候选已更新";
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
