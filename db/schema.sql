CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS districts (
    district_id TEXT PRIMARY KEY,
    district_name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    city_name TEXT NOT NULL DEFAULT '上海',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_providers (
    provider_id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    provider_category TEXT NOT NULL,
    acquisition_mode TEXT NOT NULL,
    priority_level TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'planned',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    provider_id TEXT REFERENCES source_providers(provider_id),
    policy_scope TEXT NOT NULL,
    policy_status TEXT NOT NULL DEFAULT 'draft',
    summary TEXT NOT NULL,
    review_owner TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id BIGSERIAL PRIMARY KEY,
    external_run_id TEXT NOT NULL UNIQUE,
    provider_id TEXT REFERENCES source_providers(provider_id),
    batch_name TEXT NOT NULL,
    acquisition_mode TEXT NOT NULL DEFAULT 'authorized_import',
    business_scope TEXT NOT NULL DEFAULT 'sale_rent',
    status TEXT NOT NULL DEFAULT 'completed',
    sale_input_file TEXT,
    rent_input_file TEXT,
    output_manifest_path TEXT,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ingestion_runs_provider_idx ON ingestion_runs (provider_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS communities (
    community_id TEXT PRIMARY KEY,
    district_id TEXT NOT NULL REFERENCES districts(district_id),
    name TEXT NOT NULL,
    aliases_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    centroid_gcj02 GEOMETRY(Point, 4326),
    centroid_wgs84 GEOMETRY(Point, 4326),
    polygon_geojson JSONB,
    source_confidence NUMERIC(4, 3) NOT NULL DEFAULT 0.700,
    anchor_source TEXT,
    anchor_quality NUMERIC(4, 3),
    anchor_decision_state TEXT,
    latest_anchor_reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE communities
    ADD COLUMN IF NOT EXISTS anchor_source TEXT;

ALTER TABLE communities
    ADD COLUMN IF NOT EXISTS anchor_quality NUMERIC(4, 3);

ALTER TABLE communities
    ADD COLUMN IF NOT EXISTS anchor_decision_state TEXT;

ALTER TABLE communities
    ADD COLUMN IF NOT EXISTS latest_anchor_reviewed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS communities_district_idx ON communities (district_id);
CREATE INDEX IF NOT EXISTS communities_centroid_wgs84_gix ON communities USING GIST (centroid_wgs84);

CREATE TABLE IF NOT EXISTS community_aliases (
    alias_id BIGSERIAL PRIMARY KEY,
    community_id TEXT NOT NULL REFERENCES communities(community_id),
    alias_name TEXT NOT NULL,
    alias_source TEXT,
    confidence_score NUMERIC(5, 4) NOT NULL DEFAULT 0.800,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (community_id, alias_name)
);

CREATE INDEX IF NOT EXISTS community_aliases_name_idx ON community_aliases (alias_name);

CREATE TABLE IF NOT EXISTS anchor_review_events (
    event_id TEXT PRIMARY KEY,
    community_id TEXT NOT NULL REFERENCES communities(community_id),
    district_id TEXT REFERENCES districts(district_id),
    reference_run_id TEXT,
    action TEXT NOT NULL,
    decision_state TEXT NOT NULL,
    candidate_index INTEGER,
    previous_center_lng NUMERIC(12, 6),
    previous_center_lat NUMERIC(12, 6),
    center_lng NUMERIC(12, 6),
    center_lat NUMERIC(12, 6),
    anchor_source TEXT,
    anchor_quality NUMERIC(4, 3),
    review_note TEXT,
    alias_appended TEXT,
    review_owner TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS anchor_review_events_community_idx
    ON anchor_review_events (community_id, reviewed_at DESC);

CREATE TABLE IF NOT EXISTS buildings (
    building_id TEXT PRIMARY KEY,
    community_id TEXT NOT NULL REFERENCES communities(community_id),
    building_no TEXT NOT NULL,
    total_floors INTEGER,
    unit_count INTEGER,
    geom_gcj02 GEOMETRY(Geometry, 4326),
    geom_wgs84 GEOMETRY(Geometry, 4326),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (community_id, building_no)
);

CREATE INDEX IF NOT EXISTS buildings_community_idx ON buildings (community_id);
CREATE INDEX IF NOT EXISTS buildings_geom_wgs84_gix ON buildings USING GIST (geom_wgs84);

CREATE TABLE IF NOT EXISTS building_aliases (
    alias_id BIGSERIAL PRIMARY KEY,
    building_id TEXT NOT NULL REFERENCES buildings(building_id),
    alias_name TEXT NOT NULL,
    alias_source TEXT,
    source_ref TEXT,
    confidence_score NUMERIC(5, 4) NOT NULL DEFAULT 0.800,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (building_id, alias_name)
);

CREATE INDEX IF NOT EXISTS building_aliases_name_idx ON building_aliases (alias_name);

CREATE TABLE IF NOT EXISTS geo_assets (
    asset_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    asset_type TEXT NOT NULL CHECK (asset_type IN ('district_boundary', 'community_aoi', 'building_footprint', 'export_kml')),
    provider_id TEXT REFERENCES source_providers(provider_id),
    district_id TEXT REFERENCES districts(district_id),
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    source_ref TEXT,
    geom_gcj02 GEOMETRY(Geometry, 4326),
    geom_wgs84 GEOMETRY(Geometry, 4326),
    payload_json JSONB,
    captured_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE geo_assets
    ADD COLUMN IF NOT EXISTS ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id);

CREATE INDEX IF NOT EXISTS geo_assets_type_idx ON geo_assets (asset_type);
CREATE INDEX IF NOT EXISTS geo_assets_geom_wgs84_gix ON geo_assets USING GIST (geom_wgs84);
CREATE UNIQUE INDEX IF NOT EXISTS geo_assets_run_building_ref_uidx
    ON geo_assets (ingestion_run_id, asset_type, building_id, source_ref);

CREATE TABLE IF NOT EXISTS raw_listings_sale (
    raw_listing_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    source TEXT NOT NULL,
    source_listing_id TEXT NOT NULL,
    url TEXT NOT NULL,
    raw_payload_json JSONB NOT NULL,
    crawled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, source_listing_id)
);

CREATE TABLE IF NOT EXISTS raw_listings_rent (
    raw_listing_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    source TEXT NOT NULL,
    source_listing_id TEXT NOT NULL,
    url TEXT NOT NULL,
    raw_payload_json JSONB NOT NULL,
    crawled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, source_listing_id)
);

CREATE TABLE IF NOT EXISTS listings_sale (
    listing_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    source TEXT NOT NULL,
    source_listing_id TEXT NOT NULL,
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    raw_community_name TEXT NOT NULL,
    raw_address TEXT,
    raw_building_text TEXT,
    floor_no INTEGER,
    total_floors INTEGER,
    floor_bucket TEXT,
    area_sqm NUMERIC(10, 2),
    bedrooms INTEGER,
    living_rooms INTEGER,
    bathrooms INTEGER,
    orientation TEXT,
    decoration TEXT,
    price_total_wan NUMERIC(12, 2),
    unit_price_yuan NUMERIC(12, 2),
    published_at TIMESTAMPTZ,
    crawled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active',
    dedup_group_id BIGINT,
    raw_payload_json JSONB,
    UNIQUE (source, source_listing_id)
);

CREATE INDEX IF NOT EXISTS listings_sale_community_idx ON listings_sale (community_id, building_id);
CREATE INDEX IF NOT EXISTS listings_sale_floor_idx ON listings_sale (floor_bucket, floor_no);
CREATE INDEX IF NOT EXISTS listings_sale_price_idx ON listings_sale (price_total_wan);

CREATE TABLE IF NOT EXISTS listings_rent (
    listing_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    source TEXT NOT NULL,
    source_listing_id TEXT NOT NULL,
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    raw_community_name TEXT NOT NULL,
    raw_address TEXT,
    raw_building_text TEXT,
    floor_no INTEGER,
    total_floors INTEGER,
    floor_bucket TEXT,
    area_sqm NUMERIC(10, 2),
    bedrooms INTEGER,
    living_rooms INTEGER,
    bathrooms INTEGER,
    orientation TEXT,
    decoration TEXT,
    monthly_rent NUMERIC(12, 2),
    published_at TIMESTAMPTZ,
    crawled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active',
    dedup_group_id BIGINT,
    raw_payload_json JSONB,
    UNIQUE (source, source_listing_id)
);

CREATE INDEX IF NOT EXISTS listings_rent_community_idx ON listings_rent (community_id, building_id);
CREATE INDEX IF NOT EXISTS listings_rent_floor_idx ON listings_rent (floor_bucket, floor_no);
CREATE INDEX IF NOT EXISTS listings_rent_price_idx ON listings_rent (monthly_rent);

CREATE TABLE IF NOT EXISTS listing_dedup_groups (
    dedup_group_id BIGSERIAL PRIMARY KEY,
    business_type TEXT NOT NULL CHECK (business_type IN ('sale', 'rent')),
    canonical_listing_id BIGINT,
    confidence_score NUMERIC(5, 4) NOT NULL,
    member_listing_ids_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS address_resolution_queue (
    task_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    source TEXT NOT NULL,
    source_listing_id TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_district_id TEXT REFERENCES districts(district_id),
    parsed_community_id TEXT REFERENCES communities(community_id),
    parsed_building_id TEXT REFERENCES buildings(building_id),
    parsed_unit TEXT,
    parsed_floor_no INTEGER,
    parse_status TEXT NOT NULL DEFAULT 'pending',
    confidence_score NUMERIC(5, 4),
    resolution_notes TEXT,
    review_owner TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, source_listing_id)
);

CREATE INDEX IF NOT EXISTS address_resolution_status_idx ON address_resolution_queue (parse_status, confidence_score);

CREATE TABLE IF NOT EXISTS address_review_events (
    event_id TEXT PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    queue_id TEXT NOT NULL,
    source TEXT NOT NULL,
    source_listing_id TEXT NOT NULL,
    parsed_community_id TEXT REFERENCES communities(community_id),
    parsed_building_id TEXT REFERENCES buildings(building_id),
    floor_no INTEGER,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    resolution_notes TEXT,
    review_owner TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS address_review_events_run_idx
    ON address_review_events (ingestion_run_id, reviewed_at DESC);

CREATE TABLE IF NOT EXISTS geo_asset_capture_tasks (
    task_id TEXT PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    provider_id TEXT REFERENCES source_providers(provider_id),
    task_scope TEXT NOT NULL CHECK (task_scope IN ('missing_building', 'unresolved_feature')),
    status TEXT NOT NULL DEFAULT 'needs_capture',
    priority TEXT NOT NULL DEFAULT 'medium',
    district_id TEXT REFERENCES districts(district_id),
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    source_ref TEXT,
    community_name TEXT,
    building_name TEXT,
    resolution_notes TEXT,
    review_owner TEXT,
    reviewed_at TIMESTAMPTZ,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS geo_asset_capture_tasks_run_idx
    ON geo_asset_capture_tasks (ingestion_run_id, status, priority);

CREATE TABLE IF NOT EXISTS geo_asset_review_events (
    event_id TEXT PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    task_id TEXT NOT NULL REFERENCES geo_asset_capture_tasks(task_id),
    task_scope TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    review_owner TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    resolution_notes TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS geo_asset_review_events_run_idx
    ON geo_asset_review_events (ingestion_run_id, reviewed_at DESC);

CREATE TABLE IF NOT EXISTS geo_capture_work_orders (
    work_order_id TEXT PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    provider_id TEXT REFERENCES source_providers(provider_id),
    status TEXT NOT NULL DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'delivered', 'closed')),
    district_id TEXT REFERENCES districts(district_id),
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    title TEXT NOT NULL,
    assignee TEXT,
    task_ids_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    task_count INTEGER NOT NULL DEFAULT 0,
    primary_task_id TEXT,
    focus_floor_no INTEGER,
    focus_yield_pct NUMERIC(8, 4),
    watchlist_hits INTEGER NOT NULL DEFAULT 0,
    impact_score NUMERIC(8, 2),
    impact_band TEXT,
    notes TEXT,
    due_at TIMESTAMPTZ,
    created_by TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS geo_capture_work_orders_run_idx
    ON geo_capture_work_orders (ingestion_run_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS geo_capture_work_order_events (
    event_id TEXT PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    work_order_id TEXT NOT NULL REFERENCES geo_capture_work_orders(work_order_id),
    previous_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS geo_capture_work_order_events_run_idx
    ON geo_capture_work_order_events (ingestion_run_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS floor_evidence_pairs (
    pair_id TEXT PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    floor_no INTEGER,
    sale_source TEXT NOT NULL,
    sale_source_listing_id TEXT NOT NULL,
    rent_source TEXT NOT NULL,
    rent_source_listing_id TEXT NOT NULL,
    sale_price_wan NUMERIC(12, 2),
    monthly_rent NUMERIC(12, 2),
    annual_yield_pct NUMERIC(8, 4),
    area_gap_sqm NUMERIC(10, 2),
    floor_gap INTEGER,
    match_confidence NUMERIC(5, 4) NOT NULL,
    normalized_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS floor_evidence_pairs_floor_idx
    ON floor_evidence_pairs (building_id, floor_no, match_confidence DESC);

CREATE TABLE IF NOT EXISTS floor_evidence_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    ingestion_run_id BIGINT REFERENCES ingestion_runs(run_id),
    community_id TEXT REFERENCES communities(community_id),
    building_id TEXT REFERENCES buildings(building_id),
    floor_no INTEGER NOT NULL,
    pair_count INTEGER NOT NULL DEFAULT 0,
    sale_median_wan NUMERIC(12, 2),
    rent_median_monthly NUMERIC(12, 2),
    yield_pct NUMERIC(8, 4),
    best_pair_confidence NUMERIC(5, 4),
    payload_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ingestion_run_id, building_id, floor_no)
);

CREATE INDEX IF NOT EXISTS floor_evidence_snapshots_yield_idx
    ON floor_evidence_snapshots (building_id, yield_pct DESC, best_pair_confidence DESC);

CREATE TABLE IF NOT EXISTS metrics_community (
    community_id TEXT NOT NULL REFERENCES communities(community_id),
    snapshot_date DATE NOT NULL,
    sale_median_wan NUMERIC(12, 2),
    rent_median_monthly NUMERIC(12, 2),
    yield_pct NUMERIC(8, 4),
    rent_sale_ratio NUMERIC(12, 4),
    sale_sample_size INTEGER NOT NULL DEFAULT 0,
    rent_sample_size INTEGER NOT NULL DEFAULT 0,
    opportunity_score NUMERIC(6, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (community_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS metrics_community_score_idx ON metrics_community (snapshot_date, opportunity_score DESC);

CREATE TABLE IF NOT EXISTS metrics_building_floor (
    community_id TEXT NOT NULL REFERENCES communities(community_id),
    building_id TEXT NOT NULL REFERENCES buildings(building_id),
    floor_bucket TEXT NOT NULL,
    snapshot_date DATE NOT NULL,
    sale_median_wan NUMERIC(12, 2),
    rent_median_monthly NUMERIC(12, 2),
    yield_pct NUMERIC(8, 4),
    rent_sale_ratio NUMERIC(12, 4),
    sample_size INTEGER NOT NULL DEFAULT 0,
    opportunity_score NUMERIC(6, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (building_id, floor_bucket, snapshot_date)
);

CREATE INDEX IF NOT EXISTS metrics_building_floor_score_idx
    ON metrics_building_floor (snapshot_date, opportunity_score DESC);
