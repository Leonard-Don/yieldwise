function defaultBackend() {
  if (typeof window === "undefined" || !window.localStorage) {
    return null;
  }
  try {
    // Probe — Safari private mode throws here.
    window.localStorage.setItem("__atlas_probe__", "1");
    window.localStorage.removeItem("__atlas_probe__");
    return window.localStorage;
  } catch {
    return null;
  }
}

export function createStorage(key, { backend } = {}) {
  const target = backend === undefined ? defaultBackend() : backend;

  function read() {
    if (!target) return null;
    let raw;
    try {
      raw = target.getItem(key);
    } catch {
      return null;
    }
    if (raw === null || raw === undefined) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function write(value) {
    if (!target) return;
    try {
      target.setItem(key, JSON.stringify(value));
    } catch {
      /* quota / private-mode — silently drop */
    }
  }

  function clear() {
    if (!target) return;
    try {
      target.removeItem(key);
    } catch {
      /* nothing to do */
    }
  }

  return { read, write, clear };
}
