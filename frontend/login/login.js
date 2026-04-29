const form = document.getElementById("login-form");
const errorEl = form.querySelector('[data-role="error"]');

function getNextUrl() {
  const params = new URLSearchParams(window.location.search);
  const next = params.get("next");
  // Allow only same-origin paths to defeat open-redirect attacks.
  if (next && next.startsWith("/") && !next.startsWith("//")) {
    return next;
  }
  return "/";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.hidden = true;
  const data = new FormData(form);
  const payload = {
    username: data.get("username"),
    password: data.get("password"),
  };
  try {
    const r = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (r.status === 401) {
      errorEl.textContent = "用户名或密码错误";
      errorEl.hidden = false;
      return;
    }
    if (!r.ok) {
      errorEl.textContent = `登录失败 (${r.status})`;
      errorEl.hidden = false;
      return;
    }
    window.location.href = getNextUrl();
  } catch (err) {
    errorEl.textContent = `网络错误: ${err.message}`;
    errorEl.hidden = false;
  }
});
