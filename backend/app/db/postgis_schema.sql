-- Production PostgreSQL + PostGIS Schema for GeoSense Phase 4
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS gis_layers (
    layer_id TEXT PRIMARY KEY,
    layer_name TEXT NOT NULL,
    layer_type TEXT NOT NULL,
    source TEXT NOT NULL,
    description TEXT NOT NULL,
    crs TEXT NOT NULL DEFAULT 'EPSG:4326',
    geographic_coverage TEXT NOT NULL,
    resolution TEXT,
    last_updated TIMESTAMPTZ NOT NULL,
    availability_status TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS gis_features (
    feature_id TEXT PRIMARY KEY,
    layer_id TEXT NOT NULL REFERENCES gis_layers(layer_id) ON DELETE CASCADE,
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    properties_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    region_id TEXT,
    risk_category TEXT,
    feature_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gis_features_geom ON gis_features USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_gis_features_layer_region ON gis_features (layer_id, region_id);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    reporter_type TEXT NOT NULL,
    status TEXT NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    description TEXT,
    region_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_geom ON incidents USING GIST (geom);

CREATE TABLE IF NOT EXISTS emergency_resources (
    id TEXT PRIMARY KEY,
    resource_type TEXT NOT NULL,
    name TEXT NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    region_id TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emergency_resources_geom ON emergency_resources USING GIST (geom);
