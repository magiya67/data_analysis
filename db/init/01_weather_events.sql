CREATE TABLE IF NOT EXISTS weather_events (
  id              BIGSERIAL PRIMARY KEY,
  ts              TIMESTAMPTZ NOT NULL DEFAULT now(),
  station_id      TEXT        NOT NULL,

  temperature_c   REAL        NOT NULL,
  humidity_pct    REAL        NOT NULL,
  pressure_hpa    REAL        NOT NULL,
  wind_speed_mps  REAL        NOT NULL,
  wind_dir_deg    SMALLINT    NOT NULL,

  CONSTRAINT humidity_range CHECK (humidity_pct >= 0 AND humidity_pct <= 100),
  CONSTRAINT wind_dir_range CHECK (wind_dir_deg >= 0 AND wind_dir_deg <= 359)
);

CREATE INDEX IF NOT EXISTS idx_weather_events_ts ON weather_events (ts);
CREATE INDEX IF NOT EXISTS idx_weather_events_station_ts ON weather_events (station_id, ts);
