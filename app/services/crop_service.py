import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from geopy.distance import geodesic

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


def fetch_latest_nearby_price(state: str, crop: str, user_location: tuple, max_days: int = 15):
    """
    Fetch the latest available crop price for the NEAREST market.

    Args:
        state (str): State name (as per API)
        crop (str): Commodity name
        user_location (tuple): (latitude, longitude)
        max_days (int): Look back days (default 15)

    Returns:
        dict: Data for latest date & nearest market:
            {
                "Market": ...,
                "District": ...,
                "Arrival_Date": ...,
                "Modal_Price": ...,
                "Distance_km": ...
            }
    """

    if not BASE_URL or not API_KEY:
        raise ValueError("API_KEY or BASE_URL is missing in .env")

    today = datetime.today()

    # Search from today backwards → stops when first date with data found
    for i in range(max_days):
        date_str = (today - timedelta(days=i)).strftime("%d-%m-%Y")

        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 5000,
            "filters[State]": state,
            "filters[Commodity]": crop,
            "filters[Arrival_Date]": date_str
        }

        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"⚠️ API error {resp.status_code} for {date_str}")
                continue

            data = resp.json()
            records = data.get("records", [])

            # If we found a date with data → process nearest market
            if records:
                print(f"✅ Found latest available data on {date_str}")

                # Add distance for each market
                enriched = []
                for r in records:
                    if "Latitude" in r and "Longitude" in r:
                        market_loc = (float(r["Latitude"]), float(r["Longitude"]))
                        distance = geodesic(user_location, market_loc).km
                    else:
                        distance = None

                    enriched.append({
                        "State": r.get("State"),
                        "District": r.get("District"),
                        "Market": r.get("Market"),
                        "Arrival_Date": r.get("Arrival_Date"),
                        "Modal_Price": r.get("Modal_Price"),
                        "Distance_km": distance
                    })

                # Convert to DataFrame
                df = pd.DataFrame(enriched)

                # Sort by nearest distance
                df = df.sort_values("Distance_km")

                # Return nearest market's info
                return df.iloc[0].to_dict()

        except Exception as e:
            print(f"⚠️ Error: {e}")
            continue

    # If nothing is found for last `max_days`
    return {"error": "No price data available for recent days."}
