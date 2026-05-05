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
  return {
    targets: normalizeWatchlistItems(items).slice(0, 5).map((item) => ({
      target_id: item.target_id,
      target_type: item.target_type,
    })),
  };
}

export function formatCandidateMetric(value, suffix = "") {
  if (value === null || value === undefined || value === "") return "—";
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return `${number.toFixed(suffix === "%" ? 2 : 0)}${suffix}`;
}

function compareWatchlistItems(a, b) {
  const statusRank = { shortlisted: 0, researching: 1, watching: 2, rejected: 3 };
  const actionRank = { changed: 0, due: 1, ready: 2, sample: 3, blocked: 4 };
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
