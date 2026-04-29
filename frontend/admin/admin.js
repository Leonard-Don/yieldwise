const usersEl = document.querySelector('[data-role="users"]');
const meEl = document.querySelector('[data-role="me-name"]');
const addForm = document.getElementById("add-user-form");
const addError = document.querySelector('[data-role="add-error"]');
const logoutBtn = document.querySelector('[data-role="logout"]');

async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, { credentials: "same-origin", ...opts });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`${r.status} ${text}`);
  }
  return r.json();
}

async function loadMe() {
  const me = await fetchJSON("/api/auth/whoami");
  meEl.textContent = `${me.username} (${me.role})`;
}

async function loadUsers() {
  const users = await fetchJSON("/api/auth/admin/users");
  usersEl.innerHTML = "";
  for (const u of users) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHTML(u.username)}</td>
      <td>${escapeHTML(u.role)}</td>
      <td>${u.disabled ? "<em>已禁用</em>" : "<span>启用</span>"}</td>
      <td></td>
    `;
    const actions = tr.querySelector("td:last-child");
    actions.appendChild(makeRoleSelector(u));
    actions.appendChild(makeToggleBtn(u));
    actions.appendChild(makeRotatePwBtn(u));
    usersEl.appendChild(tr);
  }
}

function makeRoleSelector(u) {
  const sel = document.createElement("select");
  for (const role of ["viewer", "analyst", "admin"]) {
    const opt = document.createElement("option");
    opt.value = role;
    opt.textContent = role;
    if (role === u.role) opt.selected = true;
    sel.appendChild(opt);
  }
  sel.addEventListener("change", async () => {
    await patchUser(u.id, { role: sel.value });
    await loadUsers();
  });
  return sel;
}

function makeToggleBtn(u) {
  const btn = document.createElement("button");
  btn.textContent = u.disabled ? "启用" : "禁用";
  btn.addEventListener("click", async () => {
    await patchUser(u.id, { disabled: !u.disabled });
    await loadUsers();
  });
  return btn;
}

function makeRotatePwBtn(u) {
  const btn = document.createElement("button");
  btn.textContent = "改密";
  btn.addEventListener("click", async () => {
    const pw = window.prompt(`为 ${u.username} 设置新密码（≥8 字符）：`);
    if (!pw) return;
    if (pw.length < 8) {
      window.alert("密码至少 8 字符");
      return;
    }
    await patchUser(u.id, { password: pw });
    window.alert("密码已更新");
  });
  return btn;
}

async function patchUser(id, payload) {
  await fetchJSON(`/api/auth/admin/users/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
}

addForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  addError.hidden = true;
  const data = new FormData(addForm);
  const payload = {
    username: data.get("username"),
    password: data.get("password"),
    role: data.get("role"),
  };
  try {
    await fetchJSON("/api/auth/admin/users", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    addForm.reset();
    await loadUsers();
  } catch (err) {
    addError.textContent = err.message;
    addError.hidden = false;
  }
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  window.location.href = "/login";
});

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

(async () => {
  try {
    await loadMe();
    await loadUsers();
  } catch (err) {
    if (err.message.startsWith("401") || err.message.startsWith("403")) {
      window.location.href = "/login";
      return;
    }
    addError.textContent = `加载失败：${err.message}`;
    addError.hidden = false;
  }
})();
