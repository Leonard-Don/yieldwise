export const PRIMARY_MODE_ID = "yield";

export const MODES = [
  {
    id: PRIMARY_MODE_ID,
    label: "租售比观察",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "yield", label: "租售比", format: "pct" },
      { key: "paybackYears", label: "回本年限", format: "years" },
      { key: "score", label: "机会分", format: "int" },
      { key: "sample", label: "样本", format: "sample" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    defaultFilters: {},
  },
];

const MODE_INDEX = new Map(MODES.map((m) => [m.id, m]));

export function getMode(id) {
  return MODE_INDEX.get(normalizeModeId(id)) || MODES[0];
}

export function normalizeModeId(id) {
  return MODE_INDEX.has(id) ? id : PRIMARY_MODE_ID;
}

export function yieldColorFor(yieldPct) {
  if (yieldPct === null || yieldPct === undefined || Number.isNaN(yieldPct)) {
    return "var(--text-dim)";
  }
  if (yieldPct < 3.5) return "var(--down)";
  if (yieldPct < 5) return "var(--warn)";
  return "var(--up)";
}

export function defaultFiltersFor(modeId) {
  return { ...(getMode(modeId).defaultFilters || {}) };
}

const LEGACY_DEFAULT_FILTERS = {
  yield: [{ minYield: 4, maxBudget: 1500 }],
};

export function normalizeInitialFiltersFor(modeId, persistedFilters) {
  if (!persistedFilters || typeof persistedFilters !== "object" || Array.isArray(persistedFilters)) {
    return defaultFiltersFor(modeId);
  }
  const filters = { ...persistedFilters };
  const legacyDefaults = LEGACY_DEFAULT_FILTERS[modeId] || [];
  if (legacyDefaults.some((legacy) => filtersEqual(filters, legacy))) {
    return defaultFiltersFor(modeId);
  }
  return filters;
}

function filtersEqual(left, right) {
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);
  if (leftKeys.length !== rightKeys.length) return false;
  return rightKeys.every((key) => {
    if (!Object.prototype.hasOwnProperty.call(left, key)) return false;
    const leftValue = left[key];
    const rightValue = right[key];
    if (typeof rightValue === "number") return Number(leftValue) === rightValue;
    return leftValue === rightValue;
  });
}

const FILTER_KEY_MAP = {
  minYield: "min_yield",
  maxBudget: "max_budget",
  minSamples: "min_samples",
  minScore: "min_score",
  district: "district",
};

const FILTER_API_DEFAULTS = {
  minYield: 0,
  maxBudget: 10000,
  minSamples: 0,
  minScore: 0,
  district: "all",
};

export function filtersToApiParams(filters) {
  const out = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (value === undefined || value === null || value === "") continue;
    const apiKey = FILTER_KEY_MAP[key];
    if (!apiKey) continue;
    out[apiKey] = value;
  }
  return out;
}

const FILTER_LABELS = {
  minYield: (v) => `租售比 ≥ ${v}%`,
  maxBudget: (v) => `总价 ≤ ${v} 万`,
  minSamples: (v) => `样本量 ≥ ${v}`,
  minScore: (v) => `机会分 ≥ ${v}`,
  district: (v) => `区域 = ${v}`,
};

export function describeFilter(key, value) {
  const fn = FILTER_LABELS[key];
  return fn ? fn(value) : `${key} = ${value}`;
}

export function prunedFilters(filters) {
  const out = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (value === undefined || value === null || value === "") continue;
    if (Object.prototype.hasOwnProperty.call(FILTER_API_DEFAULTS, key)) {
      const apiDefault = FILTER_API_DEFAULTS[key];
      if (typeof apiDefault === "number" && Number(value) === apiDefault) continue;
      if (typeof apiDefault === "string" && value === apiDefault) continue;
    }
    out[key] = value;
  }
  return out;
}

export function resolveDefaultFilters() {
  return { ...defaultFiltersFor(PRIMARY_MODE_ID) };
}
