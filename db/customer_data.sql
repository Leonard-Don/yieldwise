-- Yieldwise customer data schema. Single-tenant: client_id is the
-- uploading user's username (effectively a partition key on each row).

CREATE SCHEMA IF NOT EXISTS customer_data;

CREATE TABLE IF NOT EXISTS customer_data.portfolio (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    address TEXT,
    building_no TEXT,
    unit_type TEXT,
    monthly_rent_cny NUMERIC(14, 2),
    occupancy_rate_pct NUMERIC(5, 2),
    move_in_date DATE,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (client_id, project_name)
);
CREATE INDEX IF NOT EXISTS portfolio_client_idx ON customer_data.portfolio (client_id);

CREATE TABLE IF NOT EXISTS customer_data.pipeline (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    address TEXT,
    stage TEXT NOT NULL CHECK (stage IN ('lead', 'qualified', 'negotiating', 'won', 'lost')),
    est_price_cny NUMERIC(16, 2),
    notes TEXT,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    updated_at DATE,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (client_id, project_name)
);
CREATE INDEX IF NOT EXISTS pipeline_client_idx ON customer_data.pipeline (client_id);
CREATE INDEX IF NOT EXISTS pipeline_stage_idx ON customer_data.pipeline (client_id, stage);

CREATE TABLE IF NOT EXISTS customer_data.comp_set (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    source TEXT NOT NULL,
    report_date DATE,
    address TEXT,
    transaction_price_cny NUMERIC(16, 2),
    rent_per_sqm_cny NUMERIC(10, 2),
    area_sqm NUMERIC(10, 2),
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS comp_set_client_idx ON customer_data.comp_set (client_id);
CREATE INDEX IF NOT EXISTS comp_set_source_idx ON customer_data.comp_set (client_id, source, report_date);

CREATE TABLE IF NOT EXISTS customer_data.import_errors (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('portfolio', 'pipeline', 'comp_set')),
    row_index INT NOT NULL,
    raw_values JSONB NOT NULL,
    error_messages JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS import_errors_run_idx ON customer_data.import_errors (run_id);
