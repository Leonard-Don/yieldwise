import {
  bucketBars,
  districtYieldDistribution,
  formatPct,
  formatWan,
  formatYuan,
  normalizeDecisionBrief,
  normalizeQuality,
  pickKpisFor,
  topCommunitiesFromDistrict,
} from "./drawer-data.js";

export function initDrawer({ root, store }) {
  const drawer = root.querySelector('[data-component="drawer"]');
  const backdrop = root.querySelector('[data-component="drawer-backdrop"]');
  const titleEl = drawer.querySelector('[data-role="drawer-title"]');
  const subtitleEl = drawer.querySelector('[data-role="drawer-subtitle"]');
  const bodyEl = drawer.querySelector('[data-role="drawer-body"]');
  const closeButton = drawer.querySelector('[data-role="drawer-close"]');

  let activeRequestId = 0;
  let lastSelectionId = null;
  let lastMode = null;

  closeButton.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  bodyEl.addEventListener("click", (event) => {
    const floorButton = event.target.closest("[data-floor-evidence]");
    if (floorButton) {
      void loadFloorEvidence(floorButton);
      return;
    }
    const row = event.target.closest("[data-community-id]");
    if (!row) return;
    const communityId = row.dataset.communityId;
    if (!communityId) return;
    store.set({
      selection: {
        type: "community",
        id: communityId,
        props: { name: row.querySelector(".atlas-district-name")?.textContent || "" },
      },
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer.dataset.open === "true") {
      close();
    }
  });

  store.subscribe(handleStateChange);
  handleStateChange(store.get());

  function handleStateChange(state) {
    const sel = state.selection;
    if (
      !sel ||
      (sel.type !== "building" &&
        sel.type !== "community" &&
        sel.type !== "district")
    ) {
      if (lastSelectionId !== null) {
        renderClosed();
        lastSelectionId = null;
        lastMode = null;
      }
      return;
    }
    const id = `${sel.type}:${sel.id}`;
    if (id === lastSelectionId) {
      // Same selection — only act if mode actually changed.
      if (state.mode !== lastMode) {
        lastMode = state.mode;
        renderKpisForCurrent(state.mode);
      }
      return;
    }
    lastSelectionId = id;
    lastMode = state.mode;
    const myRequestId = ++activeRequestId;
    open();
    renderLoading(sel);
    fetchDetail(sel)
      .then((detail) => {
        if (myRequestId !== activeRequestId) return; // a newer selection won
        renderDetail({ sel, detail, mode: state.mode });
      })
      .catch((err) => {
        if (myRequestId !== activeRequestId) return;
        renderError(err.message || "详情加载失败");
      });
  }

  function close() {
    store.set({ selection: null });
    renderClosed();
    lastSelectionId = null;
  }

  function open() {
    drawer.dataset.open = "true";
    backdrop.dataset.open = "true";
    drawer.setAttribute("aria-hidden", "false");
  }

  function renderClosed() {
    drawer.dataset.open = "false";
    backdrop.dataset.open = "false";
    drawer.setAttribute("aria-hidden", "true");
    titleEl.textContent = "—";
    subtitleEl.textContent = "—";
    bodyEl.innerHTML = '<div class="atlas-drawer-empty">选择楼栋或机会榜条目以查看详情</div>';
  }

  function renderLoading(sel) {
    titleEl.textContent = sel.props?.name || sel.props?.communityName || sel.id;
    subtitleEl.textContent = (sel.type || "").toUpperCase();
    bodyEl.innerHTML = `<div class="atlas-skeleton-section"><div class="atlas-skeleton-label"></div><div class="atlas-skeleton-grid-3"><div class="atlas-skeleton-card"></div><div class="atlas-skeleton-card"></div><div class="atlas-skeleton-card"></div></div></div><div class="atlas-skeleton-section"><div class="atlas-skeleton-label"></div><div class="atlas-skeleton-block"></div></div><div class="atlas-skeleton-section"><div class="atlas-skeleton-label"></div><div class="atlas-skeleton-grid-2"><div class="atlas-skeleton-card"></div><div class="atlas-skeleton-card"></div></div></div>`;
  }

  function renderError(message) {
    bodyEl.innerHTML = `<div class="atlas-drawer-status" data-state="error">${escapeText(message)}</div>`;
  }

  function renderDetail({ sel, detail, mode }) {
    titleEl.textContent = detail.name || sel.props?.name || sel.id;
    subtitleEl.textContent = (detail.districtName || sel.props?.districtName || "").toString();
    bodyEl.innerHTML = renderBody({ sel, detail, mode });
    bodyEl.dataset.detailJson = JSON.stringify({
      yieldAvg: detail.yieldAvg,
      score: detail.score,
      sampleSize: detail.sampleSize ?? detail.sample,
      saleMedianWan: detail.saleMedianWan ?? detail.avgPriceWan,
      rentMedianMonthly: detail.rentMedianMonthly ?? detail.monthlyRent,
      yield: detail.yield,
      paybackYears: detail.paybackYears,
      sample: detail.sample,
      osmFootprintCount: detail.osmFootprintCount,
      decisionBrief: detail.decisionBrief,
    });
  }

  function renderKpisForCurrent(mode) {
    if (!bodyEl.dataset.detailJson) return;
    const cached = JSON.parse(bodyEl.dataset.detailJson);
    const kpiHtml = renderKpiRow(pickKpisFor(mode, cached));
    const kpiContainer = bodyEl.querySelector('[data-role="kpi-row"]');
    if (kpiContainer) {
      kpiContainer.outerHTML = kpiHtml;
    }
  }

  function renderBody({ sel, detail, mode }) {
    if (sel && sel.type === "district") {
      return renderDistrictBody({ detail });
    }
    const kpis = pickKpisFor(mode, detail);
    const bars = bucketBars({
      low: detail.low ?? 0,
      mid: detail.mid ?? 0,
      high: detail.high ?? 0,
    });
    return [
      renderKpiRow(kpis),
      renderDecisionPanel(detail),
      renderQualityPanel(detail),
      renderFloorChart(bars),
      renderTopFloorEvidence(detail),
      renderListingSummary(detail),
    ].join("");
  }

  function renderDistrictBody({ detail }) {
    const kpis = pickKpisFor("city", {
      yield: detail.yield,
      paybackYears: detail.paybackYears,
      score: detail.score,
      sample: detail.sample,
    });
    const distribution = districtYieldDistribution(detail);
    const spread = distribution ? renderYieldSpread(distribution) : "";
    const top = topCommunitiesFromDistrict(detail, 8);
    return `${renderKpiRow(kpis)}${spread}<div><h3 class="atlas-section-title">区内小区（前 ${top.length}）</h3>${renderCommunityList(top)}</div>`;
  }

  function renderYieldSpread(distribution) {
    const { points, min, max, q1, median, q3, span } = distribution;
    const safeSpan = span > 0 ? span : 1;
    const pct = (value) => ((value - min) / safeSpan) * 100;
    const dots = points
      .map(
        (p) =>
          `<span class="atlas-yield-spread-dot" style="left: ${pct(p.value).toFixed(2)}%" title="${escapeText(p.name)} · ${escapeText(formatPct(p.value))}"></span>`,
      )
      .join("");
    const summary = `<div class="atlas-yield-spread-summary"><span>min ${escapeText(formatPct(min))}</span><span>中位 ${escapeText(formatPct(median))}</span><span>max ${escapeText(formatPct(max))}</span></div>`;
    const box =
      span > 0
        ? `<span class="atlas-yield-spread-box" style="left: ${pct(q1).toFixed(2)}%; right: ${(100 - pct(q3)).toFixed(2)}%"></span>`
        : "";
    const medianMarker =
      span > 0
        ? `<span class="atlas-yield-spread-median" style="left: ${pct(median).toFixed(2)}%"></span>`
        : "";
    return `<div class="atlas-yield-spread"><h3 class="atlas-section-title">区内 yield 分布（${points.length} 个小区）</h3><div class="atlas-yield-spread-track">${box}${medianMarker}${dots}</div>${summary}</div>`;
  }

  function renderCommunityList(rows) {
    if (rows.length === 0) {
      return `<div class="atlas-district-empty">该区暂无小区数据</div>`;
    }
    return `<ol class="atlas-district-list">${rows
      .map(
        (row) =>
          `<li class="atlas-district-row" data-community-id="${escapeText(row.id)}"><span class="atlas-district-name">${escapeText(row.name)}</span><span class="atlas-district-stat">${escapeText(formatPct(row.yield))}</span><span class="atlas-district-stat">${escapeText(formatScore(row.score))}</span></li>`,
      )
      .join("")}</ol>`;
  }

  function formatScore(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return "—";
    return String(Math.round(Number(value)));
  }

  function renderKpiRow(kpis) {
    const cells = kpis
      .map(
        (k) => `<div class="atlas-kpi"><span class="atlas-kpi-label">${escapeText(k.label)}</span><span class="atlas-kpi-value">${escapeText(k.value)}</span></div>`,
      )
      .join("");
    return `<div class="atlas-kpi-row" data-role="kpi-row">${cells}</div>`;
  }

  function renderFloorChart(bars) {
    const cols = bars
      .map(
        (b) =>
          `<div class="atlas-bucket-col"><span class="atlas-bucket-value">${escapeText(formatBucketValue(b.value))}</span><div class="atlas-bucket-bar-track"><div class="atlas-bucket-bar" style="height: ${b.pct}%"></div></div><span class="atlas-bucket-label">${escapeText(b.label)}</span></div>`,
      )
      .join("");
    return `<div><h3 class="atlas-section-title">楼层段租售比</h3><div class="atlas-bucket-chart">${cols}</div></div>`;
  }

  function renderTopFloorEvidence(detail) {
    const floors = Array.isArray(detail.topFloors) ? detail.topFloors.slice(0, 4) : [];
    const buildingId = detail.id || detail.buildingId;
    if (!buildingId || floors.length === 0) return "";
    const rows = floors
      .map((floor) => {
        const floorNo = floor.floorNo;
        const label = `${floorNo}层 · ${formatPct(floor.yieldPct)} · ${formatScore(floor.opportunityScore)}分`;
        return `<button type="button" class="atlas-floor-evidence-chip" data-floor-evidence data-building-id="${escapeText(buildingId)}" data-floor-no="${escapeText(floorNo)}">${escapeText(label)}</button>`;
      })
      .join("");
    return `<section class="atlas-floor-evidence">
      <h3 class="atlas-section-title">重点楼层证据</h3>
      <div class="atlas-floor-evidence-chips">${rows}</div>
      <div class="atlas-floor-evidence-panel" data-role="floor-evidence-panel">选择楼层查看样本证据</div>
    </section>`;
  }

  function renderListingSummary(detail) {
    const sale = detail.saleMedianWan ?? detail.avgPriceWan;
    const rent = detail.rentMedianMonthly ?? detail.monthlyRent;
    const cells = [
      { label: "中位总价", value: formatWan(sale) },
      { label: "中位月租", value: formatYuan(rent) },
    ]
      .map(
        (c) =>
          `<div class="atlas-listing-cell"><span class="atlas-kpi-label">${escapeText(c.label)}</span><span class="atlas-kpi-value">${escapeText(c.value)}</span></div>`,
      )
      .join("");
    return `<div><h3 class="atlas-section-title">挂牌摘要</h3><div class="atlas-listing-summary">${cells}</div></div>`;
  }

  function renderQualityPanel(detail) {
    const quality = normalizeQuality(detail);
    if (!quality) return "";
    const score = quality.score === null ? "—" : `${quality.score}/100`;
    const checks = quality.checks.length
      ? quality.checks
          .map(
            (item) =>
              `<span class="atlas-quality-check" data-state="${escapeText(item.status || "info")}"><strong>${escapeText(item.label || "")}</strong>${escapeText(item.detail || "")}</span>`,
          )
          .join("")
      : "";
    const reason = quality.reasons[0] || quality.summary;
    return `<div class="atlas-quality-panel" data-quality-status="${escapeText(quality.status)}">
      <div class="atlas-quality-head">
        <span class="atlas-quality-badge" data-quality-status="${escapeText(quality.status)}">${escapeText(quality.label)}</span>
        <strong>${escapeText(score)}</strong>
        <small>${escapeText(quality.sampleLabel)}</small>
      </div>
      <p>${escapeText(reason || "")}</p>
      ${checks ? `<div class="atlas-quality-checks">${checks}</div>` : ""}
    </div>`;
  }

  function renderDecisionPanel(detail) {
    const brief = normalizeDecisionBrief(detail);
    if (!brief) return "";
    const factors = brief.factors.length
      ? `<div class="atlas-decision-factors">${brief.factors
          .map((factor) => `<span>${escapeText(factor)}</span>`)
          .join("")}</div>`
      : "";
    const risks = brief.risks.length
      ? `<ul class="atlas-decision-risks">${brief.risks
          .map((risk) => `<li>${escapeText(risk)}</li>`)
          .join("")}</ul>`
      : "";
    return `<div class="atlas-decision-panel" data-decision-stance="${escapeText(brief.stance)}">
      <div class="atlas-decision-head">
        <span class="atlas-decision-badge" data-decision-stance="${escapeText(brief.stance)}">${escapeText(brief.label)}</span>
        <strong>${escapeText(brief.summary)}</strong>
      </div>
      ${factors}
      ${risks}
      <p>${escapeText(brief.nextAction)}</p>
    </div>`;
  }

  async function fetchDetail(sel) {
    if (sel.type === "building") {
      return getJSON(`/api/v2/buildings/${encodeURIComponent(sel.id)}`);
    }
    if (sel.type === "community") {
      // Prefer the building behind a community row for richer KPI/floor data.
      const buildingId = sel.primaryBuildingId || sel.props?.primaryBuildingId;
      if (buildingId) {
        return getJSON(`/api/v2/buildings/${encodeURIComponent(buildingId)}`);
      }
      return getJSON(`/api/v2/communities/${encodeURIComponent(sel.id)}`);
    }
    if (sel.type === "district") {
      return getJSON(`/api/v2/districts/${encodeURIComponent(sel.id)}`);
    }
    throw new Error(`未知的选中类型：${sel.type}`);
  }

  async function loadFloorEvidence(button) {
    const panel = bodyEl.querySelector('[data-role="floor-evidence-panel"]');
    const buildingId = button.dataset.buildingId;
    const floorNo = button.dataset.floorNo;
    if (!panel || !buildingId || !floorNo) return;
    panel.dataset.state = "loading";
    panel.textContent = "楼层证据加载中…";
    try {
      const detail = await getJSON(`/api/v2/buildings/${encodeURIComponent(buildingId)}/floors/${encodeURIComponent(floorNo)}`);
      panel.dataset.state = "ready";
      panel.innerHTML = renderFloorEvidenceDetail(detail);
    } catch (err) {
      panel.dataset.state = "error";
      panel.textContent = err.message || "楼层证据加载失败";
    }
  }
}

async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API ${url} → ${response.status}`);
  }
  return response.json();
}

function formatBucketValue(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const num = Number(value);
  if (num === 0) return "0";
  return num >= 1 ? num.toFixed(2) : (num * 100).toFixed(2);
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function renderFloorEvidenceDetail(detail) {
  const pairs = Array.isArray(detail.samplePairs) ? detail.samplePairs.slice(0, 4) : [];
  const summary = detail.historySummary || {};
  const source = detail.evidenceSource === "imported" ? "真实导入样本" : detail.evidenceSource === "simulated" ? "演示样本" : "样本不足";
  const pairRows = pairs.length
    ? pairs.map(renderSamplePair).join("")
    : '<li class="atlas-floor-pair-empty">暂无可展示样本配对</li>';
  return `<div class="atlas-floor-evidence-head">
      <strong>${escapeText(detail.buildingName)} · ${escapeText(detail.floorNo)}层</strong>
      <span>${escapeText(source)} · ${escapeText(detail.importRun?.batchName || "当前快照")}</span>
    </div>
    <div class="atlas-floor-evidence-stats">
      <span>收益 ${escapeText(formatPct(detail.yieldPct))}</span>
      <span>配对 ${escapeText(summary.totalPairCount ?? detail.measuredMetrics?.pairCount ?? pairs.length)}</span>
      <span>批次 ${escapeText(summary.observedRuns ?? detail.historyTimeline?.length ?? 0)}</span>
    </div>
    <ol class="atlas-floor-pair-list">${pairRows}</ol>`;
}

function renderSamplePair(pair) {
  const refs = Array.isArray(pair.sourceSnapshotRefs) ? pair.sourceSnapshotRefs : [];
  const refText = refs
    .map((ref) => `${ref.kind === "sale" ? "售" : "租"} ${ref.sourceName || ""}#${ref.sourceListingId || "—"}`)
    .join(" · ");
  return `<li class="atlas-floor-pair">
    <strong>${escapeText(pair.unitNo || pair.pairId || "样本")}</strong>
    <span>${escapeText(formatPct(pair.yieldPct))} · ${escapeText(pair.salePriceWan ?? "—")}万 / ${escapeText(pair.monthlyRent ?? "—")}元</span>
    <small>${escapeText(refText || pair.normalizedAddress || "—")}</small>
    <small>${escapeText(pair.rawSaleAddress || "售源地址待补")} ｜ ${escapeText(pair.rawRentAddress || "租源地址待补")}</small>
  </li>`;
}
