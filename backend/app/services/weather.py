from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import WeatherSnapshot


BUCKET_SIZE = 0.02
CACHE_WINDOW_MINUTES = 30


def bucket_coord(value: float) -> float:
    return round(round(value / BUCKET_SIZE) * BUCKET_SIZE, 4)


def get_weather_snapshot(db: Session, *, lat: float, lng: float) -> dict:
    lat_bucket = bucket_coord(lat)
    lng_bucket = bucket_coord(lng)
    threshold = datetime.now(timezone.utc) - timedelta(minutes=CACHE_WINDOW_MINUTES)

    cached = db.scalar(
        select(WeatherSnapshot)
        .where(WeatherSnapshot.lat_bucket == lat_bucket)
        .where(WeatherSnapshot.lng_bucket == lng_bucket)
        .where(WeatherSnapshot.fetched_at >= threshold)
        .order_by(desc(WeatherSnapshot.fetched_at))
    )
    if cached:
        return cached.data_json

    data = _fetch_accuweather(lat=lat, lng=lng)
    snapshot = WeatherSnapshot(lat_bucket=lat_bucket, lng_bucket=lng_bucket, data_json=data)
    db.add(snapshot)
    db.commit()
    return data


def _fetch_accuweather(*, lat: float, lng: float) -> dict:
    if not settings.accuweather_api_key:
        return {
            "source": "fallback",
            "precipitation": False,
            "temperature_c": 20,
            "is_daytime": True,
            "condition": "Unknown",
        }

    try:
        location_url = f"{settings.accuweather_base_url}/locations/v1/cities/geoposition/search"
        location_resp = requests.get(
            location_url,
            params={"apikey": settings.accuweather_api_key, "q": f"{lat},{lng}"},
            timeout=8,
        )
        location_resp.raise_for_status()
        location_key = location_resp.json().get("Key")
        if not location_key:
            raise ValueError("Missing location key")

        current_url = f"{settings.accuweather_base_url}/currentconditions/v1/{location_key}"
        current_resp = requests.get(
            current_url,
            params={"apikey": settings.accuweather_api_key, "details": "true"},
            timeout=8,
        )
        current_resp.raise_for_status()
        current_data = current_resp.json()[0]

        return {
            "source": "accuweather",
            "precipitation": bool(current_data.get("HasPrecipitation")),
            "temperature_c": (current_data.get("Temperature") or {})
            .get("Metric", {})
            .get("Value", 20),
            "is_daytime": bool(current_data.get("IsDayTime", True)),
            "condition": current_data.get("WeatherText", "Unknown"),
        }
    except Exception:
        return {
            "source": "fallback",
            "precipitation": False,
            "temperature_c": 20,
            "is_daytime": True,
            "condition": "Unknown",
        }
