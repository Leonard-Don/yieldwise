export function isStarred(items, targetId) {
  if (!Array.isArray(items)) return false;
  for (const entry of items) {
    if (entry && entry.target_id === targetId) return true;
  }
  return false;
}

export function watchlistCount(items) {
  return Array.isArray(items) ? items.length : 0;
}

export function normalizeWatchlistItem(item) {
  if (!item || typeof item !== "object") return null;
  const targetId = String(item.target_id || item.targetId || "").trim();
  const targetType = String(item.target_type || item.targetType || "").trim();
  if (!targetId || !["building", "community", "district"].includes(targetType)) return null;
  const snapshot = item.current_snapshot || item.currentSnapshot || null;
  return {
    ...item,
    target_id: targetId,
    target_type: targetType,
    target_name: item.target_name || item.targetName || snapshot?.name || targetId,
    status: item.status || "watching",
    status_label: item.status_label || candidateStatusLabel(item.status),
    priority: clampPriority(item.priority),
    current_snapshot: snapshot,
    snapshot_delta: item.snapshot_delta || item.snapshotDelta || null,
    target_yield_pct: item.target_yield_pct ?? item.targetYieldPct ?? null,
    candidate_triggers: Array.isArray(item.candidate_triggers || item.candidateTriggers)
      ? item.candidate_triggers || item.candidateTriggers
      : [],
    candidate_tasks: Array.isArray(item.candidate_tasks || item.candidateTasks)
      ? item.candidate_tasks || item.candidateTasks
      : [],
    candidate_action: item.candidate_action || item.candidateAction || null,
  };
}

export function normalizeWatchlistItems(items) {
  if (!Array.isArray(items)) return [];
  return items.map(normalizeWatchlistItem).filter(Boolean).sort(compareWatchlistItems);
}

export function candidateStatusLabel(status) {
  return {
    watching: "观察",
    researching: "复核中",
    shortlisted: "候选",
    rejected: "搁置",
  }[status] || "观察";
}

export function targetTypeLabel(type) {
  return {
    building: "楼栋",
    community: "小区",
    district: "区",
  }[type] || "对象";
}

export function candidateToComparisonItem(item) {
  const normalized = normalizeWatchlistItem(item);
  if (!normalized) return null;
  const snapshot = normalized.current_snapshot || {};
  return {
    target_id: normalized.target_id,
    target_type: normalized.target_type,
    target_name: normalized.target_name,
    district_name: snapshot.districtName || normalized.district_name || null,
    yield_pct: snapshot.yield ?? normalized.yield_pct ?? null,
    score: snapshot.score ?? normalized.score ?? null,
    quality_label: snapshot.qualityLabel || normalized.quality_label || null,
    quality_status: snapshot.qualityStatus || normalized.quality_status || null,
    sample_label: snapshot.sampleLabel || normalized.sample_label || null,
    primary_building_id: snapshot.primaryBuildingId || normalized.primary_building_id || null,
  };
}

export function buildWatchlistMemoPayload(items) {
  const normalized = normalizeWatchlistItems(items).slice(0, 5);
  return {
    targets: normalized.map((item) => ({
      target_id: item.target_id,
      target_type: item.target_type,
    })),
    candidate_contexts: normalized.map((item) => ({
      target_id: item.target_id,
      target_type: item.target_type,
      status: item.status || null,
      priority: item.priority || null,
      thesis: item.thesis || null,
      notes: item.notes || null,
      target_price_wan: item.target_price_wan ?? null,
      target_monthly_rent: item.target_monthly_rent ?? null,
      target_yield_pct: item.target_yield_pct ?? null,
      review_due_at: item.review_due_at || null,
      task_labels: (item.candidate_tasks || []).map((task) => task.label).filter(Boolean),
      trigger_labels: (item.candidate_triggers || []).map((trigger) => trigger.label).filter(Boolean),
    })),
  };
}

export function formatCandidateMetric(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `${number.toFixed(suffix === "%" ? 2 : 0)}${suffix}`;
}

export function candidateTaskGroupLabel(group) {
  return {
    due_review: "到期复核",
    target_rule: "目标触发",
    changed: "价格/样本变化",
    evidence_missing: "证据缺口",
    shortlisted: "Shortlist",
    ready: "可比较",
    rejected: "已放弃",
  }[group] || "全部";
}

export function countTaskGroups(items) {
  const counts = {
    all: 0,
    due_review: 0,
    target_rule: 0,
    changed: 0,
    evidence_missing: 0,
    shortlisted: 0,
  };
  for (const item of normalizeWatchlistItems(items)) {
    counts.all += 1;
    const groups = new Set((item.candidate_tasks || []).map((task) => task.group).filter(Boolean));
    if (item.status === "shortlisted") groups.add("shortlisted");
    for (const group of groups) {
      if (Object.hasOwn(counts, group)) counts[group] += 1;
    }
  }
  return counts;
}

export function candidateMatchesTaskGroup(item, group) {
  if (!group || group === "all") return true;
  const normalized = normalizeWatchlistItem(item);
  if (!normalized) return false;
  if (group === "shortlisted" && normalized.status === "shortlisted") return true;
  return (normalized.candidate_tasks || []).some((task) => task.group === group);
}

export function reviewDateAfter(days, base = new Date()) {
  const date = new Date(base);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function compareWatchlistItems(a, b) {
  const statusRank = { shortlisted: 0, researching: 1, watching: 2, rejected: 3 };
  const actionRank = {
    due_review: 0,
    target_rule: 1,
    changed: 2,
    evidence_missing: 3,
    shortlisted: 4,
    ready: 5,
    rejected: 8,
  };
  return (
    (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) ||
    (actionRank[a.candidate_action?.level] ?? 9) - (actionRank[b.candidate_action?.level] ?? 9) ||
    Number(a.priority || 3) - Number(b.priority || 3) ||
    String(a.added_at || "").localeCompare(String(b.added_at || ""))
  );
}

function clampPriority(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 3;
  return Math.min(5, Math.max(1, Math.round(number)));
}
