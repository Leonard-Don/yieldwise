from __future__ import annotations


def test_backstage_index_serves_workbench(authed_client) -> None:
    # Static shells are now gated by StaticShellAuthGate; anonymous visitors
    # are redirected to /login. An authenticated session is required to
    # render the workbench HTML.
    response = authed_client.get("/backstage/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>Yieldwise Workbench · 租知</title>" in body
    assert 'src="./app.js"' in body, "backstage page must load the legacy app bundle"


def test_backstage_assets_resolve(authed_client) -> None:
    assert authed_client.get("/backstage/styles.css").status_code == 200
    assert authed_client.get("/backstage/app.js").status_code == 200


def test_user_shell_serves_html(authed_client) -> None:
    response = authed_client.get("/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>" in body
    assert "Yieldwise · 租知" in body
    assert 'data-user-shell="atlas"' in body, "user shell must mark its root element"


def test_user_shell_modules_resolve(authed_client) -> None:
    assert authed_client.get("/styles/tokens.css").status_code == 200
    assert authed_client.get("/styles/shell.css").status_code == 200
    assert authed_client.get("/modules/main.js").status_code == 200
