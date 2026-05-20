import { createStore } from "./state.js";
import { initShell } from "./shell.js?v=20260519-no-notes";
import { initMap } from "./map.js?v=20260519-no-notes";
import { initBoard } from "./opportunity-board.js?v=20260520-board-layout";
import { initDrawer } from "./detail-drawer.js";
import { initFilterBar } from "./filter-bar.js?v=20260519-no-notes";
import { createStorage } from "./storage.js";
import { MODES, normalizeInitialFiltersFor } from "./modes.js?v=20260519-no-notes";
import { initOnboarding } from "./home-onboarding.js?v=20260519-no-notes";
import { initWatchlist } from "./watchlist.js";
import { initAlerts } from "./alerts.js";
import { initShortcuts } from "./shortcuts.js?v=20260519-no-notes";
import { initSearch } from "./search.js";
import { initComparison } from "./comparison.js?v=20260514-a11y";
import { initCandidateDesk } from "./candidate-desk.js";
import { normalizeComparisonItems } from "./comparison-helpers.js";
import { api } from "./api.js?v=20260519-no-notes";
import { bootstrapCityConfig } from "./config-bootstrap.js";

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
  const comparisonStorage = createStorage("atlas:comparison:v1");
  const persistedFilters = filtersStorage.read() || {};
  const persistedComparison = normalizeComparisonItems(comparisonStorage.read());
  const initialFilters = {};
  for (const mode of MODES) {
    const persistedForMode = persistedFilters[mode.id] || persistedFilters.home || persistedFilters.city;
    initialFilters[mode.id] = normalizeInitialFiltersFor(mode.id, persistedForMode);
  }
  if (JSON.stringify(initialFilters) !== JSON.stringify(persistedFilters)) {
    filtersStorage.write(initialFilters);
  }

  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
    userPrefs: null,
    onboardingOpen: false,
    watchlist: [],
    alerts: { items: [], last_open_at: null },
    candidateDeskOpen: false,
    comparisonItems: persistedComparison,
    helpOpen: false,
    searchOpen: false,
  });

  // Fire-and-forget: preferences are optional filters for the single rent-sale
  // ratio workspace. Failures are non-fatal.
  api.userPrefs
    .get()
    .then((prefs) => store.set({ userPrefs: prefs }))
    .catch((err) => console.warn("[atlas] user prefs prefetch failed", err));

  api.watchlist
    .list()
    .then((data) => store.set({ watchlist: data.items || [] }))
    .catch((err) => console.warn("[atlas] watchlist prefetch failed", err));

  api.alerts
    .sinceLastOpen()
    .then((data) =>
      store.set({
        alerts: {
          items: data.items || [],
          last_open_at: data.last_open_at || null,
        },
      }),
    )
    .catch((err) => console.warn("[atlas] alerts prefetch failed", err));

  let lastSerializedFilters = JSON.stringify(initialFilters);
  store.subscribe((state) => {
    const next = JSON.stringify(state.filters);
    if (next === lastSerializedFilters) return;
    lastSerializedFilters = next;
    filtersStorage.write(state.filters);
  });

  initShell({ root, store });
  initOnboarding({ root, store });
  initWatchlist({ root, store });
  initAlerts({ root, store });
  initCandidateDesk({ root, store });
  initShortcuts({ root, store });
  initSearch({ root, store });
  initComparison({ root, store, storage: comparisonStorage });

  initDrawer({ root, store });
  initFilterBar({ root, store });

  const mapContainer = root.querySelector('[data-component="map"]');
  const boardContainer = root.querySelector('[data-component="board"]');

  // City manifest must be cached before initMap reads center/zoom.
  await bootstrapCityConfig();

  // Map and board boot in parallel — they only talk via the store.
  await Promise.all([
    initMap({ container: mapContainer, store }),
    initBoard({ container: boardContainer, store }),
  ]);

  console.info("[atlas] user shell ready");
}
