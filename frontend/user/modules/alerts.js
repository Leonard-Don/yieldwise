import { api } from "./api.js";
import { formatAlertLine, severityFor } from "./alerts-helpers.js";

export function initAlerts({ root, store }) {
  const banner = root.querySelector('[data-component="alerts-banner"]');
  const countEl = banner.querySelector('[data-role="banner-count"]');
  const sinceEl = banner.querySelector('[data-role="banner-since"]');
  const toggleBtn = banner.querySelector('[data-role="banner-toggle"]');
  const markBtn = banner.querySelector('[data-role="banner-mark"]');
  const listEl = banner.querySelector('[data-role="banner-list"]');

  let expanded = false;

  toggleBtn.addEventListener("click", () => {
    expanded = !expanded;
    listEl.hidden = !expanded;
    toggleBtn.textContent = expanded ? "收起" : "展开";
    toggleBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
  });

  markBtn.addEventListener("click", () => {
    void markSeen();
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const alerts = state.alerts || { items: [], last_open_at: null };
    const items = Array.isArray(alerts.items) ? alerts.items : [];
    if (items.length === 0) {
      banner.hidden = true;
      expanded = false;
      listEl.hidden = true;
      toggleBtn.textContent = "展开";
      toggleBtn.setAttribute("aria-expanded", "false");
      return;
    }
    banner.hidden = false;
    countEl.textContent = `${items.length} 条变化`;
    sinceEl.textContent = alerts.last_open_at
      ? `自 ${alerts.last_open_at} 起`
      : "首次扫描";
    listEl.innerHTML = items
      .map((alert) => renderRow(alert))
      .join("");
    listEl.hidden = !expanded;
  }

  function renderRow(alert) {
    const severity = severityFor(alert);
    const display = alert.target_name || alert.target_id || "";
    return `<li class="atlas-banner-row" data-severity="${escapeAttr(severity)}"><span class="atlas-banner-target" title="${escapeAttr(alert.target_id || "")}">${escapeText(display)}</span><span class="atlas-banner-line">${escapeText(formatAlertLine(alert))}</span></li>`;
  }

  async function markSeen() {
    const before = store.get().alerts;
    markBtn.disabled = true;
    toggleBtn.disabled = true;
    // Optimistic clear
    store.set({ alerts: { items: [], last_open_at: before?.last_open_at ?? null } });
    try {
      await api.alerts.markSeen();
    } catch (err) {
      console.error("[atlas:alerts] mark-seen failed", err);
      try {
        const fresh = await api.alerts.sinceLastOpen();
        store.set({
          alerts: {
            items: fresh.items || [],
            last_open_at: fresh.last_open_at || null,
          },
        });
      } catch (refetchErr) {
        console.error("[atlas:alerts] refetch failed", refetchErr);
        // Restore previous state so the banner remains usable.
        store.set({ alerts: before });
      }
    } finally {
      markBtn.disabled = false;
      toggleBtn.disabled = false;
    }
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

function escapeAttr(value) {
  return escapeText(value).replace(/'/g, "&#39;");
}
