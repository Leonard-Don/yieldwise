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

CREATE TABLE IF NOT EXISTS customer_data.import_errors (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('portfolio')),
    row_index INT NOT NULL,
    raw_values JSONB NOT NULL,
    error_messages JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS import_errors_run_idx ON customer_data.import_errors (run_id);
