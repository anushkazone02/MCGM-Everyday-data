import requests
import pandas as pd
import os
from datetime import datetime

# -----------------------------
# API URLs
# -----------------------------

STATIONS_URL = "https://dmwebtwo.mcgm.gov.in/api/sublocation/loadAll"

WEATHER_URL = "https://dmwebtwo.mcgm.gov.in/api/tabWeatherForecastData/loadById"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

print("=" * 50)
print("MCGM Daily Weather Collector")
print("=" * 50)

# -----------------------------
# Create folder
# -----------------------------

os.makedirs("daily_data", exist_ok=True)

# -----------------------------
# Download stations
# -----------------------------

stations = requests.post(
    STATIONS_URL,
    headers=HEADERS,
    timeout=30
).json()

print(f"Stations Found : {len(stations)}")

records = []

# -----------------------------
# Fetch weather
# -----------------------------

for station in stations:

    station_id = station["locationid"]

    try:

        weather = requests.post(
            WEATHER_URL,
            json={"id": station_id},
            headers=HEADERS,
            timeout=30
        ).json()

        details = weather.get("dummyTestRaingaugeDataDetails", {})

        records.append({

            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            "station_id": station_id,

            "station_name": station.get("name"),

            "latitude": station.get("latitude"),

            "longitude": station.get("longitude"),

            "observation_time": details.get("timerecorded"),

            "rain_current_mm": details.get("rain"),

            "rain_24hr_mm": weather.get("avgRainTwentyFourHourAWS"),

            "temperature": details.get("tempOut"),

            "humidity": details.get("outHumidity"),

            "pressure": details.get("bar"),

            "wind_speed": details.get("windSpeed")

        })

    except Exception as e:

        print(f"Failed: {station.get('name')}")

# -----------------------------
# Create dataframe
# -----------------------------

df = pd.DataFrame(records)

print(df.head())

print(f"\nRecords Collected : {len(df)}")

# -----------------------------
# Validation
# -----------------------------

if len(df) < 100:
    raise Exception("Too few stations returned.")

# -----------------------------
# Save files
# -----------------------------

today = datetime.now().strftime("%Y-%m-%d")

csv_file = f"daily_data/mcgm_{today}.csv"

excel_file = f"daily_data/mcgm_{today}.xlsx"

df.to_csv(csv_file, index=False)

df.to_excel(excel_file, index=False)

print("\nFiles Saved")

print(csv_file)

print(excel_file)

print("=" * 50)