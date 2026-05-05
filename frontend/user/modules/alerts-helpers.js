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
  if (kind === "district_delta_up" || kind === "district_delta_down") {
    return `区均租售比 ${fmt(from)}% → ${fmt(to)}% (${signed(delta)})`;
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
  if (kind === "target_price_hit") {
    return `目标价触发 ${fmtInt(from)} → ${fmtInt(to)} 万`;
  }
  if (kind === "target_rent_hit") {
    return `目标租金触发 ${fmtInt(from)} → ${fmtInt(to)} 元/月`;
  }
  if (kind === "target_yield_hit") {
    return `目标收益触发 ${fmt(from)}% → ${fmt(to)}%`;
  }
  if (kind === "review_due") {
    return "候选到期复核";
  }
  if (kind === "evidence_missing") {
    return "证据不足，需补样";
  }
  if (kind === "floor_sample_change") {
    return `同楼层样本 ${fmtInt(from)} → ${fmtInt(to)} 条`;
  }
  return `${kind} ${fmtInt(from)} → ${fmtInt(to)}`;
}

export function severityFor(alert) {
  if (!alert) return "warn";
  const kind = alert.kind;
  if (kind === "yield_up" || kind === "district_delta_up") return "up";
  if (kind === "yield_down" || kind === "price_drop" || kind === "district_delta_down") return "down";
  if (kind === "target_yield_hit" || kind === "target_rent_hit" || kind === "floor_sample_change") return "up";
  if (kind === "target_price_hit") return "down";
  if (kind === "score_jump") {
    return Number(alert.delta) >= 0 ? "up" : "down";
  }
  return "warn";
}
