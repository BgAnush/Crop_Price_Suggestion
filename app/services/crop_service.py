import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


def fetch_crop_prices(state: str, crop: str, user_lat=None, user_lon=None):
    """
    Fetch ONLY the most recent available date’s crop prices.
    If no data exists → fallback to RANDOM dummy markets and prices.
    """

    # If API keys missing, directly fallback
    if not BASE_URL or not API_KEY:
        print("⚠ Missing API details → using dummy random prices")
        return generate_dummy_prices(user_lat, user_lon)

    # Try latest date first → go backwards 10 days
    for days_back in range(0, 10):
        date_str = (datetime.today()).strftime("%d-%m-%Y")

        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 5000,
            "filters[State]": state,
            "filters[Commodity]": crop,
            "filters[Arrival_Date]": date_str,
        }

        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)

            if resp.status_code != 200:
                continue

            data = resp.json()
            records = data.get("records", [])

            if len(records) > 0:
                print(f"✔ Using latest available data: {date_str}")

                df = pd.DataFrame([
                    {
                        "State": r.get("State"),
                        "District": r.get("District"),
                        "Market": r.get("Market"),
                        "Latitude": r.get("Latitude"),
                        "Longitude": r.get("Longitude"),
                        "Arrival_Date": r.get("Arrival_Date"),
                        "Modal_Price": r.get("Modal_Price"),
                    }
                    for r in records
                ])

                # Sort by distance
                if user_lat and user_lon:
                    df["Distance"] = (
                        (df["Latitude"] - user_lat) ** 2 +
                        (df["Longitude"] - user_lon) ** 2
                    ) ** 0.5
                    df = df.sort_values("Distance")

                return df.head(5)

        except Exception as e:
            continue

    # If no API data → fallback
    print("⚠ No API data → using dummy random prices")
    return generate_dummy_prices(user_lat, user_lon)


def generate_dummy_prices(user_lat=None, user_lon=None):
    """
    Generates RANDOM markets + RANDOM prices every time.
    """

    sample_markets = [
        ("Kolar Market", 13.13, 78.13),
        ("Bangarpet Market", 13.18, 78.26),
        ("Malur Market", 13.00, 77.94),
        ("KGF Market", 12.95, 78.27),
        ("Mulbagal Market", 13.17, 78.40),
        ("Hosakote Market", 13.07, 77.79),
        ("H cross Market", 13.21, 78.05),
        ("Vemagal Market", 13.25, 78.27),
    ]

    # Random number of markets (3 to 7)
    picked = random.sample(sample_markets, random.randint(3, 7))

    data = []
    for m in picked:
        data.append({
            "State": "Karnataka",
            "District": "Kolar",
            "Market": m[0],
            "Latitude": m[1],
            "Longitude": m[2],
            "Arrival_Date": "N/A",
            "Modal_Price": random.randint(10, 100),  # random price
            "Distance": random.random(),  # random distance for sorting
        })

    df = pd.DataFrame(data)

    # If real user location → sort by actual distance
    if user_lat and user_lon:
        df["Distance"] = (
            (df["Latitude"] - user_lat) ** 2 +
            (df["Longitude"] - user_lon) ** 2
        ) ** 0.5

    return df.sort_values("Distance").reset_index(drop=True)
