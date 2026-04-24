import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";
import { initDrawer } from "./detail-drawer.js";
import { initFilterBar } from "./filter-bar.js";
import { createStorage } from "./storage.js";
import { MODES, defaultFiltersFor } from "./modes.js";

const root = document.querySelector('[data-user-shell="atlas"]');
if (!root) {
  console.error("[atlas] user shell root not found");
} else {
  bootstrap(root).catch((err) => {
    console.error("[atlas] bootstrap failed", err);
  });
}

async function bootstrap(root) {
  const filtersStorage = createStorage("atlas:filters:v1");
  const persistedFilters = filtersStorage.read() || {};
  const initialFilters = {};
  for (const mode of MODES) {
    initialFilters[mode.id] = persistedFilters[mode.id] || defaultFiltersFor(mode.id);
  }

  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
  });

  let lastSerializedFilters = JSON.stringify(initialFilters);
  store.subscribe((state) => {
    const next = JSON.stringify(state.filters);
    if (next === lastSerializedFilters) return;
    lastSerializedFilters = next;
    filtersStorage.write(state.filters);
  });

  initShell({ root, store });
  initDrawer({ root, store });
  initFilterBar({ root, store });

  const mapContainer = root.querySelector('[data-component="map"]');
  const boardContainer = root.querySelector('[data-component="board"]');

  // Map and board boot in parallel — they only talk via the store.
  await Promise.all([
    initMap({ container: mapContainer, store }),
    initBoard({ container: boardContainer, store }),
  ]);

  console.info("[atlas] user shell ready");
}
