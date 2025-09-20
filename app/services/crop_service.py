import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


def fetch_crop_prices(state: str, crop: str, days: int = 7) -> pd.DataFrame:
    """
    Fetch crop price data for a given state and crop from the API.

    Args:
        state (str): The state name (must match API format).
        crop (str): The commodity/crop name.
        days (int): Number of past days to fetch (default: 7).

    Returns:
        pd.DataFrame: Table of crop prices with columns:
            State, District, Market, Arrival_Date, Modal_Price
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("API_KEY or BASE_URL not configured in environment variables")

    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime("%d-%m-%Y") for i in range(1, days + 1)]

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

            # If API fails, skip this date
            if resp.status_code != 200:
                print(f"⚠️ API error {resp.status_code} for date {d}: {resp.text[:100]}")
                continue

            # Try parsing JSON
            try:
                data = resp.json()
            except Exception:
                print(f"⚠️ Invalid JSON for date {d}: {resp.text[:100]}")
                continue

            records = data.get("records", [])
            for r in records:
                all_records.append({
                    "State": r.get("State"),
                    "District": r.get("District"),
                    "Market": r.get("Market"),
                    "Arrival_Date": r.get("Arrival_Date"),
                    "Modal_Price": r.get("Modal_Price")
                })

        except requests.RequestException as e:
            print(f"⚠️ Request failed for {d}: {e}")
            continue

    # Return dataframe (even if empty)
    return pd.DataFrame(all_records)
