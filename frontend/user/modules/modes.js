export const MODES = [
  {
    id: "yield",
    label: "收益猎手",
    hotkey: "1",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "yield", label: "租售比", format: "pct" },
      { key: "score", label: "机会分", format: "int" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    enabled: true,
  },
  {
    id: "home",
    label: "自住找房",
    hotkey: "2",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "avgPriceWan", label: "总价(万)", format: "wan" },
      { key: "yield", label: "租售比", format: "pct" },
    ],
    defaultSort: { key: "avgPriceWan", direction: "asc" },
    enabled: false,
  },
  {
    id: "city",
    label: "全市观察",
    hotkey: "3",
    boardColumns: [
      { key: "districtName", label: "区" },
      { key: "yield", label: "均租售比", format: "pct" },
      { key: "score", label: "机会分", format: "int" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    enabled: false,
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
