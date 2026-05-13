export function createStore(initial = {}) {
  let state = { ...initial };
  const listeners = new Set();

  function get() {
    return state;
  }

  function set(patch) {
    let changed = false;
    const next = { ...state };
    if (patch.onboardingOpen === true) {
      next.helpOpen = false;
      next.searchOpen = false;
      next.selection = null;
    }
    if (patch.searchOpen === true) {
      next.helpOpen = false;
      next.onboardingOpen = false;
      next.selection = null;
    }
    if (patch.helpOpen === true) {
      next.searchOpen = false;
      next.onboardingOpen = false;
      next.selection = null;
    }
    for (const key of Object.keys(patch)) {
      if (!Object.is(state[key], patch[key])) {
        next[key] = patch[key];
        changed = true;
      }
    }
    for (const key of ["helpOpen", "searchOpen", "onboardingOpen", "selection"]) {
      if (!Object.is(state[key], next[key])) {
        changed = true;
      }
    }
    if (!changed) return;
    state = next;
    for (const listener of listeners) {
      listener(state);
    }
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  function select(selector) {
    return selector(state);
  }

  return { get, set, subscribe, select };
}
