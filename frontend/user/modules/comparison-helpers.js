export const MAX_COMPARISON_ITEMS = 5;

export function normalizeComparisonItems(raw) {
  if (!Array.isArray(raw)) return [];
  const out = [];
  const seen = new Set();
  for (const item of raw) {
    const normalized = normalizeComparisonItem(item);
    if (!normalized) continue;
    const key = comparisonKey(normalized);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(normalized);
    if (out.length >= MAX_COMPARISON_ITEMS) break;
  }
  return out;
}

export function normalizeComparisonItem(item) {
  if (!item || typeof item !== "object") return null;
  const targetId = String(item.target_id || item.targetId || "").trim();
  const targetType = String(item.target_type || item.targetType || "").trim();
  if (!targetId || !["building", "community", "district"].includes(targetType)) {
    return null;
  }
  return {
    target_id: targetId,
    target_type: targetType,
    target_name: String(item.target_name || item.targetName || item.name || targetId),
    district_name: item.district_name || item.districtName || null,
    yield_pct: coerceNumber(item.yield_pct ?? item.yieldPct ?? item.yield ?? item.yieldAvg),
    score: coerceNumber(item.score),
    quality_label: item.quality_label || item.qualityLabel || item.quality?.label || null,
    quality_status: item.quality_status || item.qualityStatus || item.quality?.status || null,
    sample_label: item.sample_label || item.sampleLabel || item.quality?.sampleLabel || null,
    primary_building_id: item.primary_building_id || item.primaryBuildingId || null,
  };
}

export function addComparisonItem(items, candidate) {
  const current = normalizeComparisonItems(items);
  const normalized = normalizeComparisonItem(candidate);
  if (!normalized) return current;
  const key = comparisonKey(normalized);
  if (current.some((item) => comparisonKey(item) === key)) {
    return current;
  }
  return [...current, normalized].slice(0, MAX_COMPARISON_ITEMS);
}

export function removeComparisonItem(items, targetId, targetType) {
  return normalizeComparisonItems(items).filter(
    (item) => !(item.target_id === targetId && item.target_type === targetType),
  );
}

export function isCompared(items, targetId, targetType) {
  return normalizeComparisonItems(items).some(
    (item) => item.target_id === String(targetId) && item.target_type === String(targetType),
  );
}

export function comparisonCount(items) {
  return normalizeComparisonItems(items).length;
}

export function candidateFromItem(item, modeId) {
  if (!item || typeof item !== "object") return null;
  const targetType = modeId === "city" ? "district" : "community";
  return normalizeComparisonItem({
    target_id: item.id,
    target_type: targetType,
    target_name: item.name,
    district_name: item.districtName,
    yield_pct: item.yield,
    score: item.score,
    quality_label: item.qualityLabel || item.quality?.label,
    quality_status: item.qualityStatus || item.quality?.status,
    sample_label: item.quality?.sampleLabel,
    primary_building_id: item.primaryBuildingId,
  });
}

export function candidateFromSelection(selection) {
  if (!selection || !["building", "community", "district"].includes(selection.type)) {
    return null;
  }
  const props = selection.props || {};
  return normalizeComparisonItem({
    target_id: selection.id,
    target_type: selection.type,
    target_name: props.name || props.communityName || selection.id,
    district_name: props.districtName,
    yield_pct: props.yield ?? props.yieldAvg,
    score: props.score,
    quality_label: props.qualityLabel,
    quality_status: props.qualityStatus,
    sample_label: props.quality?.sampleLabel,
    primary_building_id: selection.primaryBuildingId || props.primaryBuildingId,
  });
}

export function buildDecisionMemoPayload(items) {
  return {
    targets: normalizeComparisonItems(items).map((item) => ({
      target_id: item.target_id,
      target_type: item.target_type,
    })),
  };
}

export function comparisonKey(item) {
  return `${item.target_type}:${item.target_id}`;
}

function coerceNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}
