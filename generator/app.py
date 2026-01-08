import os
import time
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

import numpy as np
import psycopg2
from psycopg2.extras import execute_values


@dataclass
class Config:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    period_sec: float
    station_id: str

    @staticmethod
    def from_env() -> "Config":
        return Config(
            db_host=os.getenv("DB_HOST", "app_db"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "appdb"),
            db_user=os.getenv("DB_USER", "appuser"),
            db_password=os.getenv("DB_PASSWORD", "apppassword"),
            period_sec=float(os.getenv("PERIOD_SEC", "1")),
            station_id=os.getenv("STATION_ID", "AMS-01"),
        )


class WeatherModel:
    """
    Осмысленная генерация:
    - суточный цикл температуры (sin)
    - влажность обратно коррелирует с температурой
    - давление — медленный random walk
    - ветер — инерция + шум
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.pressure_hpa = 1013.0 + float(self.rng.normal(0, 1.5))
        self.wind_speed = max(0.2, float(self.rng.gamma(shape=2.0, scale=1.2)))
        self.wind_dir = int(self.rng.integers(0, 360))

    def _hour_utc(self, ts: datetime) -> float:
        return ts.hour + ts.minute / 60 + ts.second / 3600

    def sample(self, ts: datetime) -> Tuple[float, float, float, float, int]:
        hour = self._hour_utc(ts)

        # температура: средняя 12C, амплитуда 6C, пик около 15:00 UTC
        temp = 12.0 + 6.0 * math.sin(2 * math.pi * (hour - 15.0) / 24.0)
        temp += float(self.rng.normal(0, 0.4))

        # влажность: выше при низкой температуре
        hum = 75.0 - 1.8 * (temp - 12.0) + float(self.rng.normal(0, 2.5))
        hum = float(np.clip(hum, 10.0, 100.0))

        # давление: медленный random walk
        self.pressure_hpa += float(self.rng.normal(0, 0.08))
        self.pressure_hpa = float(np.clip(self.pressure_hpa, 980.0, 1045.0))

        # ветер: инерция + шум
        self.wind_speed = 0.92 * self.wind_speed + 0.08 * float(self.rng.gamma(2.0, 1.2))
        self.wind_speed = float(np.clip(self.wind_speed, 0.0, 20.0))

        # направление: сохраняет тренд
        self.wind_dir = int((self.wind_dir + int(self.rng.normal(0, 8))) % 360)

        return temp, hum, self.pressure_hpa, self.wind_speed, self.wind_dir


def connect(cfg: Config):
    return psycopg2.connect(
        host=cfg.db_host,
        port=cfg.db_port,
        dbname=cfg.db_name,
        user=cfg.db_user,
        password=cfg.db_password,
    )


def main():
    cfg = Config.from_env()
    model = WeatherModel(seed=42)

    print(f"[generator] target={cfg.db_host}:{cfg.db_port}/{cfg.db_name} user={cfg.db_user}")
    while True:
        try:
            with connect(cfg) as conn:
                print("[generator] connected; inserting events...")
                batch = []
                batch_size = 10

                while True:
                    now = datetime.now(timezone.utc)
                    temp, hum, press, wind, wdir = model.sample(now)
                    batch.append((now, cfg.station_id, temp, hum, press, wind, wdir))

                    if len(batch) >= batch_size:
                        with conn.cursor() as cur:
                            execute_values(
                                cur,
                                """
                                INSERT INTO weather_events
                                  (ts, station_id, temperature_c, humidity_pct, pressure_hpa, wind_speed_mps, wind_dir_deg)
                                VALUES %s
                                """,
                                batch,
                            )
                        conn.commit()
                        batch.clear()

                    time.sleep(cfg.period_sec)

        except Exception as e:
            print(f"[generator] ERROR: {e}. retry in 3s...", flush=True)
            time.sleep(3)


if __name__ == "__main__":
    main()
