import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";
import { initDrawer } from "./detail-drawer.js";
import { initFilterBar } from "./filter-bar.js";
import { createStorage } from "./storage.js";
import { MODES, defaultFiltersFor } from "./modes.js";
import { initOnboarding } from "./home-onboarding.js";
import { isPrefsEmpty } from "./user-prefs-helpers.js";
import { api } from "./api.js";

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
    userPrefs: null,
    onboardingOpen: false,
  });

  // Fire-and-forget: prefetch the user prefs (needed by the home onboarding
  // gate). Failures are non-fatal — the user can still click 偏好 to open
  // the modal and try again.
  api.userPrefs
    .get()
    .then((prefs) => store.set({ userPrefs: prefs }))
    .catch((err) => console.warn("[atlas] user prefs prefetch failed", err));

  let lastSerializedFilters = JSON.stringify(initialFilters);
  store.subscribe((state) => {
    const next = JSON.stringify(state.filters);
    if (next === lastSerializedFilters) return;
    lastSerializedFilters = next;
    filtersStorage.write(state.filters);
  });

  initShell({ root, store });
  initOnboarding({ root, store });

  // Auto-open the onboarding modal when a fresh user lands on home mode AND
  // user prefs have been hydrated (otherwise we can't tell empty-from-unloaded).
  // Fire on either mode-change or prefs-hydration transitions.
  let lastMode = store.get().mode;
  let prefsHydrated = store.get().userPrefs !== null && store.get().userPrefs !== undefined;
  store.subscribe((state) => {
    const modeChanged = state.mode !== lastMode;
    const prefsLoadedNow = state.userPrefs !== null && state.userPrefs !== undefined;
    const prefsJustHydrated = !prefsHydrated && prefsLoadedNow;
    if (modeChanged) lastMode = state.mode;
    if (prefsJustHydrated) prefsHydrated = true;
    if (
      (modeChanged || prefsJustHydrated) &&
      state.mode === "home" &&
      prefsLoadedNow &&
      isPrefsEmpty(state.userPrefs) &&
      !state.onboardingOpen
    ) {
      store.set({ onboardingOpen: true });
    }
  });

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
