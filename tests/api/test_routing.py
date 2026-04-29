from __future__ import annotations


def test_backstage_index_serves_workbench(client) -> None:
    response = client.get("/backstage/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>Yieldwise Workbench · 租知</title>" in body
    assert 'src="./app.js"' in body, "backstage page must load the legacy app bundle"


def test_backstage_assets_resolve(client) -> None:
    assert client.get("/backstage/styles.css").status_code == 200
    assert client.get("/backstage/app.js").status_code == 200


def test_user_shell_serves_html(client) -> None:
    response = client.get("/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>" in body
    assert "Yieldwise · 租知" in body
    assert 'data-user-shell="atlas"' in body, "user shell must mark its root element"


def test_user_shell_modules_resolve(client) -> None:
    assert client.get("/styles/tokens.css").status_code == 200
    assert client.get("/styles/shell.css").status_code == 200
    assert client.get("/modules/main.js").status_code == 200
