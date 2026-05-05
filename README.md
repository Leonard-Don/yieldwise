# Yieldwise · 租知

[![Validate](https://github.com/Leonard-Don/yieldwise/actions/workflows/validate.yml/badge.svg)](https://github.com/Leonard-Don/yieldwise/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Open-source workbench for analyzing rental-yield data across Chinese cities — visualize properties on a map, compute yield / payback / occupancy KPIs.**

[中文 README](README.zh.md) · [Live demo](#quick-start) · [Browser capture import](docs/internal/import-public-browser-capture.md)

<p align="center">
  <img src="docs/screenshots/atlas-workbench-overview.png" alt="Yieldwise workbench overview" width="100%" />
</p>

## What is this

Yieldwise is a personal-scale real-estate analysis tool. It:

- Plots properties on a map alongside open-data communities and OSM building footprints
- Computes rental yield / payback / occupancy KPIs per district / community / building
- Lets you compare candidates against the local market in seconds

**Run it locally on your machine. Your data never leaves it.**

## Who is this for

- **Individual investors** who want to look at rental yield distributions across districts before bidding on a property
- **FinTech / urban-economics / real-estate finance students and researchers** who need a quick analytical scaffolding for coursework or research
- **Tinkerers** who want to see what a "Bloomberg terminal for Chinese rentals" might look like as an open-source side project

## Why it exists

Public real-estate data in China is scattered across government open-data portals, OSM, AMAP POIs, and PDF reports priced for institutions. Yieldwise stitches the open-source bits into one place.

No login-gated or unauthorized scraping — only public open data and browser-captured public pages.

## Quick start

Prerequisites: Python 3.13+ and a local Postgres + PostGIS instance. [Postgres.app](https://postgresapp.com/) is the lightest option on macOS and bundles PostGIS.

```bash
git clone https://github.com/Leonard-Don/yieldwise.git
cd yieldwise
cp .env.example .env             # edit .env to set AMAP_API_KEY (free, see below)

python3 -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt

createdb yieldwise                                                # one-time
psql yieldwise -c "CREATE EXTENSION IF NOT EXISTS postgis"        # one-time

export $(grep -v '^#' .env | xargs)
uvicorn api.main:app --reload --port 8000
```

Open `http://localhost:8000` to see the map.

The schema is applied automatically on first DB use, so no manual `psql -f` is needed.

Need a free AMAP key for the map to render? Get one at [lbs.amap.com](https://lbs.amap.com/api/javascript-api-v2/prerequisites).

### Local demo without Postgres

Want to inspect the UI first? You can boot the demo/mock mode without creating a database:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt
ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --reload --port 8000
```

This is only for local exploration. Real analysis should use Postgres/PostGIS plus open-data imports or public-page browser-scrape batches.

## Features

- **Three workflows on one map**: 收益猎手 (yield hunter) · 自住找房 (homebuyer) · 全市观察 (city overview)
- **Candidate comparison + local memo export** for communities / buildings / districts, including quality risks and next actions
- **OSM + AMAP merged building footprints** with quota-based community matching
- **Ops refresh center** for dry-running and executing staged reference/import/geo/metrics refresh jobs, with job history, anomaly triage, and geometry QA

## Data sources (transparency)

| Layer | Source | License |
|---|---|---|
| Building footprints | OpenStreetMap | ODbL |
| Community boundaries | AMAP POI | Per AMAP ToS |
| District boundaries | Shanghai government open data | Open Government Data |
| Listings (sample) | Synthetic / browser-scraped demo set | Self-generated |

Yieldwise keeps the listing path to public-page browser scraping only: no manual data-entry UI and no auto-fetching of anything that requires authorization.

## Project status

**v0.3** (April 2026) — Beta. Stable:
- Shanghai-only (no multi-city abstraction; the constants live in `api/config/city.py`)
- Backend + frontend test suites in place
- Maintained part-time — expect rough edges, file issues if you hit them

## Contributing

Issues, ideas, and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE). The MIT grant covers Yieldwise's source code only; data sources retain their own licenses (OSM ODbL, AMAP ToS, etc.).

## Contact

For questions, feedback, or bug reports, please use [GitHub Issues](https://github.com/Leonard-Don/yieldwise/issues) or [Discussions](https://github.com/Leonard-Don/yieldwise/discussions).

If you find this useful, a star on the repo helps a lot.
