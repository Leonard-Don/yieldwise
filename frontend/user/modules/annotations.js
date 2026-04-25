import { api } from "./api.js";
import { sortByCreatedDesc, targetKey } from "./annotations-helpers.js";

export function initAnnotations({ root, store }) {
  const section = root.querySelector('[data-component="notes-section"]');
  const listEl = section.querySelector('[data-role="notes-list"]');
  const statusEl = section.querySelector('[data-role="notes-status"]');
  const addForm = section.querySelector('[data-role="notes-add"]');
  const addInput = section.querySelector('[data-role="notes-add-input"]');
  const addSubmit = section.querySelector('[data-role="notes-add-submit"]');

  let editingNoteId = null;
  let editingDraft = "";

  addInput.addEventListener("input", () => {
    addSubmit.disabled = addInput.value.trim().length === 0;
  });
  addForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitAdd();
  });
  listEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    const noteId = button.dataset.noteId;
    if (action === "edit") startEdit(noteId);
    else if (action === "delete") void deleteNote(noteId);
    else if (action === "save") void saveEdit(noteId);
    else if (action === "cancel") cancelEdit();
  });
  listEl.addEventListener("input", (event) => {
    const textarea = event.target.closest("textarea[data-role='note-edit-input']");
    if (!textarea) return;
    editingDraft = textarea.value;
  });

  let lastTarget = null;
  store.subscribe(handleStateChange);
  handleStateChange(store.get());

  function handleStateChange(state) {
    const key = targetKey(state.selection);
    if (key !== lastTarget) {
      lastTarget = key;
      cancelEdit();
      if (key === null) {
        section.hidden = true;
        return;
      }
      section.hidden = false;
      const cache = state.annotationsByTarget || {};
      if (Array.isArray(cache[key])) {
        renderNotes(cache[key]);
      } else {
        statusEl.textContent = "加载中…";
        statusEl.removeAttribute("data-state");
        listEl.innerHTML = "";
        void loadFor(key);
      }
      return;
    }
    if (key !== null) {
      const cache = state.annotationsByTarget || {};
      if (Array.isArray(cache[key])) {
        renderNotes(cache[key]);
      }
    }
  }

  async function loadFor(targetId) {
    try {
      const data = await api.annotations.listForTarget(targetId);
      writeCache(targetId, data.items || []);
    } catch (err) {
      console.error("[atlas:notes] load failed", err);
      statusEl.textContent = `加载失败：${err.message}`;
      statusEl.dataset.state = "error";
    }
  }

  function writeCache(targetId, items) {
    const current = store.get().annotationsByTarget || {};
    store.set({
      annotationsByTarget: { ...current, [targetId]: items },
    });
  }

  async function submitAdd() {
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    const body = addInput.value.trim();
    if (!body) return;
    statusEl.textContent = "保存中…";
    statusEl.removeAttribute("data-state");
    try {
      const note = await api.annotations.create(key, sel.type, body);
      const current = store.get().annotationsByTarget || {};
      const prior = Array.isArray(current[key]) ? current[key] : [];
      writeCache(key, [...prior, note]);
      addInput.value = "";
      addSubmit.disabled = true;
      statusEl.textContent = `${prior.length + 1} 条`;
    } catch (err) {
      console.error("[atlas:notes] create failed", err);
      statusEl.textContent = `保存失败：${err.message}`;
      statusEl.dataset.state = "error";
    }
  }

  async function deleteNote(noteId) {
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    statusEl.textContent = "删除中…";
    statusEl.removeAttribute("data-state");
    const current = store.get().annotationsByTarget || {};
    const prior = Array.isArray(current[key]) ? current[key] : [];
    const optimistic = prior.filter((it) => it.note_id !== noteId);
    writeCache(key, optimistic);
    try {
      await api.annotations.remove(noteId);
      statusEl.textContent = `${optimistic.length} 条`;
    } catch (err) {
      console.error("[atlas:notes] delete failed", err);
      statusEl.textContent = `删除失败：${err.message}`;
      statusEl.dataset.state = "error";
      writeCache(key, prior);
    }
  }

  function startEdit(noteId) {
    editingNoteId = noteId;
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    const items = (store.get().annotationsByTarget || {})[key] || [];
    const note = items.find((it) => it.note_id === noteId);
    editingDraft = note ? note.body : "";
    renderNotes(items);
  }

  function cancelEdit() {
    if (editingNoteId === null) return;
    editingNoteId = null;
    editingDraft = "";
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (key) {
      const items = (store.get().annotationsByTarget || {})[key] || [];
      renderNotes(items);
    }
  }

  async function saveEdit(noteId) {
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    const body = editingDraft.trim();
    if (!body) {
      statusEl.textContent = "笔记内容不能为空";
      statusEl.dataset.state = "error";
      return;
    }
    statusEl.textContent = "保存中…";
    statusEl.removeAttribute("data-state");
    try {
      const updated = await api.annotations.update(noteId, body);
      const current = store.get().annotationsByTarget || {};
      const prior = Array.isArray(current[key]) ? current[key] : [];
      writeCache(
        key,
        prior.map((it) => (it.note_id === noteId ? updated : it)),
      );
      editingNoteId = null;
      editingDraft = "";
      statusEl.textContent = `${prior.length} 条`;
    } catch (err) {
      console.error("[atlas:notes] update failed", err);
      statusEl.textContent = `保存失败：${err.message}`;
      statusEl.dataset.state = "error";
    }
  }

  function renderNotes(items) {
    const sorted = sortByCreatedDesc(items);
    if (sorted.length === 0) {
      listEl.innerHTML = `<li class="atlas-notes-empty">还没有笔记 — 在下方添加第一条</li>`;
      statusEl.textContent = "0 条";
      return;
    }
    listEl.innerHTML = sorted
      .map((note) => renderCard(note))
      .join("");
    statusEl.textContent = `${sorted.length} 条`;
  }

  function renderCard(note) {
    if (note.note_id === editingNoteId) {
      return `<li class="atlas-note-card"><div class="atlas-note-edit"><textarea data-role="note-edit-input">${escapeText(editingDraft)}</textarea><div class="atlas-note-actions"><button type="button" data-action="save" data-note-id="${escapeAttr(note.note_id)}">保存</button><button type="button" data-action="cancel">取消</button></div></div></li>`;
    }
    const time = note.updated_at || note.created_at || "";
    return `<li class="atlas-note-card"><pre class="atlas-note-body">${escapeText(note.body)}</pre><div class="atlas-note-meta">${escapeText(time)}</div><div class="atlas-note-actions"><button type="button" data-action="edit" data-note-id="${escapeAttr(note.note_id)}">编辑</button><button type="button" data-action="delete" data-note-id="${escapeAttr(note.note_id)}" data-variant="danger">删除</button></div></li>`;
  }
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function escapeAttr(value) {
  return escapeText(value).replace(/'/g, "&#39;");
}
