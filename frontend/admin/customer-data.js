const meEl = document.querySelector('[data-role="me-name"]');
const uploadForm = document.getElementById("upload-form");
const uploadErr = document.querySelector('[data-role="upload-error"]');
const runsBody = document.querySelector('[data-role="runs"]');
const errorsCard = document.querySelector('[data-role="errors-card"]');
const errorsBody = document.querySelector('[data-role="errors-body"]');
const logoutBtn = document.querySelector('[data-role="logout"]');

async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, { credentials: "same-origin", ...opts });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`${r.status} ${t}`);
  }
  return r.json();
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

async function loadMe() {
  const me = await fetchJSON("/api/auth/whoami");
  meEl.textContent = `${me.username} (${me.role})`;
  if (me.role === "viewer") {
    uploadForm.querySelector("button[type=submit]").disabled = true;
    uploadErr.textContent = "viewer 角色只读，无法上传";
    uploadErr.hidden = false;
  }
}

async function loadRuns() {
  const runs = await fetchJSON("/api/v2/customer-data/imports");
  runsBody.innerHTML = "";
  for (const run of runs) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHTML(run.runId)}</td>
      <td>${escapeHTML(run.type)}</td>
      <td>${run.rowCount}</td>
      <td>${run.errorCount}</td>
      <td>${escapeHTML(run.createdAt)}</td>
      <td></td>
    `;
    const actions = tr.querySelector("td:last-child");
    actions.appendChild(makePersistBtn(run));
    runsBody.appendChild(tr);
  }
}

function makePersistBtn(run) {
  const btn = document.createElement("button");
  btn.textContent = run.errorCount > 0 ? "持久化（含错误）" : "持久化";
  btn.addEventListener("click", async () => {
    const force = run.errorCount > 0
      ? window.confirm(`这次上传有 ${run.errorCount} 行解析失败。仍然持久化？`)
      : true;
    if (!force) return;
    try {
      const url = `/api/v2/customer-data/imports/${encodeURIComponent(run.runId)}/persist`
        + (run.errorCount > 0 ? "?force=true" : "");
      const result = await fetchJSON(url, { method: "POST" });
      window.alert(`已持久化 ${result.persisted_count} 行`);
    } catch (err) {
      window.alert(`持久化失败: ${err.message}`);
    }
  });
  return btn;
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  uploadErr.hidden = true;
  errorsCard.hidden = true;
  const data = new FormData(uploadForm);
  try {
    const r = await fetch("/api/v2/customer-data/imports", {
      method: "POST",
      credentials: "same-origin",
      body: data,
    });
    if (!r.ok) {
      const t = await r.text();
      uploadErr.textContent = `上传失败 (${r.status}): ${t.slice(0, 200)}`;
      uploadErr.hidden = false;
      return;
    }
    const body = await r.json();
    uploadForm.reset();
    if (body.errorsPreview && body.errorsPreview.length) {
      errorsBody.innerHTML = "";
      for (const e of body.errorsPreview) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${e.row_index}</td><td>${escapeHTML(JSON.stringify(e.error_messages))}</td>`;
        errorsBody.appendChild(tr);
      }
      errorsCard.hidden = false;
    }
    await loadRuns();
  } catch (err) {
    uploadErr.textContent = `网络错误: ${err.message}`;
    uploadErr.hidden = false;
  }
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  window.location.href = "/login";
});

(async () => {
  try {
    await loadMe();
    await loadRuns();
  } catch (err) {
    if (err.message.startsWith("401")) {
      window.location.href = "/login";
    } else {
      uploadErr.textContent = `加载失败: ${err.message}`;
      uploadErr.hidden = false;
    }
  }
})();
