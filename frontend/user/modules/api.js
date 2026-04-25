const cache = new Map();

async function getJSON(url, { signal } = {}) {
  if (cache.has(url)) {
    return cache.get(url);
  }
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`API ${url} → ${response.status}`);
  }
  const body = await response.json();
  cache.set(url, body);
  return body;
}

function invalidate(prefix) {
  for (const key of [...cache.keys()]) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}

function buildQuery(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

async function getJSONFresh(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`API ${url} → ${response.status}`);
  return response.json();
}

async function patchJSON(url, payload) {
  const response = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${url} → ${response.status} ${text}`);
  }
  return response.json();
}

async function deleteJSON(url) {
  const response = await fetch(url, { method: "DELETE" });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${url} → ${response.status} ${text}`);
  }
  return response.json();
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${url} → ${response.status} ${text}`);
  }
  return response.json();
}

export const api = {
  opportunities: (params) => getJSON(`/api/v2/opportunities${buildQuery(params)}`),
  mapBuildings: (params) => getJSON(`/api/v2/map/buildings${buildQuery(params)}`),
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  districtsAll: () => getJSON("/api/v2/map/districts"),
  runtimeConfig: () => getJSON("/api/runtime-config"),
  userPrefs: {
    get: () => getJSONFresh("/api/v2/user/prefs"),
    patch: (payload) => patchJSON("/api/v2/user/prefs", payload),
  },
  watchlist: {
    list: () => getJSONFresh("/api/v2/watchlist"),
    add: (targetId, targetType) =>
      postJSON("/api/v2/watchlist", { target_id: targetId, target_type: targetType }),
    remove: (targetId) =>
      deleteJSON(`/api/v2/watchlist/${encodeURIComponent(targetId)}`),
  },
  invalidate,
};
