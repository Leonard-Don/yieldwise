# Adding a New City to Yieldwise

A city manifest carries everything the app historically hardcoded for "上海":
map center, default zoom, 行政区 list. Adding a new city is a 4-step recipe.

## 1. Author the YAML

Path: `api/config/cities/<city_id>.yaml`

Example:

```yaml
city_id: hangzhou
display_name: 杭州
country_code: CN
center: [120.1551, 30.2741]   # GCJ-02
default_zoom: 11.0
districts:
  - {district_code: 330102, display_name: 上城区}
  # ...
```

`district_code` is GB/T 2260 6-digit administrative code.

## 2. Activate at runtime

```bash
ATLAS_CITY=hangzhou uvicorn api.main:app --port 8000
```

The loader caches at process start; restart the app to switch.

## 3. Verify the API surface

```bash
curl -s http://127.0.0.1:8000/api/v2/config/city | python3 -m json.tool
```

`cityId` should match what you set.

## 4. Verify the frontend boot

Open `http://127.0.0.1:8000/`. The map should center on the new city.
If you see Shanghai still, hard refresh — `config-bootstrap.js` caches in
module state, not in the browser.

## What this ALONE does NOT cover

- District boundary GeoJSON (drawn on the map) — needs separate import
- Metro stations / POI overlays — needs separate import
- Reference rentals or comp anchor points — separate import

These are city-specific data, not configuration. They flow through the
existing import pipeline (`tmp/import-runs/` → PostGIS).
