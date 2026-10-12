-- CareFlow: Relational Database Schema for SQLite
-- Defines tables: patients, visits, events

PRAGMA foreign_keys = ON;

-- Clean drop in reverse dependency order (child tables and dependent views first)
DROP VIEW IF EXISTS raw_healthcare_events;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS visits;
DROP TABLE IF EXISTS patients;

-- 1. Patients Table: Stores unique patient identities
CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY NOT NULL
);

-- 2. Visits Table: Stores journey-level metadata for each patient visit
CREATE TABLE visits (
    visit_id TEXT PRIMARY KEY NOT NULL,
    patient_id TEXT NOT NULL,
    visit_start_time TEXT NOT NULL,
    visit_end_time TEXT NOT NULL,
    total_events INTEGER NOT NULL CHECK (total_events > 0),
    discharge_disposition TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE
);

-- 3. Events Table: Granular log of every event/activity in a visit
CREATE TABLE events (
    event_id TEXT PRIMARY KEY NOT NULL,
    visit_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,
    department TEXT NOT NULL,
    status TEXT NOT NULL,
    waiting_time_minutes INTEGER NOT NULL CHECK (waiting_time_minutes >= 0),
    FOREIGN KEY (visit_id) REFERENCES visits (visit_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE
);

-- Indexes to optimize analytical queries, joins, and timeline aggregations
CREATE INDEX IF NOT EXISTS idx_visits_patient_id ON visits (patient_id);
CREATE INDEX IF NOT EXISTS idx_visits_start_time ON visits (visit_start_time);
CREATE INDEX IF NOT EXISTS idx_events_visit_id ON events (visit_id);
CREATE INDEX IF NOT EXISTS idx_events_patient_id ON events (patient_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (event_timestamp);
CREATE INDEX IF NOT EXISTS idx_events_name ON events (event_name);
CREATE INDEX IF NOT EXISTS idx_events_department ON events (department);

-- 4. Reusable View: raw_healthcare_events (direct alias preserving raw CSV column order)
CREATE VIEW IF NOT EXISTS raw_healthcare_events AS
SELECT
    patient_id,
    visit_id,
    event_id,
    event_name,
    event_timestamp,
    department,
    status,
    waiting_time_minutes
FROM events;
