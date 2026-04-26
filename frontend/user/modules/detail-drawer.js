import {
  bucketBars,
  formatPct,
  formatWan,
  formatYuan,
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
      sample: detail.sample,
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
      renderFloorChart(bars),
      renderListingSummary(detail),
    ].join("");
  }

  function renderDistrictBody({ detail }) {
    const kpis = pickKpisFor("city", {
      yield: detail.yield,
      score: detail.score,
      sample: detail.sample,
    });
    const top = topCommunitiesFromDistrict(detail, 8);
    return `${renderKpiRow(kpis)}<div><h3 class="atlas-section-title">区内小区（前 ${top.length}）</h3>${renderCommunityList(top)}</div>`;
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
