import time
from datetime import datetime, timezone

import requests

from config import API_KEY, OPENWEATHER_URL
from db.supabase_utils import fetch_cities, insert_weather


def get_weather(lat, lon, api_key=API_KEY, units="metric", lang="en"):
    url = OPENWEATHER_URL
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": units, "lang": lang}
    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code == 200:
        return resp.json()
    print("API error:", resp.status_code, resp.text)
    return None


def build_weather_row(city_row, weather):
    """Map API JSON -> DB row schema."""
    dt_utc_now = datetime.now(timezone.utc).isoformat()
    return {
        "dt_utc": dt_utc_now,
        "city_id": weather.get("id"),
        "city_name": weather.get("name"),
        "country": weather.get("sys", {}).get("country"),
        "coord_lat": weather.get("coord", {}).get("lat"),
        "coord_lon": weather.get("coord", {}).get("lon"),
        "temp": weather.get("main", {}).get("temp"),
        "feels_like": weather.get("main", {}).get("feels_like"),
        "temp_min": weather.get("main", {}).get("temp_min"),
        "temp_max": weather.get("main", {}).get("temp_max"),
        "pressure": weather.get("main", {}).get("pressure"),
        "humidity": weather.get("main", {}).get("humidity"),
        "wind_speed": weather.get("wind", {}).get("speed"),
        "wind_deg": weather.get("wind", {}).get("deg"),
        "clouds_all": weather.get("clouds", {}).get("all"),
        "dt_unix": weather.get("dt"),
        "sunrise_unix": weather.get("sys", {}).get("sunrise"),
        "sunset_unix": weather.get("sys", {}).get("sunset"),
    }


def main():
    cities = fetch_cities()
    if not cities:
        print("There are no active cities in the 'cities' table.")
        return

    print(f"Processing {len(cities)} cities…")
    for i, c in enumerate(cities, start=1):
        lat, lon = c["lat"], c["lon"]
        w = get_weather(lat, lon)
        if w:
            try:
                row = build_weather_row(c, w)
                r = insert_weather(row)
                if r.data:
                    print(f"✅ [{i}/{len(cities)}] Inserted {c['city_name']}.")
                else:
                    print(f"⚠️ [{i}/{len(cities)}] Insert executed with no data returned.")
            except Exception as e:
                print(f"❌ [{i}/{len(cities)}] Error inserting {c['city_name']}: {e}")
        else:
            print(f"❌ [{i}/{len(cities)}] No data for {c['city_name']}.")
        time.sleep(1.1)  # Respect API rate limits


if __name__ == "__main__":
    main()
