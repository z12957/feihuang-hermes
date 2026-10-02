-- Node-local fleet inventory. Do not commit populated database files.
-- Initialize with: sqlite3 local/fleet.db < schemas/node-inventory.sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

INSERT OR IGNORE INTO schema_version(version) VALUES (1);

CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('compute', 'hermes', 'compute_and_hermes')),
    gpu_present INTEGER NOT NULL CHECK (gpu_present IN (0, 1)),
    os_name TEXT,
    os_version TEXT,
    notes TEXT,
    updated_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS gpu_devices (
    gpu_id INTEGER PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    gpu_index INTEGER NOT NULL,
    vendor TEXT,
    model TEXT,
    memory_mib INTEGER,
    pci_bus_id TEXT,
    subsystem_id TEXT,
    vbios_version TEXT,
    driver_version TEXT,
    power_limit_w REAL,
    physical_location TEXT,
    verified_at_utc TEXT,
    UNIQUE (node_id, gpu_index)
);

CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    service_role TEXT NOT NULL CHECK (
        service_role IN ('hermes', 'lm_link', 'model_server', 'litellm', 'monitoring', 'other')
    ),
    runtime TEXT,
    version TEXT,
    model_id TEXT,
    api_compatibility TEXT,
    base_url TEXT,
    enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    verified_at_utc TEXT,
    notes TEXT,
    UNIQUE (node_id, service_name)
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id INTEGER PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    gpu_id INTEGER REFERENCES gpu_devices(gpu_id) ON DELETE SET NULL,
    observed_at_utc TEXT NOT NULL,
    category TEXT NOT NULL CHECK (
        category IN ('gpu', 'pcie', 'thermal', 'memory', 'disk', 'network', 'model_api', 'gateway', 'other')
    ),
    symptom TEXT NOT NULL,
    evidence TEXT,
    action_taken TEXT,
    outcome TEXT,
    follow_up_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_gpu_devices_node ON gpu_devices(node_id);
CREATE INDEX IF NOT EXISTS idx_services_node ON services(node_id);
CREATE INDEX IF NOT EXISTS idx_incidents_node_time ON incidents(node_id, observed_at_utc);
