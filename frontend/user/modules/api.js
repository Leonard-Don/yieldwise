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

export const api = {
  opportunities: (params) => getJSON(`/api/v2/opportunities${buildQuery(params)}`),
  mapBuildings: (params) => getJSON(`/api/v2/map/buildings${buildQuery(params)}`),
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  runtimeConfig: () => getJSON("/api/runtime-config"),
  invalidate,
};
