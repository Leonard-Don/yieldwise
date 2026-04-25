const MINUS = "−";

function signed(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const num = Number(value);
  const abs = Math.abs(num).toFixed(digits);
  return num >= 0 ? `+${abs}` : `${MINUS}${abs}`;
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
}

function fmtInt(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return String(Math.round(Number(value)));
}

export function formatAlertLine(alert) {
  if (!alert) return "";
  const { kind, from_value: from, to_value: to, delta } = alert;
  if (kind === "yield_up" || kind === "yield_down") {
    return `租售比 ${fmt(from)}% → ${fmt(to)}% (${signed(delta)})`;
  }
  if (kind === "price_drop") {
    const fromNum = Number(from);
    const pct = fromNum > 0 ? ((Number(to) - fromNum) / fromNum) * 100 : 0;
    const pctSigned = pct >= 0 ? `+${pct.toFixed(1)}` : `${MINUS}${Math.abs(pct).toFixed(1)}`;
    return `总价 ${fmtInt(from)} → ${fmtInt(to)} 万 (${pctSigned}%)`;
  }
  if (kind === "score_jump") {
    const sign = Number(delta) >= 0 ? "+" : MINUS;
    return `机会分 ${fmtInt(from)} → ${fmtInt(to)} (${sign}${Math.abs(Math.round(Number(delta)))})`;
  }
  return `${kind} ${fmtInt(from)} → ${fmtInt(to)}`;
}

export function severityFor(alert) {
  if (!alert) return "warn";
  const kind = alert.kind;
  if (kind === "yield_up") return "up";
  if (kind === "yield_down" || kind === "price_drop") return "down";
  if (kind === "score_jump") {
    return Number(alert.delta) >= 0 ? "up" : "down";
  }
  return "warn";
}
