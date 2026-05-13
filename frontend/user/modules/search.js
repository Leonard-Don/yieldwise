import { api } from "./api.js";
import { clampIndex, debounce, formatHitLabel } from "./search-helpers.js";

const TYPE_LABEL = {
  building: "楼栋",
  community: "小区",
  district: "区",
};

export function initSearch({ root, store }) {
  const overlay = root.querySelector('[data-component="search-overlay"]');
  const backdrop = root.querySelector('[data-component="search-backdrop"]');
  const closeBtn = overlay.querySelector('[data-role="search-close"]');
  const inputEl = overlay.querySelector('[data-role="search-input"]');
  const resultsEl = overlay.querySelector('[data-role="search-results"]');
  const statusEl = overlay.querySelector('[data-role="search-status"]');

  let lastOpen = false;
  let activeIndex = 0;
  let results = [];
  let queryToken = 0;

  closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  inputEl.addEventListener("input", () => {
    activeIndex = 0;
    debouncedSearch(inputEl.value);
  });
  inputEl.addEventListener("keydown", handleInputKey);
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !lastOpen) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    close();
  });
  resultsEl.addEventListener("click", (event) => {
    const row = event.target.closest("[data-row-index]");
    if (!row) return;
    const idx = Number(row.dataset.rowIndex);
    selectIndex(idx);
  });

  store.subscribe(handleStateChange);
  handleStateChange(store.get());

  function handleStateChange(state) {
    const open = !!state.searchOpen;
    if (open === lastOpen) return;
    lastOpen = open;
    overlay.dataset.open = open ? "true" : "false";
    backdrop.dataset.open = open ? "true" : "false";
    overlay.setAttribute("aria-hidden", open ? "false" : "true");
    if (open) {
      inputEl.value = "";
      results = [];
      activeIndex = 0;
      renderResults();
      statusEl.textContent = "输入后按 ↑↓ 选择，Enter 打开";
      overlay.focus();
      // Focus on next tick so the modal is visible first.
      setTimeout(() => inputEl.focus(), 30);
    }
  }

  const debouncedSearch = debounce((q) => {
    void runSearch(q);
  }, 180);

  async function runSearch(q) {
    const myToken = ++queryToken;
    if (!q.trim()) {
      results = [];
      renderResults();
      statusEl.textContent = "输入后按 ↑↓ 选择，Enter 打开";
      return;
    }
    statusEl.textContent = "搜索中…";
    try {
      const data = await api.search(q);
      if (myToken !== queryToken) return;
      results = data.items || [];
      activeIndex = 0;
      renderResults();
      statusEl.textContent = results.length
        ? `${results.length} 条结果 · Enter 打开 · Esc 关闭`
        : "未找到匹配项，可减少关键词或直接按区域筛选。";
    } catch (err) {
      if (myToken !== queryToken) return;
      console.error("[atlas:search] query failed", err);
      statusEl.textContent = `搜索失败：${err.message}`;
    }
  }

  function handleInputKey(event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = clampIndex(activeIndex + 1, results.length);
      renderResults();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = clampIndex(activeIndex - 1, results.length);
      renderResults();
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (results.length === 0) return;
      selectIndex(activeIndex);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  }

  function selectIndex(idx) {
    if (idx < 0 || idx >= results.length) return;
    const hit = results[idx];
    if (!hit || !hit.target_id) return;
    store.set({
      selection: {
        type: hit.target_type,
        id: hit.target_id,
        props: {
          name: hit.target_name,
          districtName: hit.district_name,
        },
      },
      searchOpen: false,
    });
  }

  function close() {
    if (!lastOpen) return;
    store.set({ searchOpen: false });
  }

  function renderResults() {
    if (results.length === 0) {
      resultsEl.innerHTML = "";
      return;
    }
    resultsEl.innerHTML = results
      .map((hit, idx) => renderRow(hit, idx))
      .join("");
  }

  function renderRow(hit, idx) {
    const selected = idx === activeIndex;
    const kindLabel = TYPE_LABEL[hit.target_type] || hit.target_type || "";
    return `<li class="atlas-search-row" data-row-index="${idx}" aria-selected="${selected ? "true" : "false"}"><span class="label">${escapeText(formatHitLabel(hit))}</span><span class="kind">${escapeText(kindLabel)}</span></li>`;
  }
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}
