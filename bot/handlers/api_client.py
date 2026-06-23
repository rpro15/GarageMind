from __future__ import annotations

"""API client used by bot handlers to call the Flask backend."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str, params: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_makes() -> list[str]:
    data = _get("/api/cars")
    return data.get("makes", [])


def fetch_models(make: str) -> list[str]:
    data = _get("/api/cars", {"make": make})
    return data.get("models", [])


def fetch_recommendations(
    car_make: str,
    car_model: str,
    car_year: int,
    category: str,
    season: str,
    driving_style: str,
    budget_rub: int,
) -> dict:
    return _post(
        "/api/recommend",
        {
            "car_make": car_make,
            "car_model": car_model,
            "car_year": car_year,
            "category": category,
            "season": season,
            "driving_style": driving_style,
            "budget_rub": budget_rub,
        },
    )


def log_click(
    user_id: str,
    product_name: str,
    marketplace: str,
    affiliate_url: str,
) -> None:
    try:
        _post(
            "/api/click",
            {
                "user_id": user_id,
                "product_name": product_name,
                "marketplace": marketplace,
                "affiliate_url": affiliate_url,
            },
        )
    except Exception:  # noqa: BLE001
        pass  # click logging is best-effort
