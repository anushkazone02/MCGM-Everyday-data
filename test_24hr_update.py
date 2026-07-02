import requests
import json
from datetime import datetime
import time

WEATHER_URL = "https://dmwebtwo.mcgm.gov.in/api/tabWeatherForecastData/loadById"
STATIONS_URL = "https://dmwebtwo.mcgm.gov.in/api/sublocation/loadAll"
HEADERS = {"User-Agent": "Mozilla/5.0"}

print("=" * 70)
print("MCGM 24-Hour Rainfall Update Schedule Test")
print("=" * 70)

# First, find Colaba and Santacruz station IDs
try:
    response = requests.post(STATIONS_URL, headers=HEADERS, timeout=30)
    stations = response.json()
    if isinstance(stations, dict):
        stations = stations.get('data', [])
    
    colaba_id = None
    santacruz_id = None
    
    for station in stations:
        name = station.get('name', '').lower()
        if 'colaba' in name:
            colaba_id = station.get('locationid')
        elif 'santacruz' in name:
            santacruz_id = station.get('locationid')
    
    if not colaba_id or not santacruz_id:
        print("Warning: Could not find Colaba/Santacruz, using first available station")
        colaba_id = stations[0]['locationid'] if stations else None
        santacruz_id = stations[1]['locationid'] if len(stations) > 1 else colaba_id
        
except Exception as e:
    print(f"Error fetching stations: {e}")
    colaba_id = 1
    santacruz_id = 2

WATCH_STATIONS = {
    "Colaba": colaba_id,
    "Santacruz": santacruz_id,
}

print(f"\nMonitoring stations: {WATCH_STATIONS}\n")

# Collect data
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_data = {
    "test_start": current_time,
    "readings": []
}

for station_name, station_id in WATCH_STATIONS.items():
    try:
        response = requests.post(
            WEATHER_URL,
            json={"id": station_id},
            headers=HEADERS,
            timeout=10
        )
        weather = response.json()
        details = weather.get("dummyTestRaingaugeDataDetails", {})
        
        obs_time = details.get("timerecorded")
        rain_24h = weather.get("avgRainTwentyFourHourAWS")
        
        reading = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "station": station_name,
            "station_id": station_id,
            "observation_time": obs_time,
            "rain_24hr_mm": rain_24h
        }
        log_data["readings"].append(reading)
        
        print(f"{station_name}:")
        print(f"  Current time (IST): {datetime.now().strftime('%H:%M:%S')}")
        print(f"  Observation time: {obs_time}")
        print(f"  24-hour rainfall: {rain_24h} mm")
        print()
        
    except Exception as e:
        print(f"Error for {station_name}: {e}\n")

# Save to JSON file for tracking
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"24hr_test_log_{timestamp}.json"

try:
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    print(f"✓ Logged to: {log_file}")
except Exception as e:
    print(f"Error saving log: {e}")

print("=" * 70)
