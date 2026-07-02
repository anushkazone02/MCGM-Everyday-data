import requests
import pandas as pd
import os
import sys
from datetime import datetime

# API endpoints
STATIONS_URL = "https://dmwebtwo.mcgm.gov.in/api/sublocation/loadAll"
WEATHER_URL = "https://dmwebtwo.mcgm.gov.in/api/tabWeatherForecastData/loadById"
HEADERS = {"User-Agent": "Mozilla/5.0"}

print("=" * 70)
print(f"MCGM Daily Weather Collector - {datetime.now().isoformat()}")
print("=" * 70)

# Create output directory
os.makedirs("daily_data", exist_ok=True)

# ============================================================================
# STEP 1: Fetch Station List
# ============================================================================
try:
    print("\n[1/3] Fetching station list...")
    response = requests.post(STATIONS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    stations_raw = response.json()
    
    # Handle both dict and list API responses
    if isinstance(stations_raw, dict):
        stations = stations_raw.get('data', stations_raw.get('result', []))
    else:
        stations = stations_raw
    
    if not stations or len(stations) == 0:
        raise ValueError(f"API returned empty or invalid response: {stations_raw}")
    
    print(f"✓ Fetched {len(stations)} stations")
    
except requests.exceptions.Timeout:
    print("✗ ERROR: Request timeout while fetching stations")
    sys.exit(1)
except requests.exceptions.HTTPError as e:
    print(f"✗ ERROR: HTTP {e.response.status_code} while fetching stations")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print("✗ ERROR: Connection error while fetching stations")
    sys.exit(1)
except ValueError as e:
    print(f"✗ ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ ERROR: Unexpected error fetching stations: {type(e).__name__}: {e}")
    sys.exit(1)

# ============================================================================
# STEP 2: Fetch Weather Data for Each Station
# ============================================================================
print("\n[2/3] Fetching weather data...")
records = []
failed_stations = []

for i, station in enumerate(stations):
    station_id = station.get("locationid")
    station_name = station.get("name", "Unknown")
    
    # Skip stations with missing ID
    if not station_id:
        failed_stations.append((station_name, "Missing station ID"))
        continue
    
    try:
        # Call weather API for this station
        response = requests.post(
            WEATHER_URL,
            json={"id": station_id},
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        weather = response.json()
        
        # Extract weather details
        details = weather.get("dummyTestRaingaugeDataDetails", {})
        
        # Append record with ALL rolling rainfall windows
        records.append({
            "collection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "station_id": station_id,
            "station_name": station_name,
            "latitude": station.get("latitude"),
            "longitude": station.get("longitude"),
            "observation_time": details.get("timerecorded"),
            "rain_current_mm": details.get("rain"),
            "rain_1hr_mm": weather.get("avgRainOneHourAWS"),
            "rain_3hr_mm": weather.get("avgRainThreeHourAWS"),
            "rain_6hr_mm": weather.get("avgRainSixHourAWS"),
            "rain_12hr_mm": weather.get("avgRainTwelveHourAWS"),
            "rain_24hr_mm": weather.get("avgRainTwentyFourHourAWS"),
            "temperature": details.get("tempOut"),
            "humidity": details.get("outHumidity"),
            "pressure": details.get("bar"),
            "wind_speed": details.get("windSpeed"),
            "wind_dir": details.get("windDir"),
            "heat_index": details.get("heatIndex")
        })
    
    except requests.exceptions.Timeout:
        failed_stations.append((station_name, "Timeout"))
    except requests.exceptions.HTTPError as e:
        failed_stations.append((station_name, f"HTTP {e.response.status_code}"))
    except requests.exceptions.ConnectionError:
        failed_stations.append((station_name, "Connection error"))
    except Exception as e:
        failed_stations.append((station_name, f"{type(e).__name__}"))

# Print summary
print(f"✓ Successfully collected: {len(records)}/{len(stations)} stations")
if failed_stations:
    print(f"✗ Failed: {len(failed_stations)} stations")
    for name, reason in failed_stations[:10]:  # Show first 10 failures
        print(f"  - {name}: {reason}")

# ============================================================================
# STEP 3: Validate and Save
# ============================================================================
print("\n[3/3] Validating and saving...")

# Validation: Must have at least 100 records
if len(records) < 100:
    print(f"✗ FATAL: Only {len(records)} records collected (minimum required: 100)")
    sys.exit(1)

# Create DataFrame
df = pd.DataFrame(records)
print(f"✓ Created DataFrame with {len(df)} rows")

# Get today's date
today = datetime.now().strftime("%Y-%m-%d")

# Save CSV
csv_file = f"daily_data/mcgm_{today}.csv"
try:
    df.to_csv(csv_file, index=False)
    print(f"✓ Saved CSV: {csv_file}")
except Exception as e:
    print(f"✗ ERROR: Failed to save CSV: {e}")
    sys.exit(1)

# Save Excel
excel_file = f"daily_data/mcgm_{today}.xlsx"
try:
    df.to_excel(excel_file, index=False)
    print(f"✓ Saved Excel: {excel_file}")
except Exception as e:
    print(f"✗ ERROR: Failed to save Excel: {e}")
    sys.exit(1)

# ============================================================================
# SUCCESS
# ============================================================================
print("\n" + "=" * 70)
print("✓ SUCCESS - Data collection complete")
print("=" * 70)
print(f"\nColumns collected:")
print(f"  - rain_current_mm (instant rainfall)")
print(f"  - rain_1hr_mm (rolling 1-hour)")
print(f"  - rain_3hr_mm (rolling 3-hour)")
print(f"  - rain_6hr_mm (rolling 6-hour)")
print(f"  - rain_12hr_mm (rolling 12-hour)")
print(f"  - rain_24hr_mm (rolling 24-hour)")
print(f"\nPlus: temperature, humidity, pressure, wind_speed, wind_dir, heat_index")
sys.exit(0)
