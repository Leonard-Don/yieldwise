export function isStarred(items, targetId) {
  if (!Array.isArray(items)) return false;
  for (const entry of items) {
    if (entry && entry.target_id === targetId) return true;
  }
  return false;
}

export function watchlistCount(items) {
  return Array.isArray(items) ? items.length : 0;
}
