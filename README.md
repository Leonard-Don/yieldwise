# Yieldwise · 租知

[![Validate](https://github.com/Leonard-Don/yieldwise/actions/workflows/validate.yml/badge.svg)](https://github.com/Leonard-Don/yieldwise/actions/workflows/validate.yml)
[![Docker](https://github.com/Leonard-Don/yieldwise/actions/workflows/docker-build.yml/badge.svg)](https://github.com/Leonard-Don/yieldwise/actions/workflows/docker-build.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Open-source workbench for analyzing rental-yield, pipeline, and comp-set data across Chinese cities — on a single map, in your browser.**

[中文 README](README.zh.md) · [Live demo](#quick-start) · [How it's built](docs/internal/legacy-runbook.md)

<p align="center">
  <img src="docs/screenshots/atlas-workbench-overview.png" alt="Yieldwise workbench overview" width="100%" />
</p>

## What is this

Yieldwise is a personal-scale real-estate analysis tool. You upload your own CSV files (managed properties, deal pipeline, third-party comps) and Yieldwise:

- Plots them on a map alongside open-data communities and OSM building footprints
- Computes rental yield / payback / occupancy KPIs per district / community / building
- Lets you compare your candidates against the local market in seconds

**Run it locally on your machine. Your data never leaves it.**

## Who is this for

- **Individual investors** who want to look at rental yield distributions across districts before bidding on a property
- **FinTech / urban-economics / real-estate finance students and researchers** who need a quick analytical scaffolding without paying CoStar / 戴德梁行 prices
- **Independent property advisors** running a few small mandates who'd rather not build their own GIS stack
- **Tinkerers** who want to see what a "Bloomberg terminal for Chinese rentals" might look like at a $0 software cost

## Why it exists

Built as a final-year project by a FinTech student. Public real-estate data in China is scattered across government open-data portals, OSM, AMAP POIs, and PDF reports priced for institutions. Yieldwise stitches the open-source bits into one place and gives you a CSV import lane for the rest.

No scraping, no compliance grey area — you bring authorized data, the tool helps you analyze it.

## Quick start

Requires Docker + Docker Compose. One command brings up Postgres+PostGIS and the app:

```bash
git clone https://github.com/Leonard-Don/yieldwise.git
cd yieldwise
cp .env.example .env             # edit .env to set AMAP_API_KEY (free, see below)
docker compose up -d --build     # ~2 min first build, ~10s subsequent runs
```

Then open `http://localhost:8000` and log in with the credentials in `.env` (default `admin` / `changeme-after-first-login` — change before exposing the port to the network).

Try the customer-data upload at `/admin/customer-data`:
1. Click 下载模板 → save `portfolio.csv`
2. Fill in 5–10 rows with your sample data
3. Upload
4. The map populates with your points

Need a free AMAP key for the map to render? Get one at [lbs.amap.com](https://lbs.amap.com/api/javascript-api-v2/prerequisites). For commercial use, request a commercial key (personal keys violate AMAP ToS).

Prefer to run without Docker?

<details>
<summary>Native Python setup</summary>

```bash
docker compose up -d postgis      # postgis only
python3 -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt
export $(grep -v '^#' .env | xargs)
export POSTGRES_DSN=postgresql://atlas:atlas_local_dev@127.0.0.1:5432/yieldwise
uvicorn api.main:app --reload --port 8000
```
</details>

CSV templates: `/api/v2/customer-data/templates/{portfolio,pipeline,comp_set}.csv` — see [docs/customer-data-csv-spec.md](docs/customer-data-csv-spec.md).

## Features

- **Three workflows on one map**: 收益猎手 (yield hunter) · 自住找房 (homebuyer) · 全市观察 (city overview)
- **Three CSV import types**:
  - `portfolio` — properties under management
  - `pipeline` — acquisition candidates with stage tracking (lead/qualified/negotiating/won/lost)
  - `comp_set` — third-party reference points
- **Multi-user auth** with admin/analyst/viewer roles (single-tenant, private deploy)
- **Multi-city parameterization** — drop a YAML config to add a city
- **OSM + AMAP merged building footprints** with quota-based community matching
- **Per-row error capture** in CSV imports — bad rows go to an `errors.json` audit trail, never block the whole batch
- **Staged-first storage** — every import lands in `tmp/customer-data-runs/<run_id>/` for review before persisting to Postgres

## Data sources (transparency)

| Layer | Source | License |
|---|---|---|
| Building footprints | OpenStreetMap | ODbL |
| Community boundaries | AMAP POI (commercial key required for production) | Per AMAP ToS |
| District boundaries | Shanghai government open data | Open Government Data |
| Listings (sample) | Synthetic / hand-curated demo set | Self-generated |
| Customer data | **Brought by user (CSV)** | Owned by user |

Yieldwise ships **zero scrapers** and never auto-fetches anything that requires authorization. If a data source needs scraping, that's your decision in your own environment.

## Project status

**v0.3** (April 2026) — Beta. Stable:
- Auth + customer data import + staged-first persist
- Multi-city config (Shanghai live; templates for Beijing/Shenzhen)
- 253 backend tests passing, ~110 frontend node tests
- Built by one student, ~10h/week — expect rough edges

**Not yet shipped** — see [GitHub Issues](https://github.com/Leonard-Don/yieldwise/issues):
- PDF/Excel report export
- Public hosted demo
- Address-only geocoding (currently requires explicit lng/lat in CSV)

## Pricing

The tool itself is free under MIT. If you want a curated bundle of methodology + demo dataset + Excel templates, see [the upcoming knowledge package](https://github.com/Leonard-Don/yieldwise/discussions) — release planned for ~6 weeks from initial public push.

## Contributing

Issues, ideas, and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE). The MIT grant covers Yieldwise's source code only; data sources retain their own licenses (OSM ODbL, AMAP ToS, etc.).

## Contact

- GitHub: [@Leonard-Don](https://github.com/Leonard-Don)
- Email: leonarddon@oxxz.site

If you find this useful or have feedback, a star on the repo helps a lot.
