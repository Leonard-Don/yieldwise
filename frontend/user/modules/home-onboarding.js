import { api } from "./api.js";
import { resolveDefaultFilters } from "./modes.js";

export function initOnboarding({ root, store }) {
  const modal = root.querySelector('[data-component="onboarding"]');
  const backdrop = root.querySelector('[data-component="onboarding-backdrop"]');
  const closeBtn = modal.querySelector('[data-role="onboarding-close"]');
  const form = modal.querySelector('[data-role="onboarding-form"]');
  const submitBtn = modal.querySelector('[data-role="onboarding-submit"]');
  const statusEl = modal.querySelector('[data-role="onboarding-status"]');
  const districtsEl = modal.querySelector('[data-role="onboarding-districts"]');
  const inputs = {
    budget_min_wan: form.elements.namedItem("budget_min_wan"),
    budget_max_wan: form.elements.namedItem("budget_max_wan"),
    area_min_sqm: form.elements.namedItem("area_min_sqm"),
    area_max_sqm: form.elements.namedItem("area_max_sqm"),
  };

  let districtIds = [];
  let selectedDistricts = new Set();

  closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.dataset.open === "true") {
      event.preventDefault();
      event.stopImmediatePropagation();
      close();
    }
  });
  form.addEventListener("input", refreshSubmitState);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submit().catch((err) => showError(err.message || "保存失败"));
  });

  store.subscribe(handleStateChange);
  loadDistricts();
  handleStateChange(store.get());

  function handleStateChange(state) {
    if (state.onboardingOpen) {
      open(state.userPrefs);
    } else {
      close();
    }
  }

  function open(prefs) {
    seedForm(prefs || {});
    modal.dataset.open = "true";
    backdrop.dataset.open = "true";
    modal.setAttribute("aria-hidden", "false");
    statusEl.textContent = "偏好仅保存在本机，可随时修改。";
    statusEl.removeAttribute("data-state");
    refreshSubmitState();
    modal.focus();
    inputs.budget_max_wan.focus();
  }

  function close() {
    if (modal.dataset.open !== "true" && backdrop.dataset.open !== "true") return;
    modal.dataset.open = "false";
    backdrop.dataset.open = "false";
    modal.setAttribute("aria-hidden", "true");
    if (store.get().onboardingOpen) {
      store.set({ onboardingOpen: false });
    }
  }

  function seedForm(prefs) {
    inputs.budget_min_wan.value = numericString(prefs.budget_min_wan);
    inputs.budget_max_wan.value = numericString(prefs.budget_max_wan);
    inputs.area_min_sqm.value = numericString(prefs.area_min_sqm);
    inputs.area_max_sqm.value = numericString(prefs.area_max_sqm);
    selectedDistricts = new Set(Array.isArray(prefs.districts) ? prefs.districts : []);
    renderDistricts();
  }

  async function loadDistricts() {
    try {
      const data = await api.districtsAll();
      const items = data.districts || [];
      districtIds = items.map((d) => ({ id: d.id, name: d.name || d.short || d.id }));
      renderDistricts();
    } catch (err) {
      districtsEl.textContent = `区域列表加载失败：${err.message}`;
    }
  }

  function renderDistricts() {
    if (!districtIds.length) {
      districtsEl.textContent = "区域加载中…";
      return;
    }
    districtsEl.innerHTML = districtIds
      .map(
        (d) =>
          `<button type="button" class="atlas-onboarding-district-chip" data-district-id="${escapeAttr(d.id)}" aria-pressed="${selectedDistricts.has(d.id) ? "true" : "false"}">${escapeText(d.name)}</button>`,
      )
      .join("");
    districtsEl.querySelectorAll("[data-district-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.districtId;
        if (selectedDistricts.has(id)) selectedDistricts.delete(id);
        else selectedDistricts.add(id);
        btn.setAttribute("aria-pressed", selectedDistricts.has(id) ? "true" : "false");
        refreshSubmitState();
      });
    });
  }

  function refreshSubmitState() {
    const ok = inputs.budget_max_wan.value && Number(inputs.budget_max_wan.value) > 0;
    submitBtn.disabled = !ok;
  }

  function showError(message) {
    statusEl.textContent = message;
    statusEl.dataset.state = "error";
  }

  async function submit() {
    statusEl.textContent = "保存中…";
    statusEl.removeAttribute("data-state");
    const payload = {
      budget_min_wan: numericValue(inputs.budget_min_wan.value),
      budget_max_wan: numericValue(inputs.budget_max_wan.value),
      area_min_sqm: numericValue(inputs.area_min_sqm.value),
      area_max_sqm: numericValue(inputs.area_max_sqm.value),
      districts: [...selectedDistricts],
    };
    const saved = await api.userPrefs.patch(payload);
    // Seed the home-mode filter slice so the chip bar immediately reflects
    // the saved prefs (otherwise filter-bar shows "无筛选" while the board
    // is silently filtered through the resolver fallback in loadFor).
    const currentFilters = store.get().filters || {};
    const homeFilters = resolveDefaultFilters("home", saved);
    store.set({
      userPrefs: saved,
      onboardingOpen: false,
      filters: { ...currentFilters, home: homeFilters },
    });
  }
}

function numericString(value) {
  if (value === null || value === undefined || value === "") return "";
  return String(value);
}

function numericValue(raw) {
  if (raw === null || raw === undefined || raw === "") return null;
  const num = Number(raw);
  return Number.isNaN(num) ? null : num;
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function escapeAttr(value) {
  return escapeText(value).replace(/'/g, "&#39;");
}
