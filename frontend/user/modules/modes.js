export const MODES = [
  {
    id: "yield",
    label: "收益猎手",
    hotkey: "1",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "yield", label: "租售比", format: "pct" },
      { key: "paybackYears", label: "回本年限", format: "years" },
      { key: "score", label: "机会分", format: "int" },
      { key: "sample", label: "样本", format: "sample" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    defaultFilters: { minYield: 4, maxBudget: 1500 },
  },
  {
    id: "home",
    label: "自住找房",
    hotkey: "2",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "avgPriceWan", label: "预算匹配", format: "wan" },
      { key: "score", label: "配套", format: "int" },
      { key: "yield", label: "价格安全垫", format: "pct" },
      { key: "sample", label: "样本可信度", format: "sample" },
    ],
    defaultSort: { key: "avgPriceWan", direction: "asc" },
    defaultFilters: {},
  },
  {
    id: "city",
    label: "全市观察",
    hotkey: "3",
    boardColumns: [
      { key: "name", label: "行政区" },
      { key: "yield", label: "均值", format: "pct" },
      { key: "score", label: "分位", format: "int" },
      { key: "sample", label: "样本", format: "sample" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    defaultFilters: {},
  },
];

const MODE_INDEX = new Map(MODES.map((m) => [m.id, m]));

export function getMode(id) {
  return MODE_INDEX.get(id) || MODES[0];
}

export function yieldColorFor(yieldPct) {
  if (yieldPct === null || yieldPct === undefined || Number.isNaN(yieldPct)) {
    return "var(--text-dim)";
  }
  if (yieldPct < 3.5) return "var(--down)";
  if (yieldPct < 5) return "var(--warn)";
  return "var(--up)";
}

function normalizeYieldScalar(value) {
  if (value === null || value === undefined) return null;
  const num = Number(value);
  if (Number.isNaN(num)) return null;
  // Match the percent-vs-fraction heuristic in map.js: < 1 means fraction.
  return num < 1 ? num * 100 : num;
}

export function districtColorFor(value, mean) {
  const v = normalizeYieldScalar(value);
  const m = normalizeYieldScalar(mean);
  if (v === null || m === null) return "var(--text-dim)";
  const delta = v - m;
  if (delta > 0.2) return "var(--up)";
  if (delta < -0.2) return "var(--down)";
  return "var(--warn)";
}

export function defaultFiltersFor(modeId) {
  return { ...(getMode(modeId).defaultFilters || {}) };
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

export function resolveDefaultFilters(modeId, userPrefs) {
  if (modeId === "yield") {
    return { ...defaultFiltersFor("yield") };
  }
  if (modeId === "home") {
    const out = {};
    if (userPrefs && typeof userPrefs === "object") {
      const budget = userPrefs.budget_max_wan;
      if (budget !== null && budget !== undefined && budget !== "") {
        out.maxBudget = Number(budget);
      }
      const districts = userPrefs.districts;
      if (Array.isArray(districts) && districts.length > 0) {
        out.district = String(districts[0]);
      }
    }
    return out;
  }
  return {};
}
