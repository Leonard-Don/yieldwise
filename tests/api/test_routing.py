from __future__ import annotations


def test_backstage_index_serves_workbench(client) -> None:
    response = client.get("/backstage/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>Shanghai Yield Atlas</title>" in body
    assert 'src="./app.js"' in body, "backstage page must load the legacy app bundle"


def test_backstage_assets_resolve(client) -> None:
    assert client.get("/backstage/styles.css").status_code == 200
    assert client.get("/backstage/app.js").status_code == 200
