export function normalizeYieldPct(raw) {
  if (raw === null || raw === undefined) return null;
  const value = Number(raw);
  if (Number.isNaN(value)) return null;
  // Backend exposes yield either as a percentage (4.16) or a fraction (0.04).
  return value < 1 ? value * 100 : value;
}

export function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Number(value).toFixed(2)}%`;
}

export function formatYears(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const num = Number(value);
  if (num <= 0) return "—";
  return `${num.toFixed(1)} 年`;
}

export function formatBuildingCount(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const n = Math.round(Number(value));
  if (n <= 0) return "—";
  return `${n} 栋`;
}

export function formatWan(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Number(value).toFixed(2)} 万`;
}

export function formatYuan(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const rounded = Math.round(Number(value));
  return `¥${rounded.toLocaleString("en-US")}`;
}

export function formatInt(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return String(Math.round(Number(value)));
}

export function bucketBars({ low = 0, mid = 0, high = 0 } = {}) {
  const values = [
    { key: "low", label: "低层", value: Number(low) || 0 },
    { key: "mid", label: "中层", value: Number(mid) || 0 },
    { key: "high", label: "高层", value: Number(high) || 0 },
  ];
  const max = Math.max(...values.map((v) => v.value));
  return values.map((v) => ({
    ...v,
    pct: max > 0 ? Math.round((v.value / max) * 100) : 0,
  }));
}

export function pickKpisFor(modeId, detail) {
  const kpis = KPI_MAP[modeId] || KPI_MAP.yield;
  return kpis(detail);
}

const KPI_MAP = {
  yield: (d) => {
    const tiles = [
      { key: "yield", label: "租售比", value: formatPct(normalizeYieldPct(d.yieldAvg)) },
      { key: "payback", label: "回本年限", value: formatYears(d.paybackYears) },
      { key: "score", label: "机会分", value: formatInt(d.score) },
      { key: "sample", label: "样本量", value: formatInt(d.sampleSize) },
    ];
    if (d.osmFootprintCount > 0) {
      // Insert "实拍楼栋" between payback and score so it sits next to the
      // other quantitative tiles, not at the end.
      tiles.splice(2, 0, { key: "footprints", label: "实拍楼栋", value: formatBuildingCount(d.osmFootprintCount) });
    }
    return tiles;
  },
  home: (d) => {
    const tiles = [
      { key: "price", label: "中位总价", value: formatWan(d.saleMedianWan) },
      { key: "rent", label: "中位月租", value: formatYuan(d.rentMedianMonthly) },
      { key: "payback", label: "回本年限", value: formatYears(d.paybackYears) },
      { key: "sample", label: "样本量", value: formatInt(d.sampleSize) },
    ];
    if (d.osmFootprintCount > 0) {
      tiles.splice(3, 0, { key: "footprints", label: "实拍楼栋", value: formatBuildingCount(d.osmFootprintCount) });
    }
    return tiles;
  },
  city: (d) => [
    { key: "yield", label: "均租售比", value: formatPct(normalizeYieldPct(d.yield ?? d.yieldAvg)) },
    { key: "payback", label: "均回本年限", value: formatYears(d.paybackYears) },
    { key: "score", label: "均机会分", value: formatInt(d.score) },
    { key: "sample", label: "样本量", value: formatInt(d.sample ?? d.sampleSize) },
  ],
};

export function topCommunitiesFromDistrict(detail, limit) {
  if (!detail || typeof detail !== "object") return [];
  const items = Array.isArray(detail.communities) ? detail.communities : [];
  const out = [];
  for (const row of items) {
    if (!row || !row.id) continue;
    out.push({
      id: row.id,
      name: row.name || row.id,
      yield: row.yield ?? null,
      paybackYears: row.paybackYears ?? null,
      score: row.score ?? null,
    });
    if (out.length >= Math.max(0, limit | 0)) break;
  }
  return out;
}
