const SIGNAL_KEYS = ["budget_min_wan", "budget_max_wan", "area_min_sqm", "area_max_sqm"];

export function isPrefsEmpty(prefs) {
  if (!prefs || typeof prefs !== "object") return true;
  for (const key of SIGNAL_KEYS) {
    const value = prefs[key];
    if (value !== null && value !== undefined && value !== "") return false;
  }
  const districts = prefs.districts;
  if (Array.isArray(districts) && districts.length > 0) return false;
  return true;
}
