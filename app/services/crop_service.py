import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import random

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


def fetch_crop_prices(state: str, crop: str, days: int = 7, user_lat=None, user_lon=None):
    """
    Fetch latest crop prices. If API returns nothing,
    generate sample dummy data for 5 nearest markets.
    """

    if not BASE_URL or not API_KEY:
        print("⚠ Missing API details, generating random prices...")
        return generate_dummy_prices(user_lat, user_lon)

    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime("%d-%m-%Y") for i in range(days)]

    all_records = []

    for d in dates:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 5000,
            "filters[State]": state,
            "filters[Commodity]": crop,
            "filters[Arrival_Date]": d
        }

        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)

            if resp.status_code != 200:
                continue

            data = resp.json()
            records = data.get("records", [])

            for r in records:
                all_records.append({
                    "State": r.get("State"),
                    "District": r.get("District"),
                    "Market": r.get("Market"),
                    "Latitude": r.get("Latitude"),
                    "Longitude": r.get("Longitude"),
                    "Arrival_Date": r.get("Arrival_Date"),
                    "Modal_Price": r.get("Modal_Price")
                })

            # If this date gave results → stop searching older dates
            if len(records) > 0:
                break

        except:
            continue

    if len(all_records) == 0:
        print("⚠ No API data found → using dummy prices")
        return generate_dummy_prices(user_lat, user_lon)

    # Convert to DataFrame
    df = pd.DataFrame(all_records)

    # If user location provided → sort by nearest
    if user_lat is not None and user_lon is not None:
        df["Distance"] = (
            (df["Latitude"] - user_lat) ** 2 +
            (df["Longitude"] - user_lon) ** 2
        ) ** 0.5
        df = df.sort_values("Distance")

    # Limit to 5 nearest markets
    return df.head(5)


def generate_dummy_prices(user_lat=None, user_lon=None):
    """ Returns random 5 markets with random prices as fallback """

    markets = [
        ("Kolar Market", 13.13, 78.13),
        ("Bangarpet Market", 13.18, 78.26),
        ("Malur Market", 13.00, 77.94),
        ("KGF Market", 12.95, 78.27),
        ("Mulbagal Market", 13.17, 78.40),
    ]

    data = []
    for m in markets:
        data.append({
            "State": "Karnataka",
            "District": "Kolar",
            "Market": m[0],
            "Latitude": m[1],
            "Longitude": m[2],
            "Arrival_Date": "N/A",
            "Modal_Price": random.randint(10, 80)  # random price
        })

    df = pd.DataFrame(data)

    # Sort by nearest
    if user_lat and user_lon:
        df["Distance"] = (
            (df["Latitude"] - user_lat) ** 2 +
            (df["Longitude"] - user_lon) ** 2
        ) ** 0.5
        df = df.sort_values("Distance")

    return df.head(5)
