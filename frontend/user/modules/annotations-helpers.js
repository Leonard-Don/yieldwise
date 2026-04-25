export function sortByCreatedDesc(items) {
  if (!Array.isArray(items)) return [];
  return [...items].sort((a, b) => {
    const av = (a && a.created_at) || "";
    const bv = (b && b.created_at) || "";
    if (av === bv) return 0;
    if (!av) return 1;
    if (!bv) return -1;
    return av > bv ? -1 : 1;
  });
}

export function targetKey(sel) {
  if (!sel || (sel.type !== "building" && sel.type !== "community")) {
    return null;
  }
  return sel.id;
}
