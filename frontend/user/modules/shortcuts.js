import { api } from "./api.js";
import { parseShortcut } from "./shortcuts-helpers.js";

const VALID_MODES = new Set(["yield", "home", "city"]);

export function initShortcuts({ root, store }) {
  const overlay = root.querySelector('[data-component="help-overlay"]');
  const backdrop = root.querySelector('[data-component="help-backdrop"]');
  const closeBtn = overlay.querySelector('[data-role="help-close"]');
  const chipBtn = root.querySelector('[data-component="help-chip"]');

  document.addEventListener("keydown", handleKeyDown);
  closeBtn.addEventListener("click", () => store.set({ helpOpen: false }));
  backdrop.addEventListener("click", () => store.set({ helpOpen: false }));
  if (chipBtn) {
    chipBtn.addEventListener("click", () => {
      store.set({ helpOpen: !store.get().helpOpen });
    });
  }

  store.subscribe(renderOverlay);
  renderOverlay(store.get());

  function renderOverlay(state) {
    const open = !!state.helpOpen;
    overlay.dataset.open = open ? "true" : "false";
    backdrop.dataset.open = open ? "true" : "false";
    overlay.setAttribute("aria-hidden", open ? "false" : "true");
  }

  function handleKeyDown(event) {
    // Esc always closes the help overlay if it's open. Other Esc semantics
    // (drawer / onboarding) are owned by their own modules.
    if (event.key === "Escape" && store.get().helpOpen) {
      event.preventDefault();
      store.set({ helpOpen: false });
      return;
    }
    const action = parseShortcut(event);
    if (!action) return;
    event.preventDefault();
    if (VALID_MODES.has(action)) {
      switchMode(action);
    } else if (action === "star") {
      void toggleStar();
    } else if (action === "note") {
      focusNoteInput();
    } else if (action === "help") {
      store.set({ helpOpen: !store.get().helpOpen });
    }
  }

  function switchMode(modeId) {
    if (store.get().mode === modeId) return;
    store.set({ mode: modeId });
    const params = new URLSearchParams(window.location.search);
    params.set("mode", modeId);
    window.history.replaceState({}, "", `${window.location.pathname}?${params.toString()}`);
  }

  function focusNoteInput() {
    const input = root.querySelector('[data-role="notes-add-input"]');
    if (!input) return;
    input.focus();
  }

  async function toggleStar() {
    const state = store.get();
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) return;
    const items = Array.isArray(state.watchlist) ? state.watchlist : [];
    const isStarred = items.some((it) => it.target_id === sel.id);
    try {
      if (isStarred) {
        const next = items.filter((it) => it.target_id !== sel.id);
        store.set({ watchlist: next });
        await api.watchlist.remove(sel.id);
      } else {
        const optimistic = {
          target_id: sel.id,
          target_type: sel.type,
          added_at: new Date().toISOString().slice(0, 19),
          last_seen_snapshot: null,
        };
        store.set({ watchlist: [...items, optimistic] });
        const saved = await api.watchlist.add(sel.id, sel.type);
        const merged = store
          .get()
          .watchlist.map((it) => (it.target_id === sel.id ? saved : it));
        store.set({ watchlist: merged });
      }
    } catch (err) {
      console.error("[atlas:shortcuts] star toggle failed", err);
      try {
        const fresh = await api.watchlist.list();
        store.set({ watchlist: fresh.items || [] });
      } catch (refetchErr) {
        console.error("[atlas:shortcuts] watchlist refetch failed", refetchErr);
      }
    }
  }
}
