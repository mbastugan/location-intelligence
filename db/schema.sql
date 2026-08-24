-- Location Intelligence MVP schema (SQLite dialect; portable to PostgreSQL)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS country (
  id            INTEGER PRIMARY KEY,
  iso2          TEXT NOT NULL UNIQUE,
  name          TEXT NOT NULL,
  currency_code TEXT NOT NULL DEFAULT 'EUR'
);

CREATE TABLE IF NOT EXISTS location (
  id           INTEGER PRIMARY KEY,
  country_id   INTEGER NOT NULL REFERENCES country(id),
  slug         TEXT NOT NULL,
  name         TEXT NOT NULL,
  name_local   TEXT,
  admin_code   TEXT,          -- e.g. INE municipality code
  location_type TEXT NOT NULL DEFAULT 'city',
  lat          REAL,
  lon          REAL,
  UNIQUE (country_id, slug)
);

CREATE TABLE IF NOT EXISTS data_source (
  id          INTEGER PRIMARY KEY,
  code        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  homepage_url TEXT,
  license_note TEXT,
  notes       TEXT
);

CREATE TABLE IF NOT EXISTS metric_definition (
  id               INTEGER PRIMARY KEY,
  code             TEXT NOT NULL UNIQUE,
  name             TEXT NOT NULL,
  description      TEXT,
  category         TEXT NOT NULL,
  unit             TEXT NOT NULL,
  higher_is_better INTEGER,   -- 1 / 0 / NULL (neutral)
  is_derived       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS metric_observation (
  id            INTEGER PRIMARY KEY,
  location_id   INTEGER NOT NULL REFERENCES location(id),
  metric_id     INTEGER NOT NULL REFERENCES metric_definition(id),
  source_id     INTEGER NOT NULL REFERENCES data_source(id),
  period_start  TEXT NOT NULL,  -- ISO date YYYY-MM-DD
  period_end    TEXT,           -- ISO date
  value         REAL NOT NULL,
  currency_code TEXT,
  quality_flag  TEXT NOT NULL DEFAULT 'ok',  -- ok | provisional | estimated | partial
  source_url    TEXT,
  collected_at  TEXT NOT NULL,
  UNIQUE (location_id, metric_id, period_start, source_id)
);

CREATE TABLE IF NOT EXISTS score_definition (
  id          INTEGER PRIMARY KEY,
  code        TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  version     TEXT NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS score_weight (
  id                  INTEGER PRIMARY KEY,
  score_definition_id INTEGER NOT NULL REFERENCES score_definition(id),
  metric_id           INTEGER NOT NULL REFERENCES metric_definition(id),
  weight              REAL NOT NULL,
  UNIQUE (score_definition_id, metric_id)
);

CREATE TABLE IF NOT EXISTS location_score (
  id                  INTEGER PRIMARY KEY,
  location_id         INTEGER NOT NULL REFERENCES location(id),
  score_definition_id INTEGER NOT NULL REFERENCES score_definition(id),
  value               REAL NOT NULL,
  coverage            REAL NOT NULL,  -- 0-1 fraction of weighted inputs present
  quality_flag        TEXT NOT NULL DEFAULT 'ok',
  computed_at         TEXT NOT NULL,
  UNIQUE (location_id, score_definition_id)
);

CREATE INDEX IF NOT EXISTS idx_obs_location_metric_period
  ON metric_observation (location_id, metric_id, period_start);
