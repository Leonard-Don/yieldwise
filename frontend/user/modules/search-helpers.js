export function clampIndex(index, count) {
  if (!count || count <= 0) return 0;
  if (index < 0) return 0;
  if (index >= count) return count - 1;
  return index;
}

export function formatHitLabel(hit) {
  if (!hit) return "";
  const name = hit.target_name || "";
  if (!name) return "";
  const district = hit.district_name;
  if (district && district !== name) {
    return `${district} · ${name}`;
  }
  return name;
}

export function debounce(fn, ms) {
  let handle = null;
  return function debounced(...args) {
    if (handle !== null) clearTimeout(handle);
    handle = setTimeout(() => {
      handle = null;
      fn.apply(this, args);
    }, ms);
  };
}
