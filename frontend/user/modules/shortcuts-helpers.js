const MODE_BY_DIGIT = { "1": "yield", "2": "home", "3": "city" };

function isEditableTarget(target) {
  if (!target) return false;
  const tag = (target.tagName || "").toUpperCase();
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return false;
}

export function parseShortcut(event) {
  if (!event) return null;
  const { key, metaKey, ctrlKey, shiftKey, altKey, target } = event;
  const modKey = metaKey || ctrlKey;

  // Mode switch is privileged: works even when typing in a form field.
  if (modKey && !altKey && Object.prototype.hasOwnProperty.call(MODE_BY_DIGIT, key)) {
    return MODE_BY_DIGIT[key];
  }

  // All other shortcuts are suppressed inside editable targets.
  if (isEditableTarget(target)) return null;

  // Modifier-bearing letters are reserved for the browser (Cmd+F / Ctrl+N etc.).
  if (modKey || altKey) return null;

  // The ? glyph: most browsers report event.key === "?" directly, but some
  // keyboard layouts / automation tools send key === "/" with shiftKey set.
  // Accept both so the help shortcut is reliable across environments.
  if (key === "?") return "help";
  if (key === "/" && shiftKey) return "help";

  const lower = typeof key === "string" ? key.toLowerCase() : "";
  if (lower === "f") return "star";
  if (lower === "n") return "note";

  return null;
}
