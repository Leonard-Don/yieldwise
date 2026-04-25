import { api } from "./api.js";
import { isStarred, watchlistCount } from "./watchlist-helpers.js";

export function initWatchlist({ root, store }) {
  const countEl = root.querySelector('[data-component="watchlist-count"]');
  const starButton = root.querySelector('[data-component="drawer-star"]');

  starButton.addEventListener("click", () => {
    void toggleStar();
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const items = state.watchlist;
    if (!Array.isArray(items)) {
      countEl.textContent = "★ —";
      countEl.removeAttribute("data-active");
    } else {
      countEl.textContent = `★ ${watchlistCount(items)}`;
      countEl.setAttribute("data-active", items.length > 0 ? "true" : "false");
    }
    syncStarButton(state);
  }

  function syncStarButton(state) {
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) {
      starButton.hidden = true;
      starButton.setAttribute("aria-pressed", "false");
      return;
    }
    starButton.hidden = false;
    starButton.disabled = false;
    starButton.setAttribute(
      "aria-pressed",
      isStarred(state.watchlist, sel.id) ? "true" : "false",
    );
  }

  async function toggleStar() {
    const state = store.get();
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) return;
    const items = Array.isArray(state.watchlist) ? state.watchlist : [];
    const currentlyStarred = isStarred(items, sel.id);
    starButton.disabled = true;
    try {
      if (currentlyStarred) {
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
        const next = store
          .get()
          .watchlist.map((it) => (it.target_id === sel.id ? saved : it));
        store.set({ watchlist: next });
      }
    } catch (err) {
      console.error("[atlas:watchlist] toggle failed", err);
      // Roll back to whatever the server says.
      try {
        const fresh = await api.watchlist.list();
        store.set({ watchlist: fresh.items || [] });
      } catch (refetchErr) {
        console.error("[atlas:watchlist] refetch failed", refetchErr);
      }
    } finally {
      starButton.disabled = false;
    }
  }
}
